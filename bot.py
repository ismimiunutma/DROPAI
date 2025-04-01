import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from openai import OpenAI
import os
from datetime import datetime
import requests
import re
import yt_dlp  # Şarkı aramak için eklendi

# OpenAI API anahtarı (kod içinde varsayılan, ama .env varsa oradan çekilecek)
OPENAI_API_KEY_DEFAULT = "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"

# .env dosyasını kontrol et, yoksa varsayılanı kullan
if os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY") or OPENAI_API_KEY_DEFAULT
else:
    openai_api_key = OPENAI_API_KEY_DEFAULT

# OpenAI istemcisi (yeni sürüm)
client = OpenAI(api_key=openai_api_key)

# Telegram bot token'ı
telegram_token = "7805195430:AAGPiHjy1YBtTbwzd3Q9Z_8rORIpz5DpoW0"

# Güncel saat ve tarihi döndüren yardımcı fonksiyon
def get_current_time():
    now = datetime.now()
    return now.strftime("%d/%m/%Y %H:%M:%S")

# CoinGecko API'den anlık coin bilgisi çeken fonksiyon
def get_coin_price(coin_id="bitcoin", currency="usd"):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={currency}"
    try:
        response = requests.get(url)
        data = response.json()
        if coin_id in data and currency in data[coin_id]:
            return data[coin_id][currency]
        else:
            return None
    except Exception as e:
        print(f"CoinGecko API hatası: {e}")
        return None

# YouTube'dan şarkı bağlantısı bulan fonksiyon
def get_song_link(query):
    try:
        ydl_opts = {
            'format': 'bestaudio',
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch',  # YouTube'da arama yapar
            'max_downloads': 1,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(query, download=False)
            if 'entries' in result and result['entries']:
                return result['entries'][0]['webpage_url']
            elif 'webpage_url' in result:
                return result['webpage_url']
            return None
    except Exception as e:
        print(f"Şarkı bulma hatası: {e}")
        return None

# Mesajdan tek coin ve miktarı ayrıştıran fonksiyon
def extract_coin_info(message):
    pattern = r"(\d*\.?\d+)\s*(btc|eth|usdt|sol|xrp|ada|doge|tether|bitcoin|ethereum)"
    match = re.search(pattern, message.lower())
    if match:
        amount = float(match.group(1))
        coin_id = match.group(2)
        coin_map = {
            "btc": "bitcoin",
            "eth": "ethereum",
            "usdt": "tether",
            "sol": "solana",
            "xrp": "xrp",
            "ada": "cardano",
            "doge": "dogecoin",
            "tether": "tether",
            "bitcoin": "bitcoin",
            "ethereum": "ethereum"
        }
        return amount, coin_map.get(coin_id, coin_id), None
    return None, None, None

# Mesajdan coin dönüşümünü ayrıştıran fonksiyon
def extract_coin_conversion(message):
    pattern = r"(\d*\.?\d+)\s*(btc|eth|usdt|sol|xrp|ada|doge|tether|bitcoin|ethereum)\s*(to|kaç)\s*(btc|eth|usdt|sol|xrp|ada|doge|tether|bitcoin|ethereum|usd|eur|try)"
    match = re.search(pattern, message.lower())
    if match:
        amount = float(match.group(1))
        from_coin = match.group(2)
        conversion_word = match.group(3)
        to_currency = match.group(4)
        coin_map = {
            "btc": "bitcoin",
            "eth": "ethereum",
            "usdt": "tether",
            "sol": "solana",
            "xrp": "xrp",
            "ada": "cardano",
            "doge": "dogecoin",
            "tether": "tether",
            "bitcoin": "bitcoin",
            "ethereum": "ethereum",
            "usd": "usd",
            "eur": "eur",
            "try": "try"
        }
        from_coin_id = coin_map.get(from_coin, from_coin)
        to_currency_id = coin_map.get(to_currency, to_currency)
        return amount, from_coin_id, to_currency_id, conversion_word
    return None, None, None, None

# Mesajdan şarkı talebini ayrıştıran fonksiyon
def extract_song_request(message):
    pattern = r"(şarkı aç|play song|play)\s+(.+)"  # "şarkı aç <isim>" veya "play <isim>"
    match = re.search(pattern, message.lower())
    if match:
        return match.group(2).strip()  # Şarkı adı
    return None

# /start komutu
async def start(update: Update, context):
    current_time = get_current_time()
    welcome_msg = f"Merhaba! Ben DROPAI, tüm dillerde insan gibi konuşabilen, esprili ve zeki bir botum. Şu an tarih ve saat: {current_time}. Coin fiyatı için '1 btc', dönüşüm için '1 btc to eth' veya '100 tether kaç try eder', şarkı için 'şarkı aç <isim>' yazabilirsin. Sana nasıl yardımcı olabilirim?"
    await update.message.reply_text(welcome_msg)

# Mesaj işleme
async def handle_message(update: Update, context):
    user_message = update.message.text
    print(f"Mesaj alındı: {user_message}")
    
    # Şarkı talebi kontrolü
    song_query = extract_song_request(user_message)
    if song_query:
        song_link = get_song_link(song_query)
        current_time = get_current_time()
        if song_link:
            response = f"İşte istediğin şarkı: {song_link}\n(Tarih: {current_time})"
            await update.message.reply_text(response)
            return
        else:
            await update.message.reply_text("Şarkıyı bulamadım! Başka bir isimle dene veya daha spesifik ol!")
            return
    
    # Coin dönüşüm kontrolü
    amount, from_coin, to_currency, conversion_word = extract_coin_conversion(user_message)
    if amount and from_coin and to_currency:
        current_time = get_current_time()
        coin_map = {"bitcoin", "ethereum", "tether", "solana", "xrp", "cardano", "dogecoin"}
        is_turkish = conversion_word == "kaç"
        
        if to_currency in coin_map:  # Coin-to-coin dönüşüm
            from_price = get_coin_price(from_coin)
            to_price = get_coin_price(to_currency)
            if from_price and to_price:
                converted_amount = (amount * from_price) / to_price
                if is_turkish:
                    response = f"{amount} {from_coin.upper()} = {converted_amount:.6f} {to_currency.upper()} eder (1 {from_coin.upper()} = ${from_price} USD, 1 {to_currency.upper()} = ${to_price} USD, Tarih: {current_time})"
                else:
                    response = f"{amount} {from_coin.upper()} = {converted_amount:.6f} {to_currency.upper()} (1 {from_coin.upper()} = ${from_price} USD, 1 {to_currency.upper()} = ${to_price} USD, Date: {current_time})"
                await update.message.reply_text(response)
                return
            else:
                error_msg = "Fiyat bilgisi alınamadı. Doğru yazdığından emin ol!" if is_turkish else "Price info unavailable. Check your spelling!"
                await update.message.reply_text(f"{from_coin.upper()} veya {to_currency.upper()} için {error_msg}")
                return
        else:  # Coin-to-fiat dönüşüm
            price = get_coin_price(from_coin, to_currency)
            if price:
                total_value = amount * price
                if is_turkish:
                    response = f"{amount} {from_coin.upper()} = {total_value:.2f} {to_currency.upper()} eder (1 {from_coin.upper()} = {price} {to_currency.upper()}, Tarih: {current_time})"
                else:
                    response = f"{amount} {from_coin.upper()} = {total_value:.2f} {to_currency.upper()} (1 {from_coin.upper()} = {price} {to_currency.upper()}, Date: {current_time})"
                await update.message.reply_text(response)
                return
            else:
                error_msg = "Fiyat bilgisi alınamadı. Doğru yazdığından emin ol!" if is_turkish else "Price info unavailable. Check your spelling!"
                await update.message.reply_text(f"{from_coin.upper()} için {to_currency.upper()} cinsinden {error_msg}")
                return
    
    # Tek coin sorgusu kontrolü
    amount, coin_id, _ = extract_coin_info(user_message)
    if amount and coin_id:
        price = get_coin_price(coin_id)
        current_time = get_current_time()
        if price:
            total_value = amount * price
            response = f"{amount} {coin_id.upper()} anlık değeri: ${total_value:.2f} USD (1 {coin_id.upper()} = ${price} USD, Tarih: {current_time})"
            await update.message.reply_text(response)
            return
        else:
            await update.message.reply_text(f"{coin_id.upper()} için fiyat bilgisi alınamadı. Doğru yazdığından emin ol veya başka bir coin dene!")
            return
    
    # Coin veya şarkı sorgusu değilse OpenAI ile devam et
    try:
        current_time = get_current_time()
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Sen DROPAI adında esprili, yardımsever ve zeki bir botsun. Kullanıcının dilinde akıcı, mantıklı ve güncel bilgilerle cevap ver. Şu anki tarih ve saat: {current_time}. Gerektiğinde web’den veya bilinen kaynaklardan en son bilgileri araştırıp sun (bilgin 2025’e kadar güncel). Sorulara net ve doğru yanıtlar ver, eğer kesin bilgi yoksa bunu belirt ve tahmini bir cevapla espri yap. Espri yapmayı unutma!"},
                {"role": "user", "content": user_message}
            ]
        )
        
        # Yanıtı kullanıcıya gönder
        bot_response = completion.choices[0].message.content
        await update.message.reply_text(bot_response)
    
    except Exception as e:
        print(f"OpenAI hatası: {e}")
        await update.message.reply_text("Bir hata oldu, devrelerim karıştı! Tekrar dene lütfen.")

# Ana fonksiyon
def main():
    try:
        application = Application.builder().token(telegram_token).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        print("Bot başlatılıyor...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f"Bot başlatılırken hata: {e}")

if __name__ == "__main__":
    main()