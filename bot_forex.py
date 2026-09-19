import yfinance as yf
import pandas as pd
import mplfinance as mpf
import requests
import base64
import re
import time
from datetime import datetime, timedelta, timezone

TELEGRAM_TOKEN = '8227215075:AAGFrgKdUE1LeijOPdnRSyZSv-T1mRj0Rxo'
TELEGRAM_CHAT_ID = '8824675734'
OPENROUTER_API_KEY = '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'

# Fungsi RSI (Jenuh Beli/Jual)
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=window-1, adjust=False).mean()
    avg_loss = loss.ewm(com=window-1, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# Fungsi ATR (Buat Hitung SL dan TP)
def calculate_atr(data, window=14):
    high_low = data['High'] - data['Low']
    high_close = (data['High'] - data['Close'].shift()).abs()
    low_close = (data['Low'] - data['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=window).mean()

# Daftar Pasar yg Dipantau
pairs = {'EUR/USD': 'EURUSD=X', 'EMAS (XAU/USD)': 'GC=F'}
tz = timezone(timedelta(hours=7)) 
waktu_sekarang = datetime.now(tz).strftime('%Y-%m-%d %H:%M')

print("Mulai mengambil data...")

for nama_pair, simbol in pairs.items():
    print(f"\n==============================")
    print(f"Menganalisa {nama_pair}...")
    ticker = yf.Ticker(simbol)
    data = ticker.history(period='5d', interval='1h')
    
    if data.empty:
        print(f"Data {nama_pair} kosong, lewati.")
        continue
        
    data['SMA_20'] = data['Close'].rolling(window=20).mean()
    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    data['RSI'] = calculate_rsi(data)
    data['ATR'] = calculate_atr(data)
    
    last_row = data.iloc[-1]
    prev_row = data.iloc[-2]

    # Cek Sinyal Tren
    is_golden_cross = (prev_row['SMA_20'] < prev_row['SMA_50']) and (last_row['SMA_20'] > last_row['SMA_50'])
    is_death_cross = (prev_row['SMA_20'] > prev_row['SMA_50']) and (last_row['SMA_20'] < last_row['SMA_50'])
    jenis_sinyal = "Tren Naik" if last_row['SMA_20'] > last_row['SMA_50'] else "Tren Turun"
    if is_golden_cross: jenis_sinyal = "POTENSI BUY (Golden Cross)"
    elif is_death_cross: jenis_sinyal = "POTENSI SELL (Death Cross)"

    # Indikator Penting
    harga = last_row['Close']
    rsi = last_row['RSI']
    atr = last_row['ATR']
    support_terdekat = data['Low'].min()
    resisten_terdekat = data['High'].max()
    
    kondisi_rsi = "Normal (Aman)"
    if rsi > 70: kondisi_rsi = "OVERBOUGHT (Jenuh Beli - Hati-hati)"
    elif rsi < 30: kondisi_rsi = "OVERSOLD (Jenuh Jual - Hati-hati)"
    
    # Hitung SL dan TP (Otomatis menyesuaikan dengan Emas atau Mata Uang)
    if "Naik" in jenis_sinyal or "BUY" in jenis_sinyal:
        sl = harga - (1.5 * atr)
        tp = harga + (3.0 * atr)
        saran_posisi = "Saran Posisi: BUY 🟢"
    else:
        sl = harga + (1.5 * atr)
        tp = harga - (3.0 * atr)
        saran_posisi = "Saran Posisi: SELL 🔴"

    # Ambil Berita (Kalau Ada)
    berita = ticker.news
    headlines = []
    if berita:
        for n in berita[:3]:
            if 'content' in n and 'title' in n['content']:
                headlines.append(n['content']['title'])
    if not headlines:
        headlines = ["Tidak ada berita utama saat ini."]
    berita_teks = "\n- ".join(headlines)

    # Buat Grafik Candlestick
    sma20 = mpf.make_addplot(data['SMA_20'], color='blue', linestyle='--')
    sma50 = mpf.make_addplot(data['SMA_50'], color='red', linestyle='--')
    chart_filename = f'chart_{simbol.replace("=", "")}.png'
    mc = mpf.make_marketcolors(up='green', down='red', edge='inherit', wick='inherit', volume='in')
    s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', gridcolor='gray')
    mpf.plot(data, type='candle', style=s, addplot=[sma20, sma50],
             title=f'Pantauan {nama_pair}',
             ylabel='Harga', figsize=(10, 5),
             savefig=dict(fname=chart_filename, dpi=150, bbox_inches='tight'))

    # Minta AI mikir (Dengan Prompt Keren)
    prompt = f"""Kamu adalah pakar trading Forex & Gold profesional.
Pasar: {nama_pair}
Harga saat ini: {harga:.4f}
Status Tren: {jenis_sinyal}
RSI: {rsi:.1f} ({kondisi_rsi})
Berita Terkini yang beredar: 
- {berita_teks}

Tolong beri pandangan 4-5 kalimat untuk posisi trading. Hubungkan indikator RSI, tren, dan berita kalau beritanya relevan. 
PENTING: Jawab pakai bahasa Indonesia yang asik, pakai icon/emoji (📈📉🚀🔥), TAPI JANGAN pakai simbol bintang (*), pagar (#), atau backtick (`)."""

    url_ai = "https://openrouter.ai/api/v1/chat/completions"
    ai_headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {OPENROUTER_API_KEY}'
    }
    with open(chart_filename, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

    ai_payload = {
        'model': 'google/gemini-2.5-flash',
        'max_tokens': 500,
        'messages': [{
            'role': 'user',
            'content': [
                {'type': 'text', 'text': prompt},
                {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{encoded_image}'}}
            ]
        }]
    }

    analisa_ai = ""
    # Coba 3x kalau server AI penuh
    for percobaan in range(1, 4):
        try:
            response = requests.post(url_ai, headers=ai_headers, json=ai_payload, timeout=60)
            if response.status_code == 200:
                analisa_ai = response.json()['choices'][0]['message']['content']
                break
            time.sleep(5)
        except Exception:
            time.sleep(5)

    if not analisa_ai:
        analisa_ai = "Maaf, AI sedang tidur siang. Coba lagi nanti."

    # Bersihkan simbol agar Telegram tidak error
    analisa_ai = re.sub(r'```[\s\S]*?```', '', analisa_ai)
    analisa_ai = re.sub(r'[`*#_]', '', analisa_ai)
    analisa_ai = analisa_ai.strip()

    # Kirim ke Telegram (Header di Gambar)
    header = f"📊 Laporan Otomatis: {nama_pair}\n"
    header += f"⏰ Waktu: {waktu_sekarang} WIB\n"
    header += f"🏷️ Harga: {harga:.4f}\n"
    header += f"📈 Tren: {jenis_sinyal}\n"
    header += f"📉 RSI: {rsi:.1f} ({kondisi_rsi})\n\n"
    header += f"🎯 {saran_posisi}\n"
    header += f"✅ Take Profit: {tp:.4f}\n"
    header += f"❌ Stop Loss: {sl:.4f}"

    url_photo = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(chart_filename, 'rb') as photo:
        requests.post(url_photo, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': header}, files={'photo': photo})

    # Kirim Teks Analisa AI
    url_msg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    if len(analisa_ai) > 3500: analisa_ai = analisa_ai[:3500] + "\n... (Teks dipotong)"
    pesan_teks = f"💡 Analisa AI:\n\n{analisa_ai}"
    requests.post(url_msg, data={'chat_id': TELEGRAM_CHAT_ID, 'text': pesan_teks})
    
    print(f"Sukses mengirim {nama_pair}!")
    time.sleep(3) # Kasih nafas 3 detik biar bot Telegram tidak spam

print("SELESAI SEMUA!")
