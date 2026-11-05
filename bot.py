import sys
import os
import time
import argparse
from datetime import datetime

# Fix Windows console encoding for UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from config import Config
from data_feed import DataFeed
from strategy import StrategyEngine
from risk_manager import RiskManager
from paper_broker import PaperBroker

def format_row(values, widths):
    row = ""
    for v, w in zip(values, widths):
        row += str(v).ljust(w)[:w] + " "
    return row

def run_trading_bot(continuous: bool = False, delay_seconds: int = 60):
    print("=" * 75)
    print("[AI] INTRADAY TRADING AGENT (NSE / CASH SEGMENT)")
    print(f"Mode: {Config.TRADING_MODE} | Initial Capital: Rs.{Config.INITIAL_CAPITAL:.2f} | Max Daily Loss: Rs.{Config.MAX_DAILY_LOSS:.2f}")
    print("=" * 75)

    risk_manager = RiskManager(initial_capital=Config.INITIAL_CAPITAL)
    paper_broker = PaperBroker(initial_capital=Config.INITIAL_CAPITAL)

    iteration = 1
    while True:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[SCAN #{iteration}] Scanning Watchlist at {now_str}...")

        # 1. Check if trading allowed
        allowed, reason = risk_manager.check_trade_allowed()
        if not allowed:
            print(f"[ALERT] {reason}")
            if not continuous:
                break
            time.sleep(delay_seconds)
            continue

        headers = ["Symbol", "LTP", "Supp", "Resis", "VWAP", "RSI", "Pattern", "Signal"]
        widths = [14, 9, 9, 9, 9, 7, 18, 8]
        print("-" * 75)
        print(format_row(headers, widths))
        print("-" * 75)

        market_prices = {}

        for symbol in Config.WATCHLIST:
            df = DataFeed.get_intraday_data(symbol, interval=Config.TIMEFRAME)
            setup = StrategyEngine.analyze_setup(df, symbol)

            ltp = setup['current_price']
            market_prices[symbol] = ltp
            supp = f"{setup['support']:.1f}" if setup['support'] else "-"
            res = f"{setup['resistance']:.1f}" if setup['resistance'] else "-"
            vwap = f"{setup['vwap']:.1f}"
            rsi = f"{setup['rsi']:.1f}"
            pat = setup['pattern'] or "None"
            sig = setup['signal']

            row_data = [symbol.replace('.NS', ''), f"Rs.{ltp:.2f}", supp, res, vwap, rsi, pat, sig]
            print(format_row(row_data, widths))

            # Execute trade if Signal detected and no open trade on this symbol
            if sig in ["BUY", "SELL"] and symbol not in paper_broker.open_positions:
                can_trade, why_not = risk_manager.check_trade_allowed()
                if can_trade:
                    qty, risk = risk_manager.calculate_position_size(setup['entry_price'], setup['stop_loss'])
                    if qty > 0:
                        paper_broker.place_order(
                            symbol=symbol,
                            side=sig,
                            qty=qty,
                            entry_price=setup['entry_price'],
                            sl=setup['stop_loss'],
                            target=setup['target'],
                            reason=setup['reason']
                        )

        # 2. Update and check active positions
        closed_trades = paper_broker.update_positions(market_prices)
        for trade in closed_trades:
            risk_manager.record_trade_result(trade['pnl'])
            tag = "[PROFIT]" if trade['pnl'] >= 0 else "[LOSS]"
            print(f"\n{tag} TRADE CLOSED: {trade['symbol']} | Result: Rs.{trade['pnl']} ({trade['return_pct']}%) | Reason: {trade['reason']}")

        # 3. Portfolio Summary
        summary = paper_broker.get_portfolio_summary()
        print("-" * 75)
        print(f"[PORTFOLIO] Capital: Rs.{summary['current_capital']:.2f} | Open Positions: {summary['open_positions_count']} | Today's PnL: Rs.{risk_manager.daily_pnl:+.2f}")
        print("=" * 75)

        if not continuous:
            print("\n[OK] Single scan complete. Run with --monitor for live continuous scanning.")
            break

        iteration += 1
        time.sleep(delay_seconds)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Intraday Trading Bot")
    parser.add_argument("--monitor", action="store_true", help="Run continuously every 60 seconds")
    parser.add_argument("--delay", type=int, default=60, help="Delay between scans in seconds")
    args = parser.parse_args()

    run_trading_bot(continuous=args.monitor, delay_seconds=args.delay)
