import os
import datetime
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

# Render Web Service port uyumluluğu için hafif web sunucusu
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "Last War BROS Bot aktif ve çalışıyor!"

def run_web():
    app_flask.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

# Render ortam değişkenlerinden anahtarları alıyoruz
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY_EUROTISTAN")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("Lütfen Render paneline TELEGRAM_TOKEN ve GEMINI_API_KEY_EUROTISTAN değişkenlerini ekleyin!")

# Google GenAI İstemcisi
client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """
Sen Last War oyununun 2221 numaralı sunucusunda yer alan BROS ittifakının neşeli, samimi ve bilgili bir üyesisin.
Kuralların:
1. Asla sürekli aynı kalıpla cevap verme, her defasında farklı cümleler kur.
2. Doğal ve samimi bir oyuncu gibi konuş.
3. Saat veya tarih sorulduğunda, Türkiye saati ile sunucu saati arasında 5 saat fark olduğunu (sunucu saatinin 5 saat geride olduğunu) hesaba katarak zaman bilgisini ona göre ver.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Selam komutan! BROS ittifakına hoş geldin. 2221 sunucusunda bugün neler yapıyoruz?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if not user_text:
        return
    
    # Zaman hesaplamaları (Türkiye ve Sunucu Saati)
    now_tr = datetime.datetime.now()
    now_server = now_tr - datetime.timedelta(hours=5)
    
    current_time_str = now_tr.strftime("%H:%M:%S")
    server_time_str = now_server.strftime("%H:%M:%S")
    current_date_str = now_tr.strftime("%d.%m.%Y")
    
    prompt = f"[Sistem Bilgisi -> Türkiye Saati: {current_time_str}, Last War 2221 Sunucu Saati: {server_time_str}, Tarih: {current_date_str}]\nKullanıcı: {user_text}"
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                'system_instruction': SYSTEM_INSTRUCTION
            }
        )
        reply_text = response.text if response.text else "Komutan şu an sinyal alamıyorum, tekrar dener misin?"
    except Exception as e:
        reply_text = "Telsizde bir parazit oldu, sonra tekrar dene!"
        print(f"Hata: {e}")

    await update.message.reply_text(reply_text)

def main():
    # Arka planda web sunucusunu başlat
    t = Thread(target=run_web)
    t.start()

    # Telegram Botunu Başlat
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot başarıyla başlatıldı ve dinliyor...")
    # Bekleyen güncellemeleri temizleyerek taze başlat
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
