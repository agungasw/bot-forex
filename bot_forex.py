import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
import base64
from datetime import datetime, timedelta, timezone
import os

# --- PENGATURAN ---
TELEGRAM_TOKEN = '8227215075:AAGFrgKdUE1LeijOPdnRSyZSv-T1mRj0Rxo'
TELEGRAM_CHAT_ID = '8824675734'
GEMINI_API_KEY = 'KUNCI_AQ_ANDA_YANG_BARU'

def send_telegram_split(photo_path, header, analisa):
    url_photo = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(photo_path, 'rb') as photo:
        requests.post(url_photo, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': header}, files={'photo': photo})
    
    url_msg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    pesan_teks = f"**Analisa AI:**\n{analisa}"
    requests.post(url_msg, data={'chat_id': TELEGRAM_CHAT_ID, 'text': pesan_teks, 'parse_mode': 'Markdown'})

def analyze_and_alert():
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
    
    try:
        with open(chart_filename, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        url_gemini = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/png", "data": encoded_image}}
                ]
            }]
        }
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url_gemini, headers=headers, json=payload)
        
        if response.status_code == 200:
            analisa_ai = response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            analisa_ai = f"Error dari Google: {response.text}"
    except Exception as e:
        analisa_ai = f"Gagal menghubungi Google: {e}"

    tz = timezone(timedelta(hours=7)) 
    waktu_sekarang = datetime.now(tz).strftime('%Y-%m-%d %H:%M')
    header = f"🤖 **Laporan Otomatis GitHub** 🤖\n⏰ Waktu: {waktu_sekarang} WIB\n💰 Harga: {harga:.4f}\n🚦 Status: {jenis_sinyal}"
    
    send_telegram_split(chart_filename, header, analisa_ai)

if __name__ == "__main__":
    analyze_and_alert()
    
