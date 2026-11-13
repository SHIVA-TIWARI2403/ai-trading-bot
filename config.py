import os
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

class Config:
    # Mode: 'PAPER' or 'LIVE'
    TRADING_MODE = os.getenv("TRADING_MODE", "PAPER").upper()

    # Initial Virtual Capital in INR
    INITIAL_CAPITAL = float(os.getenv("INITIAL_CAPITAL", 500.0))

    # Risk Management Settings
    RISK_PER_TRADE_PERCENT = float(os.getenv("RISK_PER_TRADE_PERCENT", 2.0))
    MAX_DAILY_LOSS = float(os.getenv("MAX_DAILY_LOSS", 20.0))
    MAX_TRADES_PER_DAY = int(os.getenv("MAX_TRADES_PER_DAY", 3))
    RISK_REWARD_RATIO = float(os.getenv("RISK_REWARD_RATIO", 2.0))
    INTRADAY_MARGIN_LEVERAGE = 5.0  # Standard 5x intraday margin in Indian equity cash

    # Watchlist: High liquidity, ideal for small capital intraday
    # Note: Using .NS for NSE stocks on Yahoo Finance
    WATCHLIST = [
        "TATASTEEL.NS",   # ~180 INR (Great for small capital)
        "RELIANCE.NS",    # India's largest market cap
        "SBIN.NS",        # Top PSU Bank
        "PNB.NS",         # ~120 INR (Great for Rs.500 budget)
        "IOC.NS",         # ~145 INR (Great for Rs.500 budget)
        "INFY.NS"         # Top IT Stock
    ]

    # Data & Strategy Settings
    TIMEFRAME = "5m"            # 5-minute intraday execution candles
    TIMEFRAME_TREND = "15m"      # 15-minute macro trend filter (MTF)
    CANDLE_COUNT = 100          # Past candles for S/R and EMA calculation

    # Upgrades Toggles
    ENABLE_TRAILING_SL = os.getenv("ENABLE_TRAILING_SL", "True").lower() in ("true", "1", "yes")
    ENABLE_MTF = os.getenv("ENABLE_MTF", "True").lower() in ("true", "1", "yes")

    # Telegram Alert Settings (Free Mobile Notifications)
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

    # Admin Security
    ADMIN_PIN = os.getenv("ADMIN_PIN", "KHUSHIEE2403")  # Secret PIN for Owner Access

    # Broker API Settings (Future Live Trading)
    BROKER_CHOICE = os.getenv("BROKER_CHOICE", "NONE")
    BROKER_API_KEY = os.getenv("BROKER_API_KEY", "")
    BROKER_API_SECRET = os.getenv("BROKER_API_SECRET", "")
    BROKER_CLIENT_CODE = os.getenv("BROKER_CLIENT_CODE", "")
    BROKER_PIN = os.getenv("BROKER_PIN", "")
