import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update, Bot
import google.generativeai as genai

# កំណត់ Logging ដើម្បីមើល Error ក្នុង Render Logs
logging.basicConfig(level=logging.INFO)

# --- ការកំណត់ (Configurations) ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# រៀបចំ Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
bot = Bot(token=TOKEN)
app = Flask(__name__)

# --- មុខងារឆ្លើយតប (Logic) ---
async def process_update(update_json):
    update = Update.de_json(update_json, bot)
    
    if update.message:
        chat_id = update.message.chat_id
        
        # ១. បើជាអក្សរ
        if update.message.text:
            prompt = update.message.text
            response = model.generate_content(prompt)
            await bot.send_message(chat_id=chat_id, text=response.text)
            
        # ២. បើជារូបភាព
        elif update.message.photo:
            photo_file = await update.message.photo[-1].get_file()
            photo_bytes = await photo_file.download_as_bytearray()
            image_data = {"mime_type": "image/jpeg", "data": bytes(photo_bytes)}
            caption = update.message.caption if update.message.caption else "តើរូបនេះជាអ្វី?"
            response = model.generate_content([caption, image_data])
            await bot.send_message(chat_id=chat_id, text=response.text)

# --- ផ្នែក Flask (Webhook Receiver) ---
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    # ទទួលទិន្នន័យពី Telegram រួចបញ្ជូនទៅ Process
    update_json = request.get_json(force=True)
    asyncio.run(process_update(update_json))
    return "OK", 200

@app.route('/')
def index():
    return "Bot is Alive!", 200

# កំណត់ Webhook ពេល Restart
def set_webhook():
    webhook_url = f"{RENDER_URL}/{TOKEN}"
    success = asyncio.run(bot.set_webhook(url=webhook_url))
    if success:
        print(f"✅ Webhook set to: {webhook_url}")
    else:
        print("❌ Webhook setup failed!")

if __name__ == "__main__":
    set_webhook()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
