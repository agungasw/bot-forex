import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests

# --- PENGATURAN BOT TELEGRAM ANDA ---
TELEGRAM_TOKEN = '8227215075:AAFWFpOqnaicGk1Tc51oO51sFQAhENheiqw'
TELEGRAM_CHAT_ID = '8824675734'

def send_telegram_photo(photo_path, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(photo_path, 'rb') as photo:
        payload = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}
        files = {'photo': photo}
        requests.post(url, data=payload, files=files)

def analyze_and_alert():
    print("Mengecek harga EUR/USD...")
    data = yf.download('EURUSD=X', period='5d', interval='1h')
    data.index = data.index.tz_localize(None)

    data['SMA_20'] = data['Close'].rolling(window=20).mean()
    data['SMA_50'] = data['Close'].rolling(window=50).mean()

    last_row = data.iloc[-1]
    prev_row = data.iloc[-2]

    is_golden_cross = (prev_row['SMA_20'] < prev_row['SMA_50']) and (last_row['SMA_20'] > last_row['SMA_50'])
    is_death_cross = (prev_row['SMA_20'] > prev_row['SMA_50']) and (last_row['SMA_20'] < last_row['SMA_50'])

    # UNTUK TESTING SAAT INI AGAR NOTIFIKASI PASTI MASUK, HAPUS TANDA '#' DI BAWAH INI:
    # is_golden_cross = True

    if is_golden_cross or is_death_cross:
        plt.figure(figsize=(10, 5))
        plt.plot(data.index, data['Close'], label='Harga EUR/USD', color='black')
        plt.plot(data.index, data['SMA_20'], label='SMA 20', color='blue')
        plt.plot(data.index, data['SMA_50'], label='SMA 50', color='red')
        plt.title('Peringatan Sinyal EUR/USD')
        plt.legend()
        plt.grid(True)
        chart_filename = 'sinyal_chart.png'
        plt.savefig(chart_filename)
        plt.close()

        if is_golden_cross:
            pesan = f"🟢 **SINYAL BUY EUR/USD** 🟢\nSMA 20 memotong ke atas SMA 50!\nHarga saat ini: {last_row['Close']:.4f}"
        else:
            pesan = f"🔴 **SINYAL SELL EUR/USD** 🔴\nSMA 20 memotong ke bawah SMA 50!\nHarga saat ini: {last_row['Close']:.4f}"

        send_telegram_photo(chart_filename, pesan)
        print("Sinyal berhasil dikirim!")
    else:
        print("Belum ada sinyal.")

if __name__ == "__main__":
    analyze_and_alert()
