import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
from google import genai
from PIL import Image
from datetime import datetime, timedelta, timezone

# --- PENGATURAN ---
TELEGRAM_TOKEN = '8227215075:AAFWFpOqnaicGk1Tc51oO51sFQAhENheiqw'
TELEGRAM_CHAT_ID = '8824675734'
GEMINI_API_KEY = 'AQ.Ab8RN6IZDPqbh35JaLcl5Vs8Cdvq-CvNx6A8cMNPz2_XQ-aI5Q'

client = genai.Client(api_key=GEMINI_API_KEY)

def send_telegram_split(photo_path, header, analisa):
    # 1. Kirim Foto + Header Pendek (Aman dari limit)
    url_photo = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(photo_path, 'rb') as photo:
        requests.post(url_photo, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': header}, files={'photo': photo})
    
    # 2. Kirim Analisa AI Panjang sebagai teks biasa
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

    if is_golden_cross:
        jenis_sinyal = "🔥 POTENSI BUY (Golden Cross) 🔥"
    elif is_death_cross:
        jenis_sinyal = "❄️ POTENSI SELL (Death Cross) ❄️"
    else:
        if last_row['SMA_20'] > last_row['SMA_50']:
            jenis_sinyal = "📈 Tren Naik (Biru di atas Merah)"
        else:
            jenis_sinyal = "📉 Tren Turun (Biru di bawah Merah)"

    harga = last_row['Close']
    
    prompt = f"""
    Kamu adalah analis forex profesional. 
    Saat ini status pasar EUR/USD adalah: {jenis_sinyal} di harga {harga:.4f}.
    Tolong lihat gambar grafik terlampir (Garis biru: SMA 20, merah: SMA 50).
    Berikan laporan ringkas mengenai tren saat ini, apakah ada potensi perubahan arah, dan saran langkah untuk trader.
    Jangan gunakan teks tebal berlebihan.
    """
    
    try:
        img = Image.open(chart_filename)
        response = client.models.generate_content(model='gemini-3.6-flash', contents=[prompt, img])
        analisa_ai = response.text
    except Exception as e:
        analisa_ai = f"AI Gemini sedang sibuk. Error: {e}"

    tz = timezone(timedelta(hours=7)) 
    waktu_sekarang = datetime.now(tz).strftime('%Y-%m-%d %H:%M')

    header = f"🤖 **Laporan Rutin 1 Jam** 🤖\n⏰ Waktu: {waktu_sekarang} WIB\n💰 Harga: {harga:.4f}\n🚦 Status: {jenis_sinyal}"
    
    send_telegram_split(chart_filename, header, analisa_ai)

if __name__ == "__main__":
    analyze_and_alert()
