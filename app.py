import os
import asyncio
import datetime
from zoneinfo import ZoneInfo
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from google import genai

# ---------------------------------------------------------
# YÖNETİCİ LİSTESİ
# ---------------------------------------------------------
YONETICI_LISTESI = [5502934982]

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY_EUROTISTAN")
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("Lütfen Render paneline TELEGRAM_TOKEN ve GEMINI_API_KEY_EUROTISTAN değişkenlerini ekleyin!")

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """
Sen Last War oyununun 2221 numaralı sunucusunda yer alan BROS ittifakının neşeli, samimi ve bilgili bir üyesisin.
Kuralların:
1. Asla sürekli aynı kalıpla cevap verme, her defasında farklı ve doğal cümleler kur.
2. Doğal ve samimi bir oyuncu gibi konuş.
3. Saat veya tarih sorulduğunda, Türkiye saati ile oyun içi sunucu saati arasında 5 saat fark olduğunu (sunucu saatinin 5 saat geride olduğunu) hesaba kat. "Bizim saat" kelimesini kullanma; "Türkiye saati" ve "Sunucu saati" ifadelerini kullan.
4. Oyun içi konularda Last War kavramlarını (fırınlar, Sezon 2 kutup kışı, T10 araştırmaları, VS günleri, BROS ittifakı) temel alarak cevap ver.
5. Kullanıcı resim/ekran görüntüsü gönderdiğinde görseldeki detayları dikkatlice analiz et ve yardımcı ol.
"""

chat_histories = {}

async def start(update: Update, context):
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type
    
    if chat_type == "private" and user_id not in YONETICI_LISTESI:
        return
        
    await update.message.reply_text("Selam komutan! BROS ittifakına hoş geldin. 2221 sunucusunda bugün neler yapıyoruz?")

async def handle_message(update: Update, context):
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type
    
    if chat_type == "private" and user_id not in YONETICI_LISTESI:
        return

    user_text = update.message.text or update.message.caption or ""
    user_text = user_text.replace("@lastsisterbot", "").strip()

    tz_tr = ZoneInfo("Europe/Istanbul")
    now_tr = datetime.datetime.now(tz_tr)
    now_server = now_tr - datetime.timedelta(hours=5)
    
    current_time_str = now_tr.strftime("%H:%M:%S")
    server_time_str = now_server.strftime("%H:%M:%S")
    current_date_str = now_tr.strftime("%d.%m.%Y")
    
    sys_info = f"[Sistem Bilgisi -> Türkiye Saati: {current_time_str}, Last War 2221 Oyun İçi Sunucu Saati: {server_time_str}, Tarih: {current_date_str}]"

    image_bytes = None
    if update.message.photo:
        try:
            photo_file = await update.message.photo[-1].get_file()
            image_bytes = await photo_file.download_as_bytearray()
        except Exception as img_err:
            print(f"Görsel indirme hatası: {img_err}")

    chat_id = update.effective_chat.id
    if chat_id not in chat_histories:
        chat_histories[chat_id] = []
    
    contents = [sys_info]
    for old_msg in chat_histories[chat_id][-4:]:
        contents.append(old_msg)
        
    if user_text:
        contents.append(f"Kullanıcı: {user_text}")
    if image_bytes:
        contents.append({"mime_type": "image/jpeg", "data": bytes(image_bytes)})
        if not user_text:
            contents.append("Kullanıcı bir görsel/ekran görüntüsü gönderdi. Resmi analiz et ve değerlendir.")

    if not user_text and not image_bytes:
        return

    try:
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=contents,
            config={
                'system_instruction': SYSTEM_INSTRUCTION
            }
        )
        reply_text = response.text if response.text else "Komutan anlık sinyal kopması yaşadım, tekrar yazar mısın?"
        
        if user_text:
            chat_histories[chat_id].append(f"Kullanıcı: {user_text}")
        chat_histories[chat_id].append(f"Asistan: {reply_text}")
        
    except Exception as e:
        reply_text = f"Telsizde parazit var komutan! Hata: {e}"
        print(f"Hata detayı: {e}")

    await update.message.reply_text(reply_text)

# Flask & Telegram Uygulaması
app_flask = Flask(__name__)
application = Application.builder().token(TELEGRAM_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, handle_message))

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

async def init_webhook():
    await application.initialize()
    await application.start()
    if WEBHOOK_URL:
        clean_url = WEBHOOK_URL.rstrip('/')
        webhook_link = f"{clean_url}/{TELEGRAM_TOKEN}"
        await application.bot.set_webhook(url=webhook_link)
        print(f"Webhook başarıyla kuruldu: {webhook_link}")

loop.run_until_complete(init_webhook())

@app_flask.route('/')
def home():
    return "Last War BROS Webhook Bot aktif!"

@app_flask.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    loop.create_task(application.process_update(update))
    return 'ok', 200

if __name__ == "__main__":
    app_flask.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
