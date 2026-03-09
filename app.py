import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# កំណត់ការកត់ត្រា (Logging)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- ការកំណត់ (Configurations) ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL") # Render ផ្ដល់ឱ្យស្រាប់
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# រៀបចំ Gemini AI ជាមួយ System Instruction
genai.configure(api_key=GEMINI_API_KEY)
SYSTEM_PROMPT = "អ្នកគឺជាជំនួយការ AI ខ្មែរដ៏ឆ្លាតវៃ។ សូមឆ្លើយតបជាភាសាខ្មែរឱ្យបានសមរម្យ និងប្រើពាក្យ 'បាទ' ឬ 'ចាស'។"
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction=SYSTEM_PROMPT
)

# បង្កើត Flask App
app = Flask(__name__)
application = ApplicationBuilder().token(TOKEN).build()

# --- មុខងារឆ្លើយតបអត្ថបទ (Text Handler) ---
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = model.generate_content(update.message.text)
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"Text Error: {e}")
        await update.message.reply_text("សុំទោស ប្អូនមានបញ្ហាក្នុងការគិតបន្តិច បាទ។")

# --- មុខងារមើលរូបភាព (Image Handler) ---
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # ទាញយករូបភាព
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        
        image_data = {"mime_type": "image/jpeg", "data": bytes(photo_bytes)}
        caption = update.message.caption if update.message.caption else "តើរូបភាពនេះគឺជាអ្វី?"
        
        # ផ្ញើទៅ Gemini
        response = model.generate_content([caption, image_data])
        await update.message.reply_text(response.text)
    except Exception as e:
        logging.error(f"Photo Error: {e}")
        await update.message.reply_text("សុំទោស ប្អូនមើលរូបភាពនេះមិនច្បាស់ទេ បាទ។")

# បញ្ចូល Handler ទៅក្នុង Application
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

# --- ផ្នែក Webhook & Flask ---
@app.route(f'/{TOKEN}', methods=['POST'])
async def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.update_queue.put(update)
    return "OK", 200

@app.route('/')
def index():
    return "Bot is Online!", 200

async def setup_webhook():
    bot = Bot(token=TOKEN)
    # បង្កើត Webhook URL (ឧទាហរណ៍៖ https://your-app.onrender.com/TOKEN)
    webhook_url = f"{RENDER_URL}/{TOKEN}"
    await bot.set_webhook(url=webhook_url)
    logging.info(f"Webhook set to: {webhook_url}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    
    # ចាប់ផ្ដើម Webhook ក្នុង Async Loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup_webhook())
    
    # ដំណើរការ Flask Server
    app.run(host='0.0.0.0', port=port)
