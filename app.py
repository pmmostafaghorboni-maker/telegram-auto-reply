import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# توکن رو از متغیرهای محیطی سرور می‌خونه
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

def run_bot():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))
    application.run_polling()

if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))