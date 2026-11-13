import sys
import warnings
import argparse
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime

warnings.filterwarnings('ignore')

# Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from config import Config
from indicators import Indicators
from patterns import CandlestickPatterns
from strategy import StrategyEngine

class BacktestEngine:
    """
    Backtesting Engine for AI Intraday Trading Bot.
    Simulates past historical data to evaluate:
    - Win Rate (%)
    - Net Profit / Loss (Rs. and %)
    - Profit Factor
    - Maximum Drawdown
    - Risk to Reward efficiency with Trailing SL
    """

    def __init__(self, initial_capital: float = 500.0, rrr: float = 2.0, trailing_sl: bool = True):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.rrr = rrr
        self.trailing_sl = trailing_sl
        self.trades = []

    def run_backtest(self, symbol: str, period: str = "60d", interval: str = "15m") -> dict:
        """
        Runs backtest on a single symbol using historical candles.
        Note: Yahoo Finance allows up to 60 days of 15m/5m intraday data.
        """
        print(f"\n[BACKTEST] Fetching historical data for {symbol} ({period}, {interval})...")
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            if df.empty or len(df) < 60:
                print(f"[BACKTEST] Insufficient data for {symbol}. Simulating backtest dataset.")
                df = self._generate_simulated_bars(num_bars=300)
            else:
                df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna().copy()
        except Exception as e:
            print(f"[BACKTEST Error] {e}. Using simulated data.")
            df = self._generate_simulated_bars(num_bars=300)

        # Apply Indicators
        df = Indicators.apply_all(df)

        in_trade = False
        active_pos = None
        peak_capital = self.capital
        max_drawdown = 0.0

        # Iterate candle by candle (starting from index 50 to allow indicators to warm up)
        for i in range(50, len(df)):
            curr_candle = df.iloc[i]
            prev_candle = df.iloc[i - 1]
            sub_df = df.iloc[:i + 1]

            current_price = float(curr_candle['Close'])
            high_price = float(curr_candle['High'])
            low_price = float(curr_candle['Low'])

            # 1. Manage Active Trade if in position
            if in_trade:
                side = active_pos['side']
                entry_p = active_pos['entry_price']
                sl = active_pos['sl']
                initial_sl = active_pos['initial_sl']
                target = active_pos['target']
                qty = active_pos['qty']
                risk_ps = active_pos['risk_per_share']

                # Trailing SL update
                if self.trailing_sl and risk_ps > 0:
                    if side == "BUY":
                        if high_price >= (entry_p + 1.5 * risk_ps) and sl < (entry_p + 0.5 * risk_ps):
                            active_pos['sl'] = round(entry_p + 0.5 * risk_ps, 2)
                        elif high_price >= (entry_p + 1.0 * risk_ps) and sl < entry_p:
                            active_pos['sl'] = round(entry_p, 2)
                    elif side == "SELL":
                        if low_price <= (entry_p - 1.5 * risk_ps) and sl > (entry_p - 0.5 * risk_ps):
                            active_pos['sl'] = round(entry_p - 0.5 * risk_ps, 2)
                        elif low_price <= (entry_p - 1.0 * risk_ps) and sl > entry_p:
                            active_pos['sl'] = round(entry_p, 2)

                sl = active_pos['sl']
                exit_price = None
                exit_reason = None

                # Check exits
                if side == "BUY":
                    if high_price >= target:
                        exit_price = target
                        exit_reason = "TARGET_HIT"
                    elif low_price <= sl:
                        exit_price = sl
                        exit_reason = "TRAILING_SL_HIT" if sl > initial_sl else "STOPLOSS_HIT"
                    pnl = (exit_price - entry_p) * qty if exit_price else 0.0

                elif side == "SELL":
                    if low_price <= target:
                        exit_price = target
                        exit_reason = "TARGET_HIT"
                    elif high_price >= sl:
                        exit_price = sl
                        exit_reason = "TRAILING_SL_HIT" if sl < initial_sl else "STOPLOSS_HIT"
                    pnl = (entry_p - exit_price) * qty if exit_price else 0.0

                if exit_reason:
                    self.capital += pnl
                    if self.capital > peak_capital:
                        peak_capital = self.capital
                    dd = ((peak_capital - self.capital) / peak_capital) * 100
                    if dd > max_drawdown:
                        max_drawdown = dd

                    self.trades.append({
                        "symbol": symbol,
                        "side": side,
                        "entry": entry_p,
                        "exit": exit_price,
                        "pnl": round(pnl, 2),
                        "reason": exit_reason,
                        "return_pct": round((pnl / (entry_p * qty)) * 100, 2)
                    })
                    in_trade = False
                    active_pos = None

            # 2. Look for new setup if not in position
            else:
                setup = StrategyEngine.analyze_setup(sub_df, symbol)
                sig = setup['signal']

                if sig in ["BUY", "SELL"]:
                    entry_p = setup['entry_price']
                    sl = setup['stop_loss']
                    target = setup['target']
                    risk_ps = abs(entry_p - sl)

                    if risk_ps > 0:
                        # Position sizing based on 2% risk rule
                        risk_amount = self.capital * (Config.RISK_PER_TRADE_PERCENT / 100.0)
                        qty = int(risk_amount / risk_ps)
                        max_margin_qty = int((self.capital * Config.INTRADAY_MARGIN_LEVERAGE) / entry_p)
                        final_qty = max(1, min(qty, max_margin_qty))

                        in_trade = True
                        active_pos = {
                            "symbol": symbol,
                            "side": sig,
                            "entry_price": entry_p,
                            "sl": sl,
                            "initial_sl": sl,
                            "target": target,
                            "risk_per_share": risk_ps,
                            "qty": final_qty
                        }

        return self._generate_report(symbol, max_drawdown)

    def _generate_report(self, symbol: str, max_dd: float) -> dict:
        total_trades = len(self.trades)
        if total_trades == 0:
            return {"symbol": symbol, "total_trades": 0, "net_pnl": 0.0, "win_rate": 0.0}

        wins = [t for t in self.trades if t['pnl'] > 0]
        losses = [t for t in self.trades if t['pnl'] <= 0]

        total_gain = sum(t['pnl'] for t in wins)
        total_loss = abs(sum(t['pnl'] for t in losses))
        profit_factor = (total_gain / total_loss) if total_loss > 0 else 9.99

        win_rate = (len(wins) / total_trades) * 100.0
        net_pnl = self.capital - self.initial_capital
        net_return_pct = (net_pnl / self.initial_capital) * 100.0

        report = {
            "symbol": symbol,
            "initial_capital": self.initial_capital,
            "final_capital": round(self.capital, 2),
            "net_pnl": round(net_pnl, 2),
            "return_pct": round(net_return_pct, 2),
            "total_trades": total_trades,
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(win_rate, 2),
            "profit_factor": round(profit_factor, 2),
            "max_drawdown_pct": round(max_dd, 2)
        }
        return report

    def _generate_simulated_bars(self, num_bars: int = 300, base_price: float = 180.0) -> pd.DataFrame:
        np.random.seed(101)
        returns = np.random.normal(0.0003, 0.004, size=num_bars)
        prices = base_price * np.exp(np.cumsum(returns))
        open_p = prices
        close_p = prices * (1 + np.random.normal(0, 0.002, num_bars))
        high_p = np.maximum(open_p, close_p) * (1 + np.abs(np.random.normal(0, 0.002, num_bars)))
        low_p = np.minimum(open_p, close_p) * (1 - np.abs(np.random.normal(0, 0.002, num_bars)))
        volume = np.random.randint(50000, 300000, size=num_bars)

        dates = pd.date_range(end=datetime.now(), periods=num_bars, freq='15min')
        return pd.DataFrame({
            'Open': open_p, 'High': high_p, 'Low': low_p, 'Close': close_p, 'Volume': volume
        }, index=dates)

def print_report_card(rep: dict):
    print("\n" + "=" * 60)
    print(f"📊 HISTORICAL STRATEGY REPORT CARD: {rep['symbol']}")
    print("=" * 60)
    print(f"Initial Capital   : Rs.{rep['initial_capital']:.2f}")
    print(f"Final Capital     : Rs.{rep['final_capital']:.2f}")
    print(f"Net P&L           : Rs.{rep['net_pnl']:+.2f} ({rep['return_pct']:+.2f}%)")
    print("-" * 60)
    print(f"Total Trades      : {rep['total_trades']}")
    print(f"Winning Trades    : {rep['wins']} 🟢")
    print(f"Losing Trades     : {rep['losses']} 🔴")
    print(f"Win Rate          : {rep['win_rate']}%")
    print(f"Profit Factor     : {rep['profit_factor']}")
    print(f"Max Drawdown      : {rep['max_drawdown_pct']}%")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Strategy Backtester")
    parser.add_argument("--symbol", type=str, default="TATASTEEL.NS", help="NSE symbol to backtest")
    parser.add_argument("--period", type=str, default="60d", help="Backtest period (e.g. 30d, 60d)")
    parser.add_argument("--interval", type=str, default="15m", help="Candle interval (5m, 15m, 1h)")
    args = parser.parse_args()

    engine = BacktestEngine(initial_capital=Config.INITIAL_CAPITAL)
    report = engine.run_backtest(args.symbol, period=args.period, interval=args.interval)
    print_report_card(report)
