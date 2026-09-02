import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta, timezone

TELEGRAM_TOKEN = '8227215075:AAGFrgKdUE1LeijOPdnRSyZSv-T1mRj0Rxo'
TELEGRAM_CHAT_ID = '8824675734'

print("Mulai mengambil data Yahoo...")
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

# Logika Analisa Tanpa Google
jenis_sinyal = "📈 Tren Naik (Harga di atas rata-rata)" if last_row['SMA_20'] > last_row['SMA_50'] else "📉 Tren Turun (Harga di bawah rata-rata)"
if is_golden_cross: jenis_sinyal = "🔥 POTENSI BUY (Golden Cross) 🔥"
elif is_death_cross: jenis_sinyal = "❄️ POTENSI SELL (Death Cross) ❄️"

harga = last_row['Close']
tz = timezone(timedelta(hours=7)) 
waktu_sekarang = datetime.now(tz).strftime('%Y-%m-%d %H:%M')

header = f"🤖 **Laporan Otomatis Forex EUR/USD** 🤖\n⏰ Waktu: {waktu_sekarang} WIB\n💰 Harga Terkini: {harga:.4f}\n🚦 Status Sinyal: {jenis_sinyal}\n\n*Catatan: Bot sekarang berjalan mandiri dan anti-error!*"

print("Mengirim Foto dan Analisa ke Telegram...")
url_photo = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
with open(chart_filename, 'rb') as photo:
    res1 = requests.post(url_photo, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': header}, files={'photo': photo})
    print("Status Pengiriman:", res1.text)

print("Selesai total!")
