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
from telegram_notifier import TelegramNotifier

def format_row(values, widths):
    row = ""
    for v, w in zip(values, widths):
        row += str(v).ljust(w)[:w] + " "
    return row

def run_trading_bot(continuous: bool = False, delay_seconds: int = 60):
    print("=" * 80)
    print("[AI] INTRADAY TRADING AGENT (NSE / CASH SEGMENT)")
    print(f"Mode: {Config.TRADING_MODE} | Initial Capital: Rs.{Config.INITIAL_CAPITAL:.2f} | Max Daily Loss: Rs.{Config.MAX_DAILY_LOSS:.2f}")
    print(f"Trailing SL: {'ON' if Config.ENABLE_TRAILING_SL else 'OFF'} | MTF (15m Filter): {'ON' if Config.ENABLE_MTF else 'OFF'} | Telegram: {'ENABLED' if Config.TELEGRAM_BOT_TOKEN else 'OFF'}")
    print("=" * 80)

    risk_manager = RiskManager(initial_capital=Config.INITIAL_CAPITAL)
    paper_broker = PaperBroker(initial_capital=Config.INITIAL_CAPITAL)
    telegram = TelegramNotifier()

    iteration = 1
    while True:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[SCAN #{iteration}] Scanning Watchlist at {now_str}...")

        # 1. Check if trading allowed
        allowed, reason = risk_manager.check_trade_allowed()
        if not allowed:
            print(f"[ALERT] {reason}")
            telegram.send_message(f"⚠️ <b>Trading Paused:</b> {reason}")
            if not continuous:
                break
            time.sleep(delay_seconds)
            continue

        headers = ["Symbol", "LTP", "Supp", "Resis", "VWAP", "RSI", "15m Trend", "Signal"]
        widths = [13, 9, 9, 9, 9, 7, 11, 8]
        print("-" * 80)
        print(format_row(headers, widths))
        print("-" * 80)

        market_prices = {}

        for symbol in Config.WATCHLIST:
            # Multi-Timeframe data fetching
            if Config.ENABLE_MTF:
                mtf_data = DataFeed.get_mtf_data(symbol)
                df_5m = mtf_data['5m']
                df_15m = mtf_data['15m']
            else:
                df_5m = DataFeed.get_intraday_data(symbol, interval=Config.TIMEFRAME)
                df_15m = None

            setup = StrategyEngine.analyze_setup(df_5m, symbol, df_macro=df_15m)

            ltp = setup['current_price']
            market_prices[symbol] = ltp
            supp = f"{setup['support']:.1f}" if setup['support'] else "-"
            res = f"{setup['resistance']:.1f}" if setup['resistance'] else "-"
            vwap = f"{setup['vwap']:.1f}"
            rsi = f"{setup['rsi']:.1f}"
            macro = setup.get('macro_trend', 'NEUTRAL')
            sig = setup['signal']

            row_data = [symbol.replace('.NS', ''), f"Rs.{ltp:.2f}", supp, res, vwap, rsi, macro, sig]
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
                        # Instant Telegram Alerts
                        telegram.notify_signal(setup)
                        telegram.notify_order_placed(
                            symbol=symbol,
                            side=sig,
                            qty=qty,
                            entry_p=setup['entry_price'],
                            sl=setup['stop_loss'],
                            target=setup['target']
                        )

        # 2. Update and check active positions with Trailing SL
        closed_trades = paper_broker.update_positions(
            market_prices,
            trailing_callback=telegram.notify_trailing_sl
        )
        for trade in closed_trades:
            risk_manager.record_trade_result(trade['pnl'])
            tag = "[PROFIT]" if trade['pnl'] >= 0 else "[LOSS]"
            print(f"\n{tag} TRADE CLOSED: {trade['symbol']} | Result: Rs.{trade['pnl']} ({trade['return_pct']}%) | Reason: {trade['reason']}")
            telegram.notify_trade_closed(trade)

        # 3. Portfolio Summary
        summary = paper_broker.get_portfolio_summary()
        print("-" * 80)
        print(f"[PORTFOLIO] Capital: Rs.{summary['current_capital']:.2f} | Open Positions: {summary['open_positions_count']} | Today's PnL: Rs.{risk_manager.daily_pnl:+.2f}")
        print("=" * 80)

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
