# AI Intraday Trading Bot (Paper & Live Ready)

A Python-based automated Intraday Trading Bot and AI Strategy Screener designed for beginners and algorithmic traders.

> [!IMPORTANT]
> **No PAN Card or Demat account needed for Paper Trading!**
> This bot fetches live 5-minute stock data from NSE/BSE and executes virtual trades with a virtual capital of ₹500 (or customized amount), allowing you to master price action and risk management risk-free.

---

## 🌟 Key Features

1. **Price Action & Technical Analysis Engine:**
   - **Support & Resistance:** Automated swing high/low clustering.
   - **Candlestick Pattern Recognition:** Hammer, Shooting Star, Bullish & Bearish Engulfing, Doji.
   - **Indicators:** Volume-Weighted Average Price (VWAP), 20 & 50 Exponential Moving Averages (EMA), Relative Strength Index (RSI).
2. **Strict Risk Management (Capital Protection):**
   - 1% to 2% Risk Rule per trade.
   - Automated Stop-Loss (SL) and Target (Minimum 1:2 Risk to Reward).
   - Maximum daily loss limit (Circuit breaker).
   - Maximum 2–3 trades per day to eliminate over-trading.
3. **Paper Trading Engine:**
   - Real-time simulation of buy/sell orders.
   - Live P&L and comprehensive trade logging to `trades_journal.csv`.
4. **Future-Proof Modular Broker Architecture:**
   - When you obtain your PAN card and Demat account, easily toggle from `PAPER` mode to `LIVE` mode (Angel One SmartAPI, Dhan, Shoonya).
5. **Security First (GitHub Safe):**
   - No credentials or API keys are ever committed to version control. Everything is safely loaded via local `.env`.

---

## 📁 Project Structure

```text
ai-trading-bot/
├── config.py              # Configuration & settings (Capital, Risk, Tickers)
├── data_feed.py           # Real-time and historical candlestick fetcher (NSE)
├── indicators.py          # VWAP, EMA (20/50), RSI calculation
├── patterns.py            # Candlestick pattern detection (Hammer, Engulfing, etc.)
├── strategy.py            # Support/Resistance + Confluence decision engine
├── risk_manager.py        # Position sizing & daily loss circuit breaker
├── paper_broker.py        # Virtual broker with realistic order execution & P&L
├── live_broker_template.py# Plug-and-play template for Angel One / Dhan / Shoonya
├── bot.py                 # Main execution loop
├── requirements.txt       # Dependencies
├── .env.example           # Secrets template (Safe for GitHub)
└── .gitignore             # Excludes .env, journals, and cache from Git
```

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
Make sure you have Python 3.10+ installed:
```bash
pip install -r requirements.txt
```

### 2. Configure Settings
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(Leave default settings for Paper Trading mode).*

### 3. Run the Bot in Paper Trading Mode
```bash
python bot.py
```

The bot will monitor the watchlist (e.g. `TATAMOTORS.NS`, `TATASTEEL.NS`, `SBIN.NS`), analyze 5-minute candles, look for high-probability setups, and manage virtual trades.

---

## 🛡️ Git & GitHub Safety

Your `.env` file containing any sensitive data is ignored by `.gitignore`. You can safely push this entire repository to GitHub without exposing any private data.

---

## ⚠️ Disclaimer
*Trading in financial markets involves substantial risk of loss. This software is created for educational and paper-trading purposes. Always backtest and understand risk parameters before trading with real capital.*
