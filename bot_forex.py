import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
import google.generativeai as genai
from PIL import Image

# --- PENGATURAN ---
TELEGRAM_TOKEN = '8227215075:AAFWFpOqnaicGk1Tc51oO51sFQAhENheiqw'
TELEGRAM_CHAT_ID = '8824675734'
GEMINI_API_KEY = 'AQ.Ab8RN6J8qCn_uT-1xepxD_F_FnHlh4NHq3qkd5pp-MLG9DdUdA'

# Konfigurasi "Otak" Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') 

def send_telegram_photo(photo_path, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(photo_path, 'rb') as photo:
        payload = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}
        files = {'photo': photo}
        requests.post(url, data=payload, files=files)

def analyze_and_alert():
    data = yf.Ticker('EURUSD=X').history(period='5d', interval='1h')
    data.index = data.index.tz_localize(None)

    data['SMA_20'] = data['Close'].rolling(window=20).mean()
    data['SMA_50'] = data['Close'].rolling(window=50).mean()

    last_row = data.iloc[-1]
    prev_row = data.iloc[-2]

    is_golden_cross = (prev_row['SMA_20'] < prev_row['SMA_50']) and (last_row['SMA_20'] > last_row['SMA_50'])
    is_death_cross = (prev_row['SMA_20'] > prev_row['SMA_50']) and (last_row['SMA_20'] < last_row['SMA_50'])

    # UNTUK MENGETES GEMINI SEKARANG JUGA, HAPUS TANDA PAGAR (#) DI BAWAH INI:
    # is_golden_cross = True

    if is_golden_cross or is_death_cross:
        # 1. Membuat Grafik
        plt.figure(figsize=(10, 5))
        plt.plot(data.index, data['Close'], label='Harga EUR/USD', color='black', linewidth=2)
        plt.plot(data.index, data['SMA_20'], label='SMA 20 (Biru)', color='blue', linestyle='--')
        plt.plot(data.index, data['SMA_50'], label='SMA 50 (Merah)', color='red', linestyle='--')
        plt.title('Sinyal EUR/USD')
        plt.legend()
        plt.grid(True, linestyle=':', alpha=0.6)
        chart_filename = 'sinyal_chart.png'
        plt.savefig(chart_filename, dpi=300, bbox_inches='tight')
        plt.close()

        # 2. Persiapan Data untuk Gemini
        jenis_sinyal = "BUY (Golden Cross)" if is_golden_cross else "SELL (Death Cross)"
        harga = last_row['Close']
        
        # 3. Bot bertanya kepada Gemini layaknya manusia
        prompt = f"""
        Kamu adalah analis forex profesional. 
        Saya mendeteksi sinyal {jenis_sinyal} pada EUR/USD di harga {harga:.4f}.
        Tolong lihat gambar grafik terlampir (Garis biru: SMA 20, merah: SMA 50).
        Berikan komentar singkat dan tajam (maksimal 2 paragraf pendek) mengenai kondisi chart ini dan apa yang sebaiknya trader lakukan.
        Jangan gunakan teks tebal berlebihan.
        """
        
        try:
            img = Image.open(chart_filename)
            response = model.generate_content([prompt, img])
            analisa_ai = response.text
        except Exception as e:
            analisa_ai = "AI Gemini sedang sibuk, tidak dapat memuat analisa."

        # 4. Menggabungkan Sinyal + Analisa Gemini
        pesan_final = f"🤖 SINYAL {jenis_sinyal} 🤖\nHarga: {harga:.4f}\n\nAnalisa Gemini AI:\n{analisa_ai}"

        send_telegram_photo(chart_filename, pesan_final)

if __name__ == "__main__":
    analyze_and_alert()
