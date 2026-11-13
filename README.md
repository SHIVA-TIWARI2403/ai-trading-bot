# AI Intraday Trading Bot (Paper & Live Ready)

A Python-based automated Intraday Trading Bot, AI Strategy Screener, and Backtesting Engine designed for algorithmic trading on Indian markets (NSE Cash / Equities).

> [!IMPORTANT]
> **No PAN Card or Demat account needed for Paper Trading!**
> This bot operates in Paper Trading mode with a virtual capital of ₹500 (or custom amount), letting you practice real-time market price action, multi-timeframe trends, and risk management risk-free.

---

## 🌟 Upgraded Features

1. **Multi-Timeframe Analysis (MTF - False Breakout Filter):**
   - **15-Minute Macro Filter:** Uses 15m EMA 50 to confirm the higher timeframe trend.
   - **5-Minute Entry Trigger:** Only triggers BUYs when the macro trend is BULLISH, and SHORTs when BEARISH. Eliminates counter-trend fakeouts!
2. **Dynamic Trailing Stop Loss (TSL - Profit Lock):**
   - **Level 1 (Break-Even):** At 1:1 Risk-to-Reward, Stop Loss automatically jumps to Entry Price (Trade becomes 100% risk-free).
   - **Level 2 (Locking Profit):** At 1.5R gain, Stop Loss trails higher to lock in minimum 0.5R profit.
3. **Telegram Mobile Alerts (Instant Notifications 📲):**
   - Get instant phone alerts on Telegram whenever a trade signal is detected, orders are placed, Trailing SL moves, or Target is hit.
4. **Historical Backtesting Engine (`backtester.py` 🧪):**
   - Test strategy performance across past 60 days of historical intraday data.
   - Computes Win Rate %, Profit Factor, Max Drawdown, and Net Returns.
5. **Strict Risk Management (Capital Protection 🛡️):**
   - 2% max risk per trade on ₹500 capital.
   - Daily loss limit circuit breaker (Trading automatically stops if loss reaches limit).
   - Max 3 trades per day to eliminate emotional over-trading.
6. **Future-Proof Modular Broker Architecture:**
   - Plug-and-play template for Angel One SmartAPI, DhanHQ, or Shoonya when you obtain your PAN card in the future.
7. **Security First (GitHub Safe 🔒):**
   - All credentials and `.env` files are strictly excluded by `.gitignore`.

---

## 📁 Project Structure

```text
ai-trading-bot/
├── config.py              # Configuration & settings (Capital, Risk, Tickers, Toggles)
├── data_feed.py           # Real-time and historical candlestick fetcher (NSE)
├── indicators.py          # VWAP, EMA (20/50), RSI, ATR calculation
├── patterns.py            # Candlestick pattern detection (Hammer, Engulfing, Doji)
├── strategy.py            # Support/Resistance + Multi-Timeframe (MTF) confluence engine
├── risk_manager.py        # Position sizing & daily loss circuit breaker
├── paper_broker.py        # Virtual broker with Trailing Stop Loss (TSL) & P&L
├── live_broker_template.py# Plug-and-play template for Angel One / Dhan / Shoonya
├── telegram_notifier.py   # Free real-time Telegram alerts integration
├── backtester.py          # Historical strategy backtester & report card generator
├── bot.py                 # Main live scanning & execution loop
├── requirements.txt       # Dependencies
├── .env.example           # Secrets template (Safe for GitHub)
├── .gitignore             # Excludes .env, journals, and cache from Git
└── push_to_github.bat     # Windows one-click GitHub push helper
```

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Settings & Telegram Alerts (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
To enable free Telegram notifications:
1. Message `@BotFather` on Telegram to create a bot and copy the `TOKEN`.
2. Message `@userinfobot` to get your `CHAT_ID`.
3. Paste both into `.env`.

### 3. Run the Bot
* **Single Scan:**
  ```bash
  python bot.py
  ```
* **Continuous Live Market Monitoring (Every 60s):**
  ```bash
  python bot.py --monitor
  ```

### 4. Run Historical Backtest
Evaluate strategy performance on any stock:
```bash
python backtester.py --symbol TATASTEEL.NS --period 60d --interval 15m
```

---

## 🛡️ Git & GitHub Safety
Your `.env` file containing any sensitive data is ignored by `.gitignore`. You can safely push this entire repository to GitHub without exposing any private data.

---

## ⚠️ Disclaimer
*Trading in financial markets involves substantial risk of loss. This software is created for educational and paper-trading purposes. Always backtest and understand risk parameters before trading with real capital.*
