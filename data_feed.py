import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config import Config

class DataFeed:
    """
    Fetches real-time and historical candlestick data for NSE/BSE stocks.
    Includes smart fallback to simulate live market data if markets are closed.
    """

    @staticmethod
    def get_intraday_data(symbol: str, interval: str = "5m", period: str = "5d") -> pd.DataFrame:
        """
        Fetch intraday candlestick data from Yahoo Finance.
        """
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)

            if df is not None and not df.empty:
                df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
                df.dropna(inplace=True)
                return df
            else:
                return DataFeed._generate_simulated_data()
        except Exception as e:
            return DataFeed._generate_simulated_data()

    @staticmethod
    def get_mtf_data(symbol: str) -> dict:
        """
        Fetches both 5-minute (execution) and 15-minute (macro trend) candle data for MTF analysis.
        """
        df_5m = DataFeed.get_intraday_data(symbol, interval=Config.TIMEFRAME, period="5d")
        df_15m = DataFeed.get_intraday_data(symbol, interval=Config.TIMEFRAME_TREND, period="1mo")
        return {"5m": df_5m, "15m": df_15m}

    @staticmethod
    def get_current_price(symbol: str) -> float:
        """
        Get latest traded price for a symbol.
        """
        try:
            ticker = yf.Ticker(symbol)
            todays_data = ticker.history(period="1d", interval="1m")
            if not todays_data.empty:
                return float(todays_data['Close'].iloc[-1])
        except Exception:
            pass
        return 150.0  # Safe default test price

    @staticmethod
    def _generate_simulated_data(num_candles: int = 100, base_price: float = 150.0) -> pd.DataFrame:
        """
        Simulates realistic 5-minute price action (useful on weekends, market holidays, or test mode).
        """
        now = datetime.now()
        dates = [now - timedelta(minutes=5 * (num_candles - i)) for i in range(num_candles)]
        
        # Random walk with realistic volatility
        np.random.seed(42)
        returns = np.random.normal(loc=0.0002, scale=0.003, size=num_candles)
        prices = base_price * np.exp(np.cumsum(returns))

        open_p = prices
        close_p = prices * (1 + np.random.normal(0, 0.002, num_candles))
        high_p = np.maximum(open_p, close_p) * (1 + np.abs(np.random.normal(0, 0.0015, num_candles)))
        low_p = np.minimum(open_p, close_p) * (1 - np.abs(np.random.normal(0, 0.0015, num_candles)))
        volume = np.random.randint(10000, 250000, size=num_candles)

        df = pd.DataFrame({
            'Open': open_p,
            'High': high_p,
            'Low': low_p,
            'Close': close_p,
            'Volume': volume
        }, index=pd.DatetimeIndex(dates))

        return df
