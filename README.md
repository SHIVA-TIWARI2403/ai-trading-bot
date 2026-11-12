# Intraday Trading Screener & Paper Trading Engine

A Python-based rule-based trading scanner and paper execution engine designed for Indian equities (NSE). Implements technical analysis indicators, dynamic support/resistance identification, candlestick pattern detection, and risk management rules.

---

## Architecture & Features

### 1. Technical Analysis & Confluence Engine
- **Dynamic Support & Resistance:** Identifies local swing highs and swing lows using rolling window clustering.
- **Indicators:** Volume-Weighted Average Price (VWAP), 20 & 50 Exponential Moving Averages (EMA), and Relative Strength Index (RSI).
- **Pattern Recognition:** Algorithmic identification of key reversal patterns (Hammer, Shooting Star, Bullish/Bearish Engulfing, Doji).
- **Confluence Check:** Confirms trade entries only when multiple conditions align (e.g. price near support + bullish candlestick + RSI oversold recovery).

### 2. Risk Management
- **Position Sizing:** Caps risk per trade to 1-2% of total simulated capital.
- **Strict Risk-to-Reward:** Enforces a minimum 1:2 RRR before considering a valid setup.
- **Circuit Breakers:** Daily drawdown limit that pauses all new trade signals once hit.
- **Over-trading Prevention:** Maximum cap on daily executed orders.

### 3. Paper Trading Simulator
- Simulates market orders with realistic entry/exit slippage assumptions.
- Tracks real-time P&L, stop-loss triggers, and target completions.
- Appends closed trade details to `trades_journal.csv` for post-session review.

---

## Project Structure

```text
ai-trading-bot/
├── config.py              # User settings (capital, risk percentage, watchlist)
├── data_feed.py           # Candlestick fetcher for NSE symbols
├── indicators.py          # VWAP, EMA (20/50), RSI calculation functions
├── patterns.py            # Candlestick pattern detection rules
├── strategy.py            # Support/Resistance + confluence decision engine
├── risk_manager.py        # Position sizing and daily loss limiters
├── paper_broker.py        # Paper trading execution & order state machine
├── live_broker_template.py# Broker interface adapter (Shoonya / Dhan / Angel One)
├── bot.py                 # Main event loop and scanner
├── requirements.txt       # Dependencies
└── .env.example           # Environment template
```

---

## Quickstart

### Prerequisites
Python 3.10 or higher.

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env

# 3. Run scanner in paper trading mode
python bot.py
```

---

## Disclaimer

This software is for research, backtesting, and paper trading purposes only. It is not financial advice. Past performance in simulated environments does not guarantee future results in live market conditions.
