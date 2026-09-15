import os
import time
import random
import threading
from datetime import datetime, time as dt_time, timedelta
from zoneinfo import ZoneInfo

# 🌍 منطقه زمانی ایران
IRAN_TZ = ZoneInfo("Asia/Tehran")

from persiantools.jdatetime import JalaliDate
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

# ⚙️ تنظیمات اصلی
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = "6600182795"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
AUTO_REPLY_TEXT = "Hi! I'm not available right now, but I'll get back to you as soon as possible.✨"
COOLDOWN = 24 * 60 * 60  # 24 hours

# 📞 اطلاعات تماس شما
PHONE_NUMBER = "+989058407880"
INSTAGRAM_ID = "m_gh.tech"

# 🎵 لیست آهنگ‌ها (تصادفی انتخاب می‌شن) - Google Drive
SONGS = [
    {
        "title": "Maste Eshgh",
        "performer": "Alireza Talischi",
        "url": "https://drive.google.com/uc?export=download&id=1phRFMcaF5hwK8VUd3g0c_ZC9eipKweI6",
    },
    {
        "title": "Persian Song 1",
        "performer": "Various Artists",
        "url": "https://drive.google.com/uc?export=download&id=1yY81IMw970z_tCFIgQB6qTYISe83hNZ1",
    },
    {
        "title": "Persian Song 2",
        "performer": "Various Artists",
        "url": "https://drive.google.com/uc?export=download&id=1Bb_y5mAzdQJojp6Yd08qxJwFkA2Nostz",
    },
    {
        "title": "Mehdi Ahmadvand",
        "performer": "Mehdi Ahmadvand",
        "url": "https://drive.google.com/uc?export=download&id=1OUS-RZ-x94CKVuBcbr21nfnLvhAJX7lM",
    },
    {
        "title": "Farhad",
        "performer": "Mehdi Ahmadvand",
        "url": "https://drive.google.com/uc?export=download&id=1vrUy4Yho8wK0Kuq9YKnNVzDgq6yqj6Qk",
    },
    {
        "title": "Jonoon",
        "performer": "Mehdi Ahmadvand",
        "url": "https://drive.google.com/uc?export=download&id=1lcC8A9dIFqziY9arhVz6O9NTDjSgL3K0",
    },
    {
        "title": "Podcast 3",
        "performer": "Mehdi Ahmadvand",
        "url": "https://drive.google.com/uc?export=download&id=1yW4EClNb-TL0akEzM7brJs8bPSxyFlC6",
    },
    {
        "title": "Remix Zang Bezani",
        "performer": "Mehdi Ahmadvand",
        "url": "https://drive.google.com/uc?export=download&id=1jGjGWf1fR1UCmY8Di9mWj2wPGxsD-3NM",
    },
    {
        "title": "Zang Bezani",
        "performer": "Mehdi Ahmadvand",
        "url": "https://drive.google.com/uc?export=download&id=1AC3PUo1lp-roqBmAQMUfGYwQoBgFPwGK",
    },
    {
        "title": "Faghat Ba to Eshgham",
        "performer": "Shadmehr Aghili",
        "url": "https://drive.google.com/uc?export=download&id=1vivihQm4iU4ZRBo0OKo9wJdmctpQqOzI",
    },
    {
        "title": "Elaheye Naz",
        "performer": "Mehdi Ahmadvand",
        "url": "https://drive.google.com/uc?export=download&id=18DIw4quX12SkX_OJDyL926M77WhDkkor",
    },
]

# 🗣️ کلمات کلیدی و پاسخ‌های خودکار
KEYWORD_REPLIES = {
    "thanks": ["خواهش می‌کنم، کاری نکردم. 🖤", "قابل شما رو نداشت. ✨", "لطف دارید. 🙏"],
    "thank you": ["خواهش می‌کنم، کاری نکردم. 🖤", "قابل شما رو نداشت. ✨", "لطف دارید. 🙏"],
    "thx": ["خواهش می‌کنم. 🖤", "لطف دارید. ✨"],
    "tnx": ["خواهش می‌کنم. 🖤", "لطف دارید. ✨"],
    "مرسی": ["خواهش می‌کنم، کاری نکردم. 🖤", "قابل شما رو نداشت. ✨", "لطف دارید. 🙏"],
    "ممنون": ["خواهش می‌کنم، کاری نکردم. 🖤", "قابل شما رو نداشت. ✨", "لطف دارید. 🙏"],
    "ممنونم": ["خواهش می‌کنم. 🖤", "لطف دارید. ✨"],
    "مرسی ازت": ["خواهش می‌کنم. 🖤", "لطف دارید. ✨"],
    "goodbye": ["خداحافظ، مراقب خودت باش. 🌙", "به امید دیدار. 🖤", "دلم برات می‌مونه. ✨"],
    "bye": ["خداحافظ. 🌙", "مراقب خودت باش. 🖤"],
    "see you": ["به امید دیدار. 🌙", "منتظرتم. ✨"],
    "take care": ["مراقب خودت باش. 🖤", "به سلامت. ✨"],
    "خداحافظ": ["خداحافظ، مراقب خودت باش. 🌙", "به امید دیدار. 🖤", "دلم برات می‌مونه. ✨"],
    "خدانگهدار": ["خدا نگهدارت. 🌙", "مراقب خودت باش. 🖤"],
    "بای": ["خداحافظ. 🌙", "مراقب خودت باش. 🖤"],
    "فعلاً": ["فعلاً، به امید دیدار. 🌙", "منتظرتم. ✨"],
    "خدا نگهدار": ["خدا نگهدارت. 🌙", "مراقب خودت باش. 🖤"],
    "i miss you": ["منم دلم برات تنگ شده. 🖤", "دلت در دل من جا داره. ✨"],
    "i love you": ["منم دوستت دارم. 🖤", "محبتت برام ارزشمنده. ✨"],
    "miss you": ["منم دلم برات تنگ شده. 🖤"],
    "love you": ["منم دوستت دارم. 🖤"],
    "دلم برات تنگ شده": ["منم دلم برات تنگ شده. 🖤", "دلت در دل من جا داره. ✨"],
    "دلم برات تنگ شده بود": ["منم دلم برات تنگ شده بود. 🖤", "دلت در دل من جا داره. ✨"],
    "دوستت دارم": ["منم دوستت دارم. 🖤", "محبتت برام ارزشمنده. ✨"],
    "عاشقتم": ["منم عاشقتم. 🖤", "محبتت برام ارزشمنده. ✨"],
    "how are you": ["ممنون که پرسیدی، خوبم. تو چطوری؟ 😊", "خوبم، ممنون. تو چطوری؟ ✨"],
    "چطوری": ["ممنون که پرسیدی، خوبم. تو چطوری؟ 😊", "خوبم، ممنون. تو چطوری؟ ✨"],
    "خوبی": ["خوبم، ممنون. تو خوبی؟ 😊", "ممنون که پرسیدی. ✨"],
    "چه خبر": ["سلامتی، ممنون. تو چه خبر؟ 😊", "خبری نیست، ممنون. ✨"],
    "سلام": ["سلام، خوشحالم پیام دادی. 🖤", "سلام، چه خبر؟ ✨", "سلام، ممنون از حضورت. 🙏"],
    "hi": ["Hi, so happy to hear from you! 🖤", "Hey, what's up? ✨"],
    "hello": ["Hello, so happy to hear from you! 🖤", "Hey there, what's up? ✨"],
    "hey": ["Hey, so happy to hear from you! 🖤", "Hi, what's up? ✨"],
    "where are you": ["دور از دید، اما نزدیک به دل. 🌙", "نیستم، اما به یادتم. ✨"],
    "کجایی": ["دور از دید، اما نزدیک به دل. 🌙", "نیستم، اما به یادتم. ✨"],
    "چرا جواب نمی‌دی": ["ببخشید، الان در دسترس نیستم. 🖤", "شرمنده، الان نمی‌تونم. 🙏"],
    "کی برمی‌گردی": ["زود برمی‌گردم، منتظرم باش. 🌙", "به زودی پیشتم. ✨"],
    "are you there": ["Not right now, but you're on my mind. 🌙", "Away at the moment, but not forgotten. ✨"],
    "good night": ["شب بخیر، خواب‌های خوش. 🌙", "شب بخیر، دلم پیشته. ✨"],
    "good morning": ["صبح بخیر، روزت قشنگ. ☀️", "صبح بخیر، چه روز قشنگی. ✨"],
    "شب بخیر": ["شب بخیر، خواب‌های خوش. 🌙", "شب بخیر، دلم پیشته. ✨"],
    "صبح بخیر": ["صبح بخیر، روزت قشنگ. ☀️", "صبح بخیر، چه روز قشنگی. ✨"],
    "happy birthday": ["مرسی، چه لطفی کردی. 🎂", "ممنون، دلم رو شاد کردی. ✨"],
    "تولدت مبارک": ["مرسی، چه لطفی کردی. 🎂", "ممنون، دلم رو شاد کردی. ✨"],
    "congrats": ["مرسی. 🎉", "ممنون، دلم رو شاد کردی. ✨"],
    "تبریک": ["مرسی. 🎉", "ممنون، دلم رو شاد کردی. ✨"],
    "sorry": ["مهم نیست، نگران نباش. 🖤", "اشکالی نداره. ✨"],
    "ببخشید": ["مهم نیست، نگران نباش. 🖤", "اشکالی نداره. ✨"],
    "شرمنده": ["مهم نیست. 🖤", "اشکالی نداره. ✨"],
    "urgent": ["دریافت شد، زود خبرت می‌کنم. 🚨", "باشه، زود جوابت رو می‌دم. ⚡"],
    "فوری": ["دریافت شد، زود خبرت می‌کنم. 🚨", "باشه، زود جوابت رو می‌دم. ⚡"],
    "اضطراری": ["دریافت شد، زود خبرت می‌کنم. 🚨", "باشه، زود جوابت رو می‌دم. ⚡"],
    "asap": ["Got it, will reply soon. 🚨", "Understood, talk to you soon. ⚡"],
    "خدا خیرت بده": ["مرسی، خدا خیرت بده. 🖤", "لطف داری. ✨"],
    "دستت درد نکنه": ["سلامت باشی. 🖤", "لطف داری. ✨"],
}

# 🤖 تنظیم Gemini AI
client = None
if GEMINI_API_KEY:
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Gemini setup failed: {e}")

app = Flask(__name__)

# 🧠 حافظه‌ها
last_reply_time = {}
blacklist = set()
bot_enabled = True
stats = {"messages": 0, "replies": 0, "users": set()}
booked_slots = {}

# 🎯 مراحل رزرو وقت
BOOKING_NAME, BOOKING_DATE, BOOKING_TIME, BOOKING_CONFIRM = range(4)

# 🌍 تاریخ امروز ایران به شمسی
def get_iran_today():
    now_iran = datetime.now(IRAN_TZ)
    return JalaliDate(now_iran.date())

# 🔍 پیدا کردن پاسخ مناسب از روی کلمات کلیدی
def get_keyword_reply(user_message: str):
    msg_lower = user_message.lower()
    for keyword, replies in KEYWORD_REPLIES.items():
        if keyword.lower() in msg_lower:
            return random.choice(replies)
    return None

# 🎨 دکمه‌های شیشه‌ای اصلی
def get_inline_buttons():
    keyboard = [
        [
            InlineKeyboardButton("📞 Emergency Contact", callback_data="urgent"),
            InlineKeyboardButton("📱 Instagram", callback_data="instagram"),
        ],
        [
            InlineKeyboardButton("📅 Book Appointment", callback_data="book"),
        ],
        [
            InlineKeyboardButton("🎵 Play Music", callback_data="play_music"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# 🎯 انتخاب متن بر اساس ساعت روز
def get_time_based_message():
    now = datetime.now(IRAN_TZ)
    time_now = now.time()
    weekday = now.weekday()

    if weekday in (3, 4):
        return "It's the weekend — I'll get back to you as soon as I can. ✨"
    elif time_now >= dt_time(6, 0) and time_now < dt_time(12, 0):
        return "Good morning! I'm not available right now, but I'll reply as soon as I see your message. ☀️"
    elif time_now >= dt_time(12, 0) and time_now < dt_time(20, 30):
        return AUTO_REPLY_TEXT
    else:
        return "Good night! I'm asleep right now — I'll get back to you tomorrow. 🌙"

@app.route('/')
@app.route('/health')
def home():
    return "Bot is running"

# 🤖 پاسخ هوشمند AI
async def get_ai_reply(user_message: str):
    if not client:
        return None
    try:
        today = get_iran_today().strftime("%Y/%m/%d")
        prompt = f"""
You are an auto-reply assistant for a person who is currently unavailable.
Today's date (Shamsi): {today}

Analyze the user's message below.

- If the message is an EMOTIONAL message OR a FAREWELL message, generate a SHORT, warm auto-reply in the SAME language as the message.
- If the message is NOT emotional and NOT a farewell, reply with exactly: "NO_AI_REPLY"

User message: "{user_message}"

Your reply (only the reply text, nothing else):"""
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        reply = response.text.strip()
        if "NO_AI_REPLY" in reply:
            return None
        return reply
    except Exception as e:
        print(f"AI Error: {e}")
        return None

# 📨 پاسخ خودکار
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_enabled, stats

    message = update.message or update.business_message
    if not message:
        return

    if update.effective_chat.type != "private":
        return

    user_id = update.effective_user.id
    current_time = time.time()
    user_message = message.text or ""

    stats["messages"] += 1
    stats["users"].add(user_id)

    if update.effective_user.is_bot:
        return
    if user_id in blacklist:
        return
    if not bot_enabled:
        return

    keyword_reply = get_keyword_reply(user_message)

    if keyword_reply:
        await message.reply_text(keyword_reply)
        return

    if user_id in last_reply_time:
        if current_time - last_reply_time[user_id] < COOLDOWN:
            return

    ai_reply = await get_ai_reply(user_message)
    reply_text = ai_reply if ai_reply else get_time_based_message()
    await message.reply_text(
        reply_text,
        reply_markup=get_inline_buttons()
    )

    last_reply_time[user_id] = current_time
    stats["replies"] += 1

# 🎵 پخش آهنگ تصادفی
async def play_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    song = random.choice(SONGS)

    try:
        sent_message = await context.bot.send_audio(
            chat_id=query.message.chat_id,
            audio=song["url"],
            title=song["title"],
            performer=song["performer"],
            caption="🎵 Enjoy! This message will be deleted in 5 minutes."
        )

        # ⏰ زمان‌بندی برای پاک کردن پیام بعد از ۵ دقیقه
        context.job_queue.run_once(
            delete_message_job,
            when=300,  # ۵ دقیقه = ۳۰۰ ثانیه
            data={
                "chat_id": sent_message.chat_id,
                "message_id": sent_message.message_id,
            },
            name=f"delete_{sent_message.message_id}"
        )

        await query.answer("🎵 Sent! Enjoy.", show_alert=False)
    except Exception as e:
        print(f"Error sending audio: {e}")
        await query.answer("❌ Couldn't send. Try again.", show_alert=True)

# 🗑️ تابع پاک کردن پیام آهنگ
async def delete_message_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        await context.bot.delete_message(
            chat_id=job.data["chat_id"],
            message_id=job.data["message_id"]
        )
        print(f"Deleted message {job.data['message_id']}")
    except Exception as e:
        print(f"Error deleting message: {e}")

# 🖱️ مدیریت دکمه‌ها
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "urgent":
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]
        await query.edit_message_text(
            f"🚨 Emergency Contact:\n"
            f"📞 Phone: {PHONE_NUMBER}\n\n"
            f"Please call if it's urgent.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif query.data == "instagram":
        keyboard = [
            [InlineKeyboardButton("📱 Open Instagram", url=f"https://instagram.com/{INSTAGRAM_ID}")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
        ]
        await query.edit_message_text(
            f"📱 My Instagram:\n\n@{INSTAGRAM_ID}\n\n"
            f"Tap the button below to open my profile.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif query.data == "back_to_main":
        await query.edit_message_text(
            get_time_based_message(),
            reply_markup=get_inline_buttons()
        )
    elif query.data == "play_music":
        await play_music(update, context)

# 📅 ساخت تقویم ۵ روزه
def get_date_keyboard():
    today = get_iran_today()
    keyboard = []
    row = []
    for i in range(0, 5):
        next_day = today + timedelta(days=i)
        date_str = next_day.strftime("%Y/%m/%d")
        row.append(InlineKeyboardButton(date_str, callback_data=f"date_{date_str}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([
        InlineKeyboardButton("🔙 Back", callback_data="back_to_name"),
        InlineKeyboardButton("❌ Cancel", callback_data="cancel_booking"),
    ])
    return InlineKeyboardMarkup(keyboard)

# ⏰ ساخت دکمه‌های ساعت (با غیرفعال کردن تایم‌های گذشته و رزروشده)
def get_time_keyboard(selected_date: str = None):
    times = ["08:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00"]
    keyboard = []
    row = []
    booked = booked_slots.get(selected_date, []) if selected_date else []

    now_iran = datetime.now(IRAN_TZ)
    today_str = get_iran_today().strftime("%Y/%m/%d")
    is_today = (selected_date == today_str)

    for t in times:
        if t in booked:
            row.append(InlineKeyboardButton(f"❌ {t}", callback_data="already_booked"))
        elif is_today:
            hour, minute = map(int, t.split(":"))
            slot_time = now_iran.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if slot_time <= now_iran:
                row.append(InlineKeyboardButton(f"⏰ {t}", callback_data="past_time"))
            else:
                row.append(InlineKeyboardButton(t, callback_data=f"time_{t}"))
        else:
            row.append(InlineKeyboardButton(t, callback_data=f"time_{t}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([
        InlineKeyboardButton("🔙 Back", callback_data="back_to_date"),
        InlineKeyboardButton("❌ Cancel", callback_data="cancel_booking"),
    ])
    return InlineKeyboardMarkup(keyboard)

# 📅 شروع رزرو
async def start_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_name = query.from_user.full_name
    context.user_data['booking_name'] = user_name
    keyboard = [
        [InlineKeyboardButton("✅ Yes, that's me", callback_data="confirm_name")],
        [
            InlineKeyboardButton("🔙 Back", callback_data="back_to_main"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_booking"),
        ]
    ]
    await query.edit_message_text(
        f"📝 Is this your name?\n\n👤 {user_name}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return BOOKING_NAME

async def confirm_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    today = get_iran_today().strftime("%Y/%m/%d")
    await query.edit_message_text(
        f"📅 Please select a date:\n\n"
        f"👤 Name: {context.user_data['booking_name']}\n"
        f"📆 Today: {today}",
        reply_markup=get_date_keyboard()
    )
    return BOOKING_DATE

async def select_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    date = query.data.replace("date_", "")
    context.user_data['booking_date'] = date
    await query.edit_message_text(
        f"⏰ Please select a time:\n\n"
        f"👤 Name: {context.user_data['booking_name']}\n"
        f"📅 Date: {date}",
        reply_markup=get_time_keyboard(date)
    )
    return BOOKING_TIME

async def select_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.data == "already_booked":
        await query.answer("⛔ This time is already booked. Please choose another.", show_alert=True)
        return BOOKING_TIME

    if query.data == "past_time":
        await query.answer("⏰ This time has already passed. Please choose a future time.", show_alert=True)
        return BOOKING_TIME

    await query.answer()
    time_val = query.data.replace("time_", "")
    context.user_data['booking_time'] = time_val
    name = context.user_data.get('booking_name')
    date = context.user_data.get('booking_date')
    keyboard = [
        [InlineKeyboardButton("✅ Confirm", callback_data="confirm_booking")],
        [
            InlineKeyboardButton("🔙 Back", callback_data="back_to_time"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_booking"),
        ]
    ]
    await query.edit_message_text(
        f"📋 Please review your booking:\n\n"
        f"👤 Name: {name}\n"
        f"📅 Date: {date}\n"
        f"⏰ Time: {time_val}\n\n"
        f"Tap ✅ Confirm to submit.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return BOOKING_CONFIRM

async def confirm_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    name = context.user_data.get('booking_name')
    date = context.user_data.get('booking_date')
    time_val = context.user_data.get('booking_time')

    if date in booked_slots and time_val in booked_slots[date]:
        await query.edit_message_text(
            f"⛔ Sorry, this time was just booked by someone else.\n\n"
            f"Please choose another time.",
            reply_markup=get_time_keyboard(date)
        )
        return BOOKING_TIME

    if date not in booked_slots:
        booked_slots[date] = []
    booked_slots[date].append(time_val)

    await query.edit_message_text(
        f"✅ Booking confirmed!\n\n"
        f"👤 Name: {name}\n"
        f"📅 Date: {date}\n"
        f"⏰ Time: {time_val}\n\n"
        f"I'll get back to you soon. ✨"
    )

    # 🎵 پیشنهاد آهنگ
    playlist_keyboard = [
        [InlineKeyboardButton("🎵 Play Music", callback_data="play_music")]
    ]
    try:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🎵 A song for you:\n\nWhile you wait, enjoy a random song:",
            reply_markup=InlineKeyboardMarkup(playlist_keyboard)
        )
    except Exception as e:
        print(f"Error sending playlist: {e}")

    if ADMIN_ID:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📅 New Booking Request:\n\n"
                     f"👤 Name: {name}\n"
                     f"📅 Date: {date}\n"
                     f"⏰ Time: {time_val}\n"
                     f"📱 User: @{update.effective_user.username or 'N/A'}"
            )
        except Exception as e:
            print(f"Error notifying admin: {e}")

    return ConversationHandler.END

async def back_to_main_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        get_time_based_message(),
        reply_markup=get_inline_buttons()
    )
    return ConversationHandler.END

async def back_to_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_name = context.user_data.get('booking_name', query.from_user.full_name)
    keyboard = [
        [InlineKeyboardButton("✅ Yes, that's me", callback_data="confirm_name")],
        [
            InlineKeyboardButton("🔙 Back", callback_data="back_to_main"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_booking"),
        ]
    ]
    await query.edit_message_text(
        f"📝 Is this your name?\n\n👤 {user_name}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return BOOKING_NAME

async def back_to_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    today = get_iran_today().strftime("%Y/%m/%d")
    await query.edit_message_text(
        f"📅 Please select a date:\n\n"
        f"👤 Name: {context.user_data['booking_name']}\n"
        f"📆 Today: {today}",
        reply_markup=get_date_keyboard()
    )
    return BOOKING_DATE

async def back_to_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    date = context.user_data.get('booking_date', '')
    await query.edit_message_text(
        f"⏰ Please select a time:\n\n"
        f"👤 Name: {context.user_data['booking_name']}\n"
        f"📅 Date: {date}",
        reply_markup=get_time_keyboard(date)
    )
    return BOOKING_TIME

async def cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Booking cancelled.")
    return ConversationHandler.END

# 🔐 بررسی ادمین
async def check_admin(update: Update) -> bool:
    if str(update.effective_user.id) != str(ADMIN_ID):
        await update.message.reply_text("⛔ Access denied.")
        return False
    return True

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update):
        return
    today = get_iran_today().strftime("%Y/%m/%d")
    await update.message.reply_text(
        f"📊 Bot Stats — {today}\n"
        f"Messages received: {stats['messages']}\n"
        f"Auto-replies sent: {stats['replies']}\n"
        f"Active users: {len(stats['users'])}"
    )

async def cmd_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_enabled
    if not await check_admin(update):
        return
    bot_enabled = False
    await update.message.reply_text("🔴 Bot turned OFF.")

async def cmd_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_enabled
    if not await check_admin(update):
        return
    bot_enabled = True
    await update.message.reply_text("🟢 Bot turned ON.")

async def cmd_blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update):
        return
    if context.args:
        user_id = int(context.args[0])
        blacklist.add(user_id)
        await update.message.reply_text(f"✅ User {user_id} added to blacklist.")
    else:
        await update.message.reply_text("Usage: /blacklist [user_id]")

async def cmd_cooldown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global COOLDOWN
    if not await check_admin(update):
        return
    if not context.args:
        hours = COOLDOWN // 3600
        await update.message.reply_text(f"⏰ Current cooldown: {hours} hours")
        return
    try:
        hours = float(context.args[0])
        if hours <= 0:
            await update.message.reply_text("⛔ Please enter a positive number.")
            return
        COOLDOWN = int(hours * 60 * 60)
        await update.message.reply_text(f"✅ Cooldown changed to {hours} hours.")
    except ValueError:
        await update.message.reply_text("⛔ Invalid number. Example: /cooldown 2")

async def cmd_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update):
        return
    if not booked_slots:
        await update.message.reply_text("📅 No bookings yet.")
        return
    text = "📅 Booked Slots:\n\n"
    for date, times in booked_slots.items():
        text += f"📆 {date}: {', '.join(times)}\n"
    await update.message.reply_text(text)

async def daily_report(context: ContextTypes.DEFAULT_TYPE):
    global stats
    if ADMIN_ID:
        try:
            today = get_iran_today().strftime("%Y/%m/%d")
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📈 Daily Report — {today}\n"
                     f"Messages received: {stats['messages']}\n"
                     f"Auto-replies sent: {stats['replies']}\n"
                     f"Active users: {len(stats['users'])}"
            )
        except Exception as e:
            print(f"Error sending report: {e}")
    stats = {"messages": 0, "replies": 0, "users": set()}

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("stats", cmd_stats))
    application.add_handler(CommandHandler("off", cmd_off))
    application.add_handler(CommandHandler("on", cmd_on))
    application.add_handler(CommandHandler("blacklist", cmd_blacklist))
    application.add_handler(CommandHandler("cooldown", cmd_cooldown))
    application.add_handler(CommandHandler("bookings", cmd_bookings))

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_booking, pattern="^book$")],
        states={
            BOOKING_NAME: [
                CallbackQueryHandler(confirm_name, pattern="^confirm_name$"),
                CallbackQueryHandler(back_to_main_booking, pattern="^back_to_main$"),
                CallbackQueryHandler(cancel_booking, pattern="^cancel_booking$"),
            ],
            BOOKING_DATE: [
                CallbackQueryHandler(select_date, pattern="^date_"),
                CallbackQueryHandler(back_to_name, pattern="^back_to_name$"),
                CallbackQueryHandler(cancel_booking, pattern="^cancel_booking$"),
            ],
            BOOKING_TIME: [
                CallbackQueryHandler(select_time, pattern="^time_|^already_booked$|^past_time$"),
                CallbackQueryHandler(back_to_date, pattern="^back_to_date$"),
                CallbackQueryHandler(cancel_booking, pattern="^cancel_booking$"),
            ],
            BOOKING_CONFIRM: [
                CallbackQueryHandler(confirm_booking, pattern="^confirm_booking$"),
                CallbackQueryHandler(back_to_time, pattern="^back_to_time$"),
                CallbackQueryHandler(cancel_booking, pattern="^cancel_booking$"),
            ],
        },
        fallbacks=[CallbackQueryHandler(cancel_booking, pattern="^cancel_booking$")],
    )
    application.add_handler(conv_handler)

    application.add_handler(CallbackQueryHandler(button_handler))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))

    application.job_queue.run_daily(daily_report, time=dt_time(21, 0))

    print("Bot is running...")
    application.run_polling()
