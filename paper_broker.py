import os
import csv
from datetime import datetime

class PaperBroker:
    """
    Virtual Broker simulation:
    - Tracks virtual capital and open intraday positions.
    - Monitors real-time price against Target and Stop Loss.
    - Logs every completed trade to trades_journal.csv.
    """

    def __init__(self, initial_capital: float = 500.0, journal_file: str = None):
        self.capital = initial_capital
        self.open_positions = {}  # symbol -> position dict
        if journal_file is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.journal_file = os.path.join(base_dir, "trades_journal.csv")
        else:
            self.journal_file = journal_file
        self._init_journal()

    def _init_journal(self):
        if not os.path.exists(self.journal_file):
            with open(self.journal_file, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp", "Symbol", "Side", "Quantity",
                    "EntryPrice", "ExitPrice", "StopLoss", "Target",
                    "PnL_INR", "ReturnPercent", "ExitReason"
                ])

    def place_order(self, symbol: str, side: str, qty: int, entry_price: float, sl: float, target: float, reason: str):
        """
        Executes a simulated intraday market order.
        """
        order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.open_positions[symbol] = {
            "symbol": symbol,
            "side": side,  # BUY or SELL
            "qty": qty,
            "entry_price": entry_price,
            "stop_loss": sl,
            "target": target,
            "entry_time": order_time,
            "reason": reason
        }
        print(f"\n[PAPER ORDER EXECUTED] {side} {qty} shares of {symbol} @ Rs.{entry_price:.2f} | SL: Rs.{sl:.2f} | Target: Rs.{target:.2f}")

    def update_positions(self, market_prices: dict) -> list[dict]:
        """
        Checks open positions against current market prices.
        Triggers SL or Target exit.
        """
        closed_trades = []
        symbols_to_close = []

        for symbol, pos in self.open_positions.items():
            current_price = market_prices.get(symbol)
            if not current_price:
                continue

            side = pos['side']
            entry_p = pos['entry_price']
            sl = pos['stop_loss']
            target = pos['target']
            qty = pos['qty']

            exit_reason = None
            exit_price = current_price

            if side == "BUY":
                if current_price >= target:
                    exit_reason = "TARGET_HIT"
                    exit_price = target
                elif current_price <= sl:
                    exit_reason = "STOPLOSS_HIT"
                    exit_price = sl
                pnl = (exit_price - entry_p) * qty

            elif side == "SELL":  # Short
                if current_price <= target:
                    exit_reason = "TARGET_HIT"
                    exit_price = target
                elif current_price >= sl:
                    exit_reason = "STOPLOSS_HIT"
                    exit_price = sl
                pnl = (entry_p - exit_price) * qty

            if exit_reason:
                ret_pct = ((pnl) / (entry_p * qty)) * 100
                self.capital += pnl
                symbols_to_close.append(symbol)

                # Record to Journal
                trade_record = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "symbol": symbol,
                    "side": side,
                    "qty": qty,
                    "entry_price": entry_p,
                    "exit_price": exit_price,
                    "sl": sl,
                    "target": target,
                    "pnl": round(pnl, 2),
                    "return_pct": round(ret_pct, 2),
                    "reason": exit_reason
                }
                self._save_to_journal(trade_record)
                closed_trades.append(trade_record)

        for sym in symbols_to_close:
            del self.open_positions[sym]

        return closed_trades

    def _save_to_journal(self, t: dict):
        with open(self.journal_file, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                t["timestamp"], t["symbol"], t["side"], t["qty"],
                t["entry_price"], t["exit_price"], t["sl"], t["target"],
                t["pnl"], t["return_pct"], t["reason"]
            ])

    def get_portfolio_summary(self) -> dict:
        return {
            "current_capital": round(self.capital, 2),
            "open_positions_count": len(self.open_positions),
            "open_positions": self.open_positions
        }
