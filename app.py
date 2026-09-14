import os
import time
import threading
from datetime import datetime, time as dt_time
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# ⚙️ تنظیمات اصلی
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")
AUTO_REPLY_TEXT = "Hi! I'm not available right now, but I'll get back to you as soon as possible. 🙏"
COOLDOWN =60  # 6 hours

# 📞 اطلاعات تماس شما
PHONE_NUMBER = "+989058407880"
INSTAGRAM_ID = "m_gh.tech"

app = Flask(__name__)

# 🧠 حافظه‌ها
last_reply_time = {}
blacklist = set()
bot_enabled = True
stats = {"messages": 0, "replies": 0, "users": set()}

# 🎨 دکمه‌های شیشه‌ای
def get_inline_buttons():
    keyboard = [
        [
            InlineKeyboardButton("📞 Emergency Contact", callback_data="urgent"),
            InlineKeyboardButton("📱 Instagram", url=f"https://instagram.com/{INSTAGRAM_ID}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# 🎯 انتخاب متن بر اساس ساعت روز (انگلیسی)
def get_time_based_message():
    now = datetime.now().time()
    weekday = datetime.now().weekday()

    if weekday in (5, 6):
        return "It's the weekend — I'll get back to you as soon as I can. 🙏"
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

# 📨 پاسخ خودکار
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_enabled, stats
    
    # گرفتن پیام (چه عادی، چه Business)
    message = update.message or update.business_message
    if not message:
        return
    
    # فقط چت‌های خصوصی
    if update.effective_chat.type != "private":
        return
    
    user_id = update.effective_user.id
    current_time = time.time()
    
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
    
    await message.reply_text(
        get_time_based_message(),
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
    await update.message.reply_text(
        f"📊 Bot Stats:\n"
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

# 📅 گزارش روزانه
async def daily_report(context: ContextTypes.DEFAULT_TYPE):
    global stats
    if ADMIN_ID:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📈 Daily Report:\n"
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
    
    # دکمه‌ها
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # پیام‌های عادی و Business
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))
    
    # گزارش روزانه ساعت ۲۱:۰۰
    application.job_queue.run_daily(daily_report, time=dt_time(21, 0))
    
    print("Bot is running...")
    application.run_polling()
