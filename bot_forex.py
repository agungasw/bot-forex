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

          # Menyusun pesan teks yang edukatif
        if is_golden_cross:
            pesan = (
                f"🟢 **INSTRUKSI: BUY (BELI)** 🟢\n"
                f"Harga EUR/USD: {last_row['Close']:.4f}\n\n"
                f"🧠 **Kenapa harus BUY?**\n"
                f"Coba lihat grafik di atas. Garis Biru (rata-rata pergerakan harga 20 jam terakhir) baru saja menembus ke ATAS Garis Merah (rata-rata 50 jam).\n\n"
                f"📚 **Pelajaran Teknikal:**\n"
                f"Kondisi ini disebut 'Golden Cross'. Ini artinya momentum pembeli (buyer) dalam jangka pendek sedang sangat kuat dan mendominasi. Secara statistik, saat garis biru berada di atas merah, tren harga akan cenderung terus NAIK.\n\n"
                f"💡 **Saran Trading:**\n"
                f"Silakan buka posisi BUY. Namun, market bisa berbalik arah kapan saja karena berita ekonomi tak terduga. Jadi, JANGAN LUPA pasang Stop Loss (Batas Kerugian) di bawah harga saat ini!"
            )
        else:
            pesan = (
                f"🔴 **INSTRUKSI: SELL (JUAL)** 🔴\n"
                f"Harga EUR/USD: {last_row['Close']:.4f}\n\n"
                f"🧠 **Kenapa harus SELL?**\n"
                f"Coba lihat grafik di atas. Garis Biru (rata-rata pergerakan harga 20 jam terakhir) baru saja menukik ke BAWAH Garis Merah (rata-rata 50 jam).\n\n"
                f"📚 **Pelajaran Teknikal:**\n"
                f"Kondisi ini disebut 'Death Cross'. Ini artinya momentum penjual (seller) sedang menguasai pasar. Harga jangka pendek merosot lebih cepat dibanding harga jangka menengah, sehingga tren diperkirakan akan terus TURUN.\n\n"
                f"💡 **Saran Trading:**\n"
                f"Silakan buka posisi SELL. JANGAN LUPA pasang Stop Loss (Batas Kerugian) di atas harga saat ini untuk mencegah kerugian jika tiba-tiba tren berbalik arah."
            )

        send_telegram_photo(chart_filename, pesan)
    analyze_and_alert()
