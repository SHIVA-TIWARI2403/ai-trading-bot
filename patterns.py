import pandas as pd

class CandlestickPatterns:
    """
    Detects high-probability candlestick patterns on intraday charts:
    - Hammer (Bullish Reversal at support)
    - Shooting Star (Bearish Reversal at resistance)
    - Bullish Engulfing (Strong institutional buying)
    - Bearish Engulfing (Strong institutional selling)
    - Doji (Market Indecision / potential inflection)
    """

    @staticmethod
    def is_hammer(open_p, high_p, low_p, close_p) -> bool:
        body = abs(close_p - open_p)
        candle_range = high_p - low_p
        lower_wick = min(open_p, close_p) - low_p
        upper_wick = high_p - max(open_p, close_p)

        if candle_range == 0:
            return False

        # Lower wick at least 2x the body, small upper wick
        return (lower_wick >= 2.0 * body) and (upper_wick <= 0.3 * candle_range) and (body > 0)

    @staticmethod
    def is_shooting_star(open_p, high_p, low_p, close_p) -> bool:
        body = abs(close_p - open_p)
        candle_range = high_p - low_p
        upper_wick = high_p - max(open_p, close_p)
        lower_wick = min(open_p, close_p) - low_p

        if candle_range == 0:
            return False

        # Upper wick at least 2x the body, small lower wick
        return (upper_wick >= 2.0 * body) and (lower_wick <= 0.3 * candle_range) and (body > 0)

    @staticmethod
    def is_bullish_engulfing(prev_open, prev_close, curr_open, curr_close) -> bool:
        prev_is_red = prev_close < prev_open
        curr_is_green = curr_close > curr_open
        engulfs = (curr_open <= prev_close) and (curr_close >= prev_open)
        return prev_is_red and curr_is_green and engulfs

    @staticmethod
    def is_bearish_engulfing(prev_open, prev_close, curr_open, curr_close) -> bool:
        prev_is_green = prev_close > prev_open
        curr_is_red = curr_close < curr_open
        engulfs = (curr_open >= prev_close) and (curr_close <= prev_open)
        return prev_is_green and curr_is_red and engulfs

    @staticmethod
    def is_doji(open_p, high_p, low_p, close_p) -> bool:
        body = abs(close_p - open_p)
        candle_range = high_p - low_p
        if candle_range == 0:
            return False
        return (body / candle_range) < 0.1

    @classmethod
    def detect_latest(cls, df: pd.DataFrame) -> dict:
        """
        Inspects the last 2 candles in the DataFrame.
        """
        if len(df) < 2:
            return {"pattern": None, "sentiment": "NEUTRAL"}

        c = df.iloc[-1]
        p = df.iloc[-2]

        if cls.is_hammer(c['Open'], c['High'], c['Low'], c['Close']):
            return {"pattern": "HAMMER", "sentiment": "BULLISH"}

        if cls.is_shooting_star(c['Open'], c['High'], c['Low'], c['Close']):
            return {"pattern": "SHOOTING_STAR", "sentiment": "BEARISH"}

        if cls.is_bullish_engulfing(p['Open'], p['Close'], c['Open'], c['Close']):
            return {"pattern": "BULLISH_ENGULFING", "sentiment": "BULLISH"}

        if cls.is_bearish_engulfing(p['Open'], p['Close'], c['Open'], c['Close']):
            return {"pattern": "BEARISH_ENGULFING", "sentiment": "BEARISH"}

        if cls.is_doji(c['Open'], c['High'], c['Low'], c['Close']):
            return {"pattern": "DOJI", "sentiment": "NEUTRAL"}

        return {"pattern": None, "sentiment": "NEUTRAL"}
