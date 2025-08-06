import logging
import yfinance as yf
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = '8225520099:AAHLhMlqZvnQTWW7H8pj9SoAcIcCDhr0kbE'  # Replace this

logging.basicConfig(level=logging.INFO)

# Mapping for your desired timeframes
TIMEFRAMES = {
    '1h': ('15d', '1h'),     # 1 hour = 15-day period with 1-hour interval
    '1d': ('60d', '1d'),     # 1 day = 60-day period with 1-day interval
    '1w': ('1y', '1wk'),     # 1 week = 1-year period with 1-week interval
    '1mo': ('5y', '1mo'),    # 1 month = 5-year period with 1-month interval
}

async def support_resistance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) == 0:
            await update.message.reply_text("Usage: /sr <symbol> [timeframe]\nExample: /sr RELIANCE 1h")
            return

        symbol = context.args[0].upper() + ".NS"
        tf = context.args[1] if len(context.args) > 1 else "1d"

        if tf not in TIMEFRAMES:
            await update.message.reply_text("Invalid timeframe. Use one of: 1h, 1d, 1w, 1mo")
            return

        period, interval = TIMEFRAMES[tf]
        data = yf.download(symbol, period=period, interval=interval)

        if data.empty or len(data) < 3:
            await update.message.reply_text("Not enough data found.")
            return

        latest = data.iloc[-1]
        close = float(latest['Close'])
        high = float(latest['High'])
        low = float(latest['Low'])
        volume = int(latest['Volume'])

        # Pivot Point Calculation
        pivot = (high + low + close) / 3
        s1 = 2 * pivot - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)
        r1 = 2 * pivot - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)

        # SMA Calculation
        data['SMA20'] = data['Close'].rolling(window=20).mean()
        data['SMA50'] = data['Close'].rolling(window=50).mean()

        sma20_val = data['SMA20'].iloc[-1]
        sma50_val = data['SMA50'].iloc[-1]

        sma20 = f"{float(sma20_val):.2f}" if pd.notna(sma20_val) else "N/A"
        sma50 = f"{float(sma50_val):.2f}" if pd.notna(sma50_val) else "N/A"

        msg = f"📊 *Support & Resistance for {symbol.replace('.NS', '')} ({tf})*\n\n"
        msg += f"💰 Close: {close:.2f}\n📈 High: {high:.2f} | 📉 Low: {low:.2f}\n\n"
        msg += f"🟢 Resistance:\n• R1: {r1:.2f}\n• R2: {r2:.2f}\n• R3: {r3:.2f}\n\n"
        msg += f"🔴 Support:\n• S1: {s1:.2f}\n• S2: {s2:.2f}\n• S3: {s3:.2f}"

        await update.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

# Start bot
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("sr", support_resistance))
print("Bot running...")
app.run_polling()
