import os
import time
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
AUTO_REPLY_TEXT = "Hi! I'm not available right now, but I'll get back to you as soon as possible. 🙏"

app = Flask(__name__)

# 🧠 حافظه: زمان آخرین پاسخ خودکار به هر کاربر
last_reply_time = {}

# ⏰ زمان استراحت: ۶ ساعت به ثانیه (۶ × ۶۰ × ۶۰)
COOLDOWN = 6 * 60 * 60

@app.route('/')
@app.route('/health')
def home():
    return "Bot is running"

async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    
    user_id = update.effective_user.id
    current_time = time.time()
    
    # اگه توی ۶ ساعت گذشته به این کاربر پاسخ خودکار داده شده، دوباره نده
    if user_id in last_reply_time:
        if current_time - last_reply_time[user_id] < COOLDOWN:
            return
    
    # پاسخ خودکار بفرست و زمانش رو ثبت کن
    await update.message.reply_text(AUTO_REPLY_TEXT)
    last_reply_time[user_id] = current_time

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))
    print("ربات روشن شد...")
    application.run_polling()




    