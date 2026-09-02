import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
from google import genai
from PIL import Image
from datetime import datetime, timedelta, timezone
import os

# --- PENGATURAN ---
TELEGRAM_TOKEN = '8227215075:AAGFrgKdUE1LeijOPdnRSyZSv-T1mRj0Rxo'
TELEGRAM_CHAT_ID = '8824675734'
GEMINI_API_KEY = 'AQ.Ab8RN6IZDPqbh35JaLcl5Vs8Cdvq-CvNx6A8cMNPz2_XQ-aI5Q'

print("1. Memulai program...")
client = genai.Client(api_key=GEMINI_API_KEY)

def send_telegram_split(photo_path, header, analisa):
    print("4. Mengirim ke Telegram...")
    url_photo = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(photo_path, 'rb') as photo:
        res1 = requests.post(url_photo, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': header}, files={'photo': photo})
        print("Status Kirim Foto:", res1.text)
    
    url_msg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    pesan_teks = f"**Analisa AI:**\n{analisa}"
    res2 = requests.post(url_msg, data={'chat_id': TELEGRAM_CHAT_ID, 'text': pesan_teks, 'parse_mode': 'Markdown'})
    print("Status Kirim Teks:", res2.text)

def analyze_and_alert():
    print("2. Mengambil data Yahoo Finance...")
    data = yf.Ticker('EURUSD=X').history(period='5d', interval='1h')
    data.index = data.index.tz_localize(None)

    data['SMA_20'] = data['Close'].rolling(window=20).mean()
    data['SMA_50'] = data['Close'].rolling(window=50).mean()

    last_row = data.iloc[-1]
    prev_row = data.iloc[-2]

    is_golden_cross = (prev_row['SMA_20'] < prev_row['SMA_50']) and (last_row['SMA_20'] > last_row['SMA_50'])
    is_death_cross = (prev_row['SMA_20'] > prev_row['SMA_50']) and (last_row['SMA_20'] < last_row['SMA_50'])

    plt.figure(figsize=(10, 5))
    plt.plot(data.index, data['Close'], label='Harga EUR/USD', color='black', linewidth=2)
    plt.plot(data.index, data['SMA_20'], label='SMA 20 (Biru)', color='blue', linestyle='--')
    plt.plot(data.index, data['SMA_50'], label='SMA 50 (Merah)', color='red', linestyle='--')
    plt.title('Update Pantauan EUR/USD')
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.6)
    chart_filename = 'sinyal_chart.png'
    plt.savefig(chart_filename, dpi=300, bbox_inches='tight')
    plt.close()

    jenis_sinyal = "📈 Tren Naik" if last_row['SMA_20'] > last_row['SMA_50'] else "📉 Tren Turun"
    if is_golden_cross: jenis_sinyal = "🔥 POTENSI BUY (Golden Cross) 🔥"
    elif is_death_cross: jenis_sinyal = "❄️ POTENSI SELL (Death Cross) ❄️"

    harga = last_row['Close']
    prompt = f"Status EUR/USD: {jenis_sinyal} di {harga:.4f}. Beri analisa ringkas."
    
    print("3. Meminta Analisa AI Gemini...")
    try:
        img = Image.open(chart_filename)
        response = client.models.generate_content(model='gemini-3.6-flash', contents=[prompt, img])
        analisa_ai = response.text
    except Exception as e:
        analisa_ai = f"AI Gemini error: {e}"

    tz = timezone(timedelta(hours=7)) 
    waktu_sekarang = datetime.now(tz).strftime('%Y-%m-%d %H:%M')
    header = f"🤖 **Laporan Otomatis GitHub** 🤖\n⏰ Waktu: {waktu_sekarang} WIB\n💰 Harga: {harga:.4f}\n🚦 Status: {jenis_sinyal}"
    
    send_telegram_split(chart_filename, header, analisa_ai)
    print("5. Selesai!")

if __name__ == "__main__":
    analyze_and_alert()
    
