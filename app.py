import os
import time
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

# 🎯 مراحل رزرو وقت
BOOKING_NAME, BOOKING_DATE, BOOKING_TIME = range(3)

# 🌍 تاریخ امروز ایران به شمسی
def get_iran_today():
    now_iran = datetime.now(IRAN_TZ)
    return JalaliDate(now_iran.date())

# 🕐 ساعت فعلی ایران
def get_iran_time():
    return datetime.now(IRAN_TZ).strftime("%H:%M:%S")

# 🎨 دکمه‌های شیشه‌ای
def get_inline_buttons():
    keyboard = [
        [
            InlineKeyboardButton("📞 Emergency Contact", callback_data="urgent"),
            InlineKeyboardButton("📱 Instagram", url=f"https://instagram.com/{INSTAGRAM_ID}"),
        ],
        [
            InlineKeyboardButton("📅 Book Appointment", callback_data="book"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# 🎯 انتخاب متن بر اساس ساعت روز
def get_time_based_message():
    now = datetime.now(IRAN_TZ).time()
    today = get_iran_today()
    weekday = today.weekday()

    if weekday in (5, 6):
        return "It's the weekend — I'll get back to you as soon as I can. ✨"
    elif now >= dt_time(0, 0) and now < dt_time(12, 0):
        return "Good morning! I'm not available right now, but I'll reply as soon as I see your message. ☀️"
    elif now >= dt_time(12, 0) and now < dt_time(20, 0):
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

- If the message is an EMOTIONAL message (like "I miss you", "I love you", "دلم برات تنگ شده", "دوستت دارم") OR a FAREWELL message (like "goodbye", "خداحافظ", "bye", "فعلاً", "بای"), generate a SHORT, warm auto-reply in the SAME language as the message.
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

# 🖱️ مدیریت دکمه‌ها
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "urgent":
        await query.edit_message_text(
            f"🚨 Emergency Contact:\n"
            f"📞 Phone: {PHONE_NUMBER}\n\n"
            f"Please call if it's urgent."
        )

# 📅 ساخت تقویم ۵ روزه شمسی (از امروز ایران)
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

# ⏰ ساخت دکمه‌های ساعت (۸ صبح تا ۸ شب، هر ۲ ساعت)
def get_time_keyboard():
    times = ["08:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00"]
    keyboard = []
    row = []
    for t in times:
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
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_booking")]
    ]
    await query.edit_message_text(
        f"📝 Is this your name?\n\n👤 {user_name}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return BOOKING_NAME

# 📅 تایید اسم -> نمایش تقویم با تاریخ امروز
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

# 📅 انتخاب تاریخ -> نمایش ساعت با تاریخ و ساعت فعلی
async def select_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    date = query.data.replace("date_", "")
    context.user_data['booking_date'] = date
    current_time = get_iran_time()
    await query.edit_message_text(
        f"⏰ Please select a time:\n\n"
        f"👤 Name: {context.user_data['booking_name']}\n"
        f"📅 Date: {date}\n"
        f"🕐 Current Time: {current_time}",
        reply_markup=get_time_keyboard()
    )
    return BOOKING_TIME

# ⏰ انتخاب ساعت -> تایید نهایی
async def select_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    time_val = query.data.replace("time_", "")
    context.user_data['booking_time'] = time_val

    name = context.user_data.get('booking_name')
    date = context.user_data.get('booking_date')

    await query.edit_message_text(
        f"✅ Booking confirmed!\n\n"
        f"👤 Name: {name}\n"
        f"📅 Date: {date}\n"
        f"⏰ Time: {time_val}\n\n"
        f"I'll get back to you soon. ✨"
    )

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

# 🔙 بازگشت به مرحله تایید اسم
async def back_to_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_name = context.user_data.get('booking_name', query.from_user.full_name)
    keyboard = [
        [InlineKeyboardButton("✅ Yes, that's me", callback_data="confirm_name")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_booking")]
    ]
    await query.edit_message_text(
        f"📝 Is this your name?\n\n👤 {user_name}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return BOOKING_NAME

# 🔙 بازگشت به مرحله انتخاب تاریخ
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

# ❌ انصراف
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

# 📊 دستور آمار
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

# 🔴 خاموش کردن ربات
async def cmd_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_enabled
    if not await check_admin(update):
        return
    bot_enabled = False
    await update.message.reply_text("🔴 Bot turned OFF.")

# 🟢 روشن کردن ربات
async def cmd_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_enabled
    if not await check_admin(update):
        return
    bot_enabled = True
    await update.message.reply_text("🟢 Bot turned ON.")

# 🚫 اضافه کردن به لیست سیاه
async def cmd_blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update):
        return
    if context.args:
        user_id = int(context.args[0])
        blacklist.add(user_id)
        await update.message.reply_text(f"✅ User {user_id} added to blacklist.")
    else:
        await update.message.reply_text("Usage: /blacklist [user_id]")

# ⏰ تغییر زمان Cooldown
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

# 📅 گزارش روزانه
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

# 🌐 اجرای وب‌سرور
def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# 🚀 اجرای اصلی
if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # دستورات ادمین
    application.add_handler(CommandHandler("stats", cmd_stats))
    application.add_handler(CommandHandler("off", cmd_off))
    application.add_handler(CommandHandler("on", cmd_on))
    application.add_handler(CommandHandler("blacklist", cmd_blacklist))
    application.add_handler(CommandHandler("cooldown", cmd_cooldown))

    # هندلر مکالمه رزرو
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_booking, pattern="^book$")],
        states={
            BOOKING_NAME: [
                CallbackQueryHandler(confirm_name, pattern="^confirm_name$"),
                CallbackQueryHandler(cancel_booking, pattern="^cancel_booking$"),
            ],
            BOOKING_DATE: [
                CallbackQueryHandler(select_date, pattern="^date_"),
                CallbackQueryHandler(back_to_name, pattern="^back_to_name$"),
                CallbackQueryHandler(cancel_booking, pattern="^cancel_booking$"),
            ],
            BOOKING_TIME: [
                CallbackQueryHandler(select_time, pattern="^time_"),
                CallbackQueryHandler(back_to_date, pattern="^back_to_date$"),
                CallbackQueryHandler(cancel_booking, pattern="^cancel_booking$"),
            ],
        },
        fallbacks=[CallbackQueryHandler(cancel_booking, pattern="^cancel_booking$")],
    )
    application.add_handler(conv_handler)

    # دکمه‌ها (Emergency + Instagram)
    application.add_handler(CallbackQueryHandler(button_handler))

    # پیام‌های عادی
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))

    # گزارش روزانه ساعت ۲۱:۰۰
    application.job_queue.run_daily(daily_report, time=dt_time(21, 0))

    print("Bot is running...")
    application.run_polling()
