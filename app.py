import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update, Bot
import google.generativeai as genai

# បើក Logging ឱ្យអស់ដើម្បីមើល Error ក្នុង Render Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# កែប្រែត្រង់ចំណុចនេះ
genai.configure(api_key=GEMINI_API_KEY)

# ប្រើឈ្មោះម៉ូដែលពេញលេញ និងត្រឹមត្រូវ
model = genai.GenerativeModel('models/gemini-1.5-flash') 

# ប្រសិនបើអ្នកប្រើ System Instruction សូមដាក់បែបនេះ
# model = genai.GenerativeModel(
#     model_name='models/gemini-1.5-flash',
#     system_instruction="អ្នកគឺជាជំនួយការ AI ខ្មែរ។"
# )

bot = Bot(token=TOKEN)
app = Flask(__name__)

async def handle_update(update_json):
    try:
        update = Update.de_json(update_json, bot)
        if not update.message:
            return

        chat_id = update.message.chat_id
        logger.info(f"Received message from {chat_id}")

        if update.message.text:
            response = model.generate_content(update.message.text)
            await bot.send_message(chat_id=chat_id, text=response.text)
        
        elif update.message.photo:
            photo_file = await update.message.photo[-1].get_file()
            photo_bytes = await photo_file.download_as_bytearray()
            image_data = {"mime_type": "image/jpeg", "data": bytes(photo_bytes)}
            response = model.generate_content(["តើរូបនេះជាអ្វី?", image_data])
            await bot.send_message(chat_id=chat_id, text=response.text)

    except Exception as e:
        logger.error(f"Error handling update: {e}")

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.method == "POST":
        update_json = request.get_json(force=True)
        # ប្រើ loop ថ្មីសម្រាប់រាល់ request ដើម្បីការពារ async error
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(handle_update(update_json))
        return "OK", 200

@app.route('/')
def index():
    return "Bot is Alive!", 200

if __name__ == "__main__":
    # កំណត់ Webhook ឡើងវិញរាល់ពេល Start
    webhook_url = f"{RENDER_URL}/{TOKEN}"
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(bot.set_webhook(url=webhook_url))
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
