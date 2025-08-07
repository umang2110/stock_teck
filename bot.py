import logging
import yfinance as yf
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask import Flask
from threading import Thread

# ========== Flask Web Server ==========
web_app = Flask('')

@web_app.route('/')
def home():
    return "Bot Alive ✅"

def run_flask():
    web_app.run(host='0.0.0.0', port=8080)

# Start Flask in background
Thread(target=run_flask).start()

BOT_TOKEN = '8225520099:AAHLhMlqZvnQTWW7H8pj9SoAcIcCDhr0kbE'

logging.basicConfig(level=logging.INFO)

TIMEFRAMES = {
    '1h': ('15d', '1h'),
    '1d': ('60d', '1d'),
    '1w': ('1y', '1wk'),
    '1mo': ('5y', '1mo'),
}

# ✅ Define safe_float before usage
def safe_float(series):
    try:
        return float(series.iloc[-1])
    except:
        return None

async def support_resistance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) == 0:
            await update.message.reply_text("Usage: /sr <symbol> [timeframe]\nExample: /sr RELIANCE 1d")
            return

        symbol = context.args[0].upper() + ".NS"
        tf = context.args[1] if len(context.args) > 1 else "1d"

        if tf not in TIMEFRAMES:
            await update.message.reply_text("Invalid timeframe. Use one of: 1h, 1d, 1w, 1mo")
            return

        period, interval = TIMEFRAMES[tf]
        data = yf.download(symbol, period=period, interval=interval)

        if data.empty or len(data) < 50:
            await update.message.reply_text("Not enough data.")
            return

        latest = data.iloc[-1]
        close = float(latest['Close'])
        high = float(latest['High'])
        low = float(latest['Low'])
        volume = int(latest['Volume'])

        # Pivot Points
        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        s1 = 2 * pivot - high

        # Fibonacci Levels
        diff = high - low
        fib_levels = [
            high,
            high - 0.236 * diff,
            high - 0.382 * diff,
            pivot,
            low + 0.382 * diff,
            low + 0.236 * diff,
            low
        ]

        # Bollinger Bands (20)
        if len(data) >= 20:
            sma_bb = data['Close'].rolling(window=20).mean()
            std_bb = data['Close'].rolling(window=20).std()
            upper_bb = safe_float(sma_bb + 2 * std_bb)
            lower_bb = safe_float(sma_bb - 2 * std_bb)
        else:
            upper_bb = lower_bb = None

        # SMAs
        sma20 = safe_float(data['Close'].rolling(window=20).mean()) if len(data) >= 20 else None
        sma50 = safe_float(data['Close'].rolling(window=50).mean()) if len(data) >= 50 else None
        sma100 = safe_float(data['Close'].rolling(window=100).mean()) if len(data) >= 100 else None
        sma200 = safe_float(data['Close'].rolling(window=200).mean()) if len(data) >= 200 else None

        # Collect all indicators
        resistance_levels = [r1, fib_levels[1], fib_levels[2], upper_bb, sma20, sma50, sma100, sma200]
        support_levels = [s1, fib_levels[4], fib_levels[5], lower_bb, sma20, sma50, sma100, sma200]

        # Filter out None or NaN and sort
        resistances = sorted(set(filter(lambda x: x is not None and pd.notna(x), resistance_levels)), reverse=True)
        supports = sorted(set(filter(lambda x: x is not None and pd.notna(x), support_levels)))

        # Get top 3 of each
        top_resistances = resistances[:3]
        top_supports = supports[:3]

        msg = f"📊 *Support & Resistance for {symbol.replace('.NS', '')} ({tf})*\n\n"
        msg += f"💰 Close: {close:.2f}\n📈 High: {high:.2f} | 📉 Low: {low:.2f}\n📦 Volume: {volume}\n\n"

        msg += "🟢 *Resistance Levels:*\n"
        for i, r in enumerate(top_resistances, start=1):
            msg += f"• R{i}: {r:.2f}\n"

        msg += "\n🔴 *Support Levels:*\n"
        for i, s in enumerate(top_supports, start=1):
            msg += f"• S{i}: {s:.2f}\n"

        await update.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

# Start bot
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("sr", support_resistance))
print("Bot running...")
app.run_polling()
