import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# توکن از متغیر محیطی خونده می‌شه
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
AUTO_REPLY_TEXT = "Hi! I'm not available right now, but I'll get back to you as soon as possible. 🙏"

app = Flask(__name__)

@app.route('/')
@app.route('/health')
def home():
    return "Bot is running"

async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text(AUTO_REPLY_TEXT)

def run_flask():
    """وب‌سرور رو توی ترد جداگانه اجرا می‌کنه."""
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

if __name__ == '__main__':
    # وب‌سرور رو توی ترد جداگانه اجرا کن
    threading.Thread(target=run_flask, daemon=True).start()

    # ربات رو توی ترد اصلی اجرا کن (مهم!)
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))
    print("ربات روشن شد...")
    application.run_polling()




    