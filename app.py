import os
import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# Anahtarları Render'ın gizli ortam değişkenlerinden çeker
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("Lütfen Render paneline TELEGRAM_TOKEN ve GEMINI_API_KEY değişkenlerini ekleyin!")

genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """
Sen Telegram'da kullanıcılarla sohbet eden samimi, zeki ve neşeli bir yapay zeka asistanısın.
Kuralların:
1. Kullanıcılar sana selam verdiğinde veya hatır sorduğunda ASLA sürekli aynı kalıpla cevap verme. Her defasında farklı kelimeler, farklı cümle yapıları ve özgün ifadeler kullanarak varyasyonlu yanıtlar üret.
2. Doğal ve insan gibi konuş, çok resmi veya mekanik olma.
3. Eğer kullanıcı sana saat veya tarih sorarsa, sistem tarafından sana iletilen anlık zaman bilgisini kullanarak doğru cevabı ver.
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba! Ben senin yapay zeka destekli sohbet botunum. Benimle dilediğin gibi konuşabilirsin!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    now = datetime.datetime.now()
    current_time_str = now.strftime("%H:%M:%S")
    current_date_str = now.strftime("%d.%m.%Y")
    
    prompt = f"[Sistem Bilgisi: Şu anki anlık saat: {current_time_str}, Tarih: {current_date_str}]\nKullanıcı: {user_text}"
    
    try:
        response = model.generate_content(prompt)
        reply_text = response.text if response.text else "Şu an cevap üretemedim, tekrar dener misin?"
    except Exception as e:
        reply_text = "Ufak bir aksaklık oldu, lütfen biraz sonra tekrar dene!"
        print(f"Hata: {e}")

    await update.message.reply_text(reply_text)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot başarıyla başlatıldı ve dinliyor...")
    app.run_polling()

if __name__ == "__main__":
    main()
