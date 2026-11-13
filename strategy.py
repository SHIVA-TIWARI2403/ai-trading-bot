import pandas as pd
import numpy as np
from indicators import Indicators
from patterns import CandlestickPatterns
from config import Config

class StrategyEngine:
    """
    AI & Rule-based Strategy:
    1. Identifies dynamic Support and Resistance zones.
    2. Evaluates Candlestick Confirmation.
    3. Confluence with VWAP, 20 EMA, and RSI.
    4. Calculates Entry, Stop Loss (SL), and Target with 1:2 RRR.
    """

    @staticmethod
    def find_support_resistance(df: pd.DataFrame, window: int = 15) -> tuple:
        """
        Calculates local support and resistance levels from swing highs and lows.
        """
        recent_df = df.tail(60)
        swing_lows = recent_df['Low'].rolling(window=window, center=True).min().dropna()
        swing_highs = recent_df['High'].rolling(window=window, center=True).max().dropna()

        current_price = df['Close'].iloc[-1]

        # Closest support below current price
        supports = swing_lows[swing_lows < current_price]
        nearest_support = supports.iloc[-1] if not supports.empty else df['Low'].tail(30).min()

        # Closest resistance above current price
        resistances = swing_highs[swing_highs > current_price]
        nearest_resistance = resistances.iloc[-1] if not resistances.empty else df['High'].tail(30).max()

        return float(nearest_support), float(nearest_resistance)

    @classmethod
    def analyze_setup(cls, df: pd.DataFrame, symbol: str, df_macro: pd.DataFrame = None) -> dict:
        """
        Performs full technical scan on the symbol with Multi-Timeframe (MTF) confluence.
        Returns trade recommendation and risk parameters.
        """
        if len(df) < 50:
            return {"signal": "HOLD", "reason": "Insufficient historical candles"}

        # 0. Multi-Timeframe (MTF) Macro Trend Analysis (15-Minute EMA 50)
        macro_trend = "NEUTRAL"
        if Config.ENABLE_MTF and df_macro is not None and len(df_macro) >= 50:
            df_macro_ema = Indicators.add_ema(df_macro.copy(), [50])
            macro_close = df_macro_ema['Close'].iloc[-1]
            macro_ema50 = df_macro_ema['EMA_50'].iloc[-1]
            if macro_close > macro_ema50:
                macro_trend = "BULLISH"
            elif macro_close < macro_ema50:
                macro_trend = "BEARISH"

        # 1. Apply Technical Indicators (5-Minute execution timeframe)
        df = Indicators.apply_all(df)
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        current_price = float(curr['Close'])

        # 2. Support / Resistance
        support, resistance = cls.find_support_resistance(df)

        # 3. Candlestick Pattern
        pattern_data = CandlestickPatterns.detect_latest(df)
        pattern = pattern_data['pattern']
        sentiment = pattern_data['sentiment']

        # 4. Proximity to S/R (within 0.8% threshold)
        dist_to_support_pct = (current_price - support) / current_price * 100
        dist_to_resistance_pct = (resistance - current_price) / current_price * 100

        # Indicators Values
        ema20 = curr['EMA_20']
        ema50 = curr['EMA_50']
        vwap = curr['VWAP']
        rsi = curr['RSI']
        atr = curr['ATR'] if not np.isnan(curr['ATR']) else (current_price * 0.005)

        signal = "HOLD"
        reason = "No clear high-probability confluence"
        entry_price = current_price
        stop_loss = 0.0
        target = 0.0

        # ==========================================
        # BULLISH LONG SETUP (BUY)
        # ==========================================
        # Near support + Bullish Pattern / Uptrend + VWAP/EMA support
        is_near_support = (dist_to_support_pct >= 0) and (dist_to_support_pct <= 0.8)
        is_bullish_trend = (current_price > vwap) and (current_price >= ema20)
        is_healthy_rsi = (rsi > 40) and (rsi < 68)

        if (is_near_support or sentiment == "BULLISH") and is_bullish_trend and is_healthy_rsi:
            # MTF Filter: Do NOT buy if higher timeframe (15m) is Bearish!
            if Config.ENABLE_MTF and macro_trend == "BEARISH":
                signal = "HOLD"
                reason = f"Filtered by MTF: 15m Macro Trend is BEARISH (Below 15m EMA 50)"
            else:
                signal = "BUY"
                candle_low = min(curr['Low'], prev['Low'])
                stop_loss = round(min(support, candle_low) - (0.2 * atr), 2)

                risk_per_share = entry_price - stop_loss
                if risk_per_share <= 0:
                    risk_per_share = round(0.005 * entry_price, 2)
                    stop_loss = round(entry_price - risk_per_share, 2)

                target = round(entry_price + (risk_per_share * Config.RISK_REWARD_RATIO), 2)
                reason = f"Bullish bounce near Support (Rs.{support:.2f}) | {pattern or 'Trend'} | 15m Trend: {macro_trend}"

        # ==========================================
        # BEARISH SHORT SETUP (SELL)
        # ==========================================
        # Near resistance + Bearish Pattern / Downtrend + Below VWAP/EMA
        is_near_resistance = (dist_to_resistance_pct >= 0) and (dist_to_resistance_pct <= 0.8)
        is_bearish_trend = (current_price < vwap) and (current_price <= ema20)
        is_weak_rsi = (rsi < 60) and (rsi > 30)

        if (is_near_resistance or sentiment == "BEARISH") and is_bearish_trend and is_weak_rsi:
            # MTF Filter: Do NOT short if higher timeframe (15m) is Bullish!
            if Config.ENABLE_MTF and macro_trend == "BULLISH":
                signal = "HOLD"
                reason = f"Filtered by MTF: 15m Macro Trend is BULLISH (Above 15m EMA 50)"
            else:
                signal = "SELL"
                candle_high = max(curr['High'], prev['High'])
                stop_loss = round(max(resistance, candle_high) + (0.2 * atr), 2)

                risk_per_share = stop_loss - entry_price
                if risk_per_share <= 0:
                    risk_per_share = round(0.005 * entry_price, 2)
                    stop_loss = round(entry_price + risk_per_share, 2)

                target = round(entry_price - (risk_per_share * Config.RISK_REWARD_RATIO), 2)
                reason = f"Bearish rejection near Resistance (Rs.{resistance:.2f}) | {pattern or 'Downtrend'} | 15m Trend: {macro_trend}"

        return {
            "symbol": symbol,
            "current_price": current_price,
            "signal": signal,
            "reason": reason,
            "support": support,
            "resistance": resistance,
            "pattern": pattern,
            "macro_trend": macro_trend,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "target": target,
            "vwap": round(vwap, 2),
            "rsi": round(rsi, 2)
        }
