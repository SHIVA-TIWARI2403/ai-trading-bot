import pandas as pd
import numpy as np

class Indicators:
    """
    Calculates technical indicators essential for Intraday Price Action:
    - EMA (20 & 50)
    - VWAP (Volume Weighted Average Price)
    - RSI (Relative Strength Index)
    - ATR (Average True Range for volatility-based SL)
    """

    @staticmethod
    def add_ema(df: pd.DataFrame, periods=[20, 50]) -> pd.DataFrame:
        for p in periods:
            df[f'EMA_{p}'] = df['Close'].ewm(span=p, adjust=False).mean()
        return df

    @staticmethod
    def add_vwap(df: pd.DataFrame) -> pd.DataFrame:
        """
        VWAP = sum(Price * Volume) / sum(Volume)
        Standard intraday benchmark for institutional buyers.
        """
        typical_price = (df['High'] + df['Low'] + df['Close']) / 3.0
        pv = typical_price * df['Volume']
        df['VWAP'] = pv.cumsum() / df['Volume'].cumsum()
        return df

    @staticmethod
    def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Relative Strength Index (RSI).
        """
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / (loss + 1e-10)
        df['RSI'] = 100 - (100 / (1 + rs))
        return df

    @staticmethod
    def add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Average True Range (ATR) to measure volatility and place dynamic Stop Losses.
        """
        high_low = df['High'] - df['Low']
        high_close = (df['High'] - df['Close'].shift()).abs()
        low_close = (df['Low'] - df['Close'].shift()).abs()
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(window=period).mean()
        return df

    @classmethod
    def apply_all(cls, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df = cls.add_ema(df, [20, 50])
        df = cls.add_vwap(df)
        df = cls.add_rsi(df)
        df = cls.add_atr(df)
        return df
