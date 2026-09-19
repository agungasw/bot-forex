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
waktu_sekarang_dt = datetime.now(tz)
waktu_sekarang = waktu_sekarang_dt.strftime('%Y-%m-%d %H:%M')

# Deteksi Hari Libur Pasar (Sabtu/Minggu)
hari_ini = waktu_sekarang_dt.weekday()
status_pasar = "BUKA 🟢"
if hari_ini >= 5: # 5=Sabtu, 6=Minggu
    status_pasar = "TUTUP (Libur Akhir Pekan) 😴"

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
    sma20_harga = last_row['SMA_20']
    
    kondisi_rsi = "Normal (Aman)"
    if rsi > 70: kondisi_rsi = "OVERBOUGHT (Jenuh Beli - Hati-hati)"
    elif rsi < 30: kondisi_rsi = "OVERSOLD (Jenuh Jual - Hati-hati)"
    
    # STRATEGI TRADER PRO (Tunggu Koreksi / Pullback)
    if "Naik" in jenis_sinyal or "BUY" in jenis_sinyal:
        if harga <= sma20_harga + (0.2 * atr): 
            saran_posisi = "Harga sedang terkoreksi! Momen bagus BUY 🟢"
            harga_masuk = harga
        else:
            saran_posisi = f"JANGAN BUY SEKARANG! Tunggu harga turun (koreksi) ke {sma20_harga:.4f} baru BUY 🟢"
            harga_masuk = sma20_harga
            
        sl = harga_masuk - (1.5 * atr)
        tp = harga_masuk + (3.0 * atr)
    else:
        if harga >= sma20_harga - (0.2 * atr):
            saran_posisi = "Harga sedang terkoreksi naik! Momen bagus SELL 🔴"
            harga_masuk = harga
        else:
            saran_posisi = f"JANGAN SELL SEKARANG! Tunggu harga naik (koreksi) ke {sma20_harga:.4f} baru SELL 🔴"
            harga_masuk = sma20_harga
            
        sl = harga_masuk + (1.5 * atr)
        tp = harga_masuk - (3.0 * atr)

    berita = ticker.news
    headlines = []
    if berita:
        for n in berita[:3]:
            if 'content' in n and 'title' in n['content']:
                headlines.append(n['content']['title'])
    if not headlines:
        headlines = ["Tidak ada berita utama saat ini."]

    # PEMBUATAN GRAFIK CANDLESTICK
    sma20 = mpf.make_addplot(data['SMA_20'], color='blue', linestyle='--')
    sma50 = mpf.make_addplot(data['SMA_50'], color='red', linestyle='--')
    chart_filename = f'chart_{simbol.replace("=", "")}.png'
    mc = mpf.make_marketcolors(up='green', down='red', edge='inherit', wick='inherit', volume='in')
    s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', gridcolor='gray')
    mpf.plot(data, type='candle', style=s, addplot=[sma20, sma50],
             title=f'Pantauan {nama_pair}',
             ylabel='Harga', figsize=(10, 5),
             savefig=dict(fname=chart_filename, dpi=150, bbox_inches='tight'))

    # AI INTERNAL PRO VERSION
    analisa_ai = f"Halo Bosku! {nama_pair} saat ini sedang dalam fase **{jenis_sinyal}**. "
    if status_pasar != "BUKA 🟢":
        analisa_ai += "\n\n⚠️ **PERHATIAN: PASAR SEDANG TUTUP/LIBUR!** Jangan membuka posisi sekarang karena rawan Gap (loncatan harga) di hari Senin pagi."
    
    analisa_ai += f"\n\nStrategi Pro: Trik terbaik saat ini adalah bersabar. Seperti saran di atas, jangan masuk di pucuk. Kita tunggu harga memantul di garis biru (SMA 20) sebelum eksekusi."
        
    if "Hati-hati" in kondisi_rsi:
        analisa_ai += f"\n\n⚠️ **Peringatan RSI:** Harga sedang dalam status {kondisi_rsi.split('(')[0].strip().lower()}. Jangan pernah melawan arus atau masuk sembarangan tanpa Stop Loss!"
        
    if headlines[0] != "Tidak ada berita utama saat ini.":
        analisa_ai += f"\n\n📰 **Kabar Pasar Hari Ini:**\nSelain grafik, perhatikan juga isu ini ya Bos:\n_{headlines[0]}_"
        
    analisa_ai += "\n\nTrader yang sabar adalah trader yang cuan! 💰🤑"

    # KIRIM LAPORAN KE TELEGRAM
    header = f"📊 Laporan Otomatis: {nama_pair}\n"
    header += f"🏢 Status Pasar: {status_pasar}\n"
    header += f"⏰ Waktu: {waktu_sekarang} WIB\n"
    header += f"🏷️ Harga Saat Ini: {harga:.4f}\n"
    header += f"📈 Tren: {jenis_sinyal}\n"
    header += f"📉 RSI: {rsi:.1f} ({kondisi_rsi})\n\n"
    header += f"🎯 Saran: {saran_posisi}\n"
    header += f"✅ Take Profit (TP): {tp:.4f}\n"
    header += f"❌ Stop Loss (SL): {sl:.4f}"

    url_photo = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(chart_filename, 'rb') as photo:
        requests.post(url_photo, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': header}, files={'photo': photo})

    url_msg = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    pesan_teks = f"💡 Analisa Cerdas (Mode Pro):\n\n{analisa_ai}"
    requests.post(url_msg, data={'chat_id': TELEGRAM_CHAT_ID, 'text': pesan_teks, 'parse_mode': 'Markdown'})
    
    time.sleep(3)
