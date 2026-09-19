import yfinance as yf
import pandas as pd
import mplfinance as mpf
import requests
import time
from datetime import datetime, timedelta, timezone

TELEGRAM_TOKEN = '8227215075:AAGFrgKdUE1LeijOPdnRSyZSv-T1mRj0Rxo'
TELEGRAM_CHAT_ID = '8824675734'

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=window-1, adjust=False).mean()
    avg_loss = loss.ewm(com=window-1, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_atr(data, window=14):
    high_low = data['High'] - data['Low']
    high_close = (data['High'] - data['Close'].shift()).abs()
    low_close = (data['Low'] - data['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=window).mean()

pairs = {'EUR/USD': 'EURUSD=X', 'EMAS (XAU/USD)': 'GC=F'}
tz = timezone(timedelta(hours=7)) 
waktu_sekarang = datetime.now(tz).strftime('%Y-%m-%d %H:%M')

for nama_pair, simbol in pairs.items():
    ticker = yf.Ticker(simbol)
    data = ticker.history(period='5d', interval='1h')
    
    if data.empty:
        continue
        
    data['SMA_20'] = data['Close'].rolling(window=20).mean()
    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    data['RSI'] = calculate_rsi(data)
    data['ATR'] = calculate_atr(data)
    
    last_row = data.iloc[-1]
    prev_row = data.iloc[-2]

    is_golden_cross = (prev_row['SMA_20'] < prev_row['SMA_50']) and (last_row['SMA_20'] > last_row['SMA_50'])
    is_death_cross = (prev_row['SMA_20'] > prev_row['SMA_50']) and (last_row['SMA_20'] < last_row['SMA_50'])
    
    jenis_sinyal = "Tren Naik" if last_row['SMA_20'] > last_row['SMA_50'] else "Tren Turun"
    if is_golden_cross: jenis_sinyal = "POTENSI BUY (Golden Cross)"
    elif is_death_cross: jenis_sinyal = "POTENSI SELL (Death Cross)"

    harga = last_row['Close']
    rsi = last_row['RSI']
    atr = last_row['ATR']
    
    kondisi_rsi = "Normal (Aman)"
    if rsi > 70: kondisi_rsi = "OVERBOUGHT (Jenuh Beli - Hati-hati)"
    elif rsi < 30: kondisi_rsi = "OVERSOLD (Jenuh Jual - Hati-hati)"
    
    if "Naik" in jenis_sinyal or "BUY" in jenis_sinyal:
        sl = harga - (1.5 * atr)
        tp = harga + (3.0 * atr)
        saran_posisi = "Saran Posisi: BUY 🟢"
    else:
        sl = harga + (1.5 * atr)
        tp = harga - (3.0 * atr)
        saran_posisi = "Saran Posisi: SELL 🔴"

    berita = ticker.news
    headlines = []
    if berita:
        for n in berita[:3]:
            if 'content' in n and 'title' in n['content']:
                headlines.append(n['content']['title'])
    if not headlines:
        headlines = ["Tidak ada berita utama saat ini."]
    berita_teks = "\n- ".join(headlines)

    # PEMBUATAN GRAFIK
    sma20 = mpf.make_addplot(data['SMA_20'], color='blue', linestyle='--')
    sma50 = mpf.make_addplot(data['SMA_50'], color='red', linestyle='--')
    chart_filename = f'chart_{simbol.replace("=", "")}.png'
    mc = mpf.make_marketcolors(up='green', down='red', edge='inherit', wick='inherit', volume='in')
    s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', gridcolor='gray')
    mpf.plot(data, type='candle', style=s, addplot=[sma20, sma50],
             title=f'Pantauan {nama_pair}',
             ylabel='Harga', figsize=(10, 5),
             savefig=dict(fname=chart_filename, dpi=150, bbox_inches='tight'))

    # AI INTERNAL (Tanpa Kunci API, Anti-Error)
    analisa_ai = f"Halo Bosku! Berdasarkan pantauan grafik terkini, {nama_pair} sedang berada di fase **{jenis_sinyal}**. "
    if "BUY" in saran_posisi:
        analisa_ai += f"Kelihatannya banteng (buyer) lagi kuat nih! 🐂🚀 Posisi RSI ada di {rsi:.1f}, yang berarti {kondisi_rsi.split('(')[0].strip().lower()}. Ruang untuk naik masih terbuka lebar! 📈"
    else:
        analisa_ai += f"Hati-hati, beruang (seller) sedang ngamuk! 🐻🩸 Posisi RSI ada di {rsi:.1f}, statusnya {kondisi_rsi.split('(')[0].strip().lower()}. Mending ikuti arus ke bawah dan jangan paksakan buy ya! 📉"
        
    if "Hati-hati" in kondisi_rsi:
        analisa_ai += "\n\n⚠️ **Peringatan Ekstra:** Karena harganya sudah sangat jenuh, siap-siap waspada kalau harganya tiba-tiba putar balik!"
        
    if headlines[0] != "Tidak ada berita utama saat ini.":
        analisa_ai += f"\n\n📰 **Kabar Pasar Hari Ini:**\nSelain grafik, perhatikan juga isu ini ya Bos:\n_{headlines[0]}_"
        
    analisa_ai += "\n\nSelalu disiplin pakai Stop Loss sesuai rekomendasi di atas ya. Tetap cuan! 💰🤑"

    # KIRIM LAPORAN KE TELEGRAM
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

    url_msg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    pesan_teks = f"💡 Analisa Cerdas:\n\n{analisa_ai}"
    requests.post(url_msg, data={'chat_id': TELEGRAM_CHAT_ID, 'text': pesan_teks, 'parse_mode': 'Markdown'})
    
    time.sleep(3)
