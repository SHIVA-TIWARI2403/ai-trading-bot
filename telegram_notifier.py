import requests
from config import Config

class TelegramNotifier:
    """
    Sends real-time trading notifications to your phone via Telegram Bot.
    Free, instant, and works with no paid subscriptions.
    """

    def __init__(self):
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.enabled = bool(self.bot_token and self.chat_id and self.bot_token != "your_telegram_bot_token_here")

    def send_message(self, text: str) -> bool:
        """
        Sends an HTML formatted message to Telegram.
        """
        if not self.enabled:
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }

        try:
            res = requests.post(url, json=payload, timeout=5)
            return res.status_code == 200
        except Exception as e:
            print(f"[TelegramNotifier Error] Failed to send alert: {e}")
            return False

    def notify_signal(self, setup: dict):
        """
        Notifies when a high-probability trade signal is generated.
        """
        side_emoji = "🟢 BUY" if setup['signal'] == "BUY" else "🔴 SHORT/SELL"
        msg = (
            f"<b>{side_emoji} SIGNAL DETECTED</b>\n\n"
            f"<b>Stock:</b> {setup['symbol'].replace('.NS', '')}\n"
            f"<b>Entry Price:</b> Rs.{setup['entry_price']:.2f}\n"
            f"<b>Stop Loss:</b> Rs.{setup['stop_loss']:.2f}\n"
            f"<b>Target (1:2):</b> Rs.{setup['target']:.2f}\n"
            f"<b>Macro Trend (15m):</b> {setup.get('macro_trend', 'N/A')}\n"
            f"<b>Pattern:</b> {setup.get('pattern') or 'Price Action Setup'}\n"
            f"<b>Reason:</b> {setup['reason']}"
        )
        self.send_message(msg)

    def notify_order_placed(self, symbol: str, side: str, qty: int, entry_p: float, sl: float, target: float):
        """
        Notifies when an order is executed.
        """
        tag = "🟢 [ORDER EXECUTED]" if side == "BUY" else "🔴 [SHORT EXECUTED]"
        msg = (
            f"<b>{tag}</b>\n\n"
            f"<b>Symbol:</b> {symbol.replace('.NS', '')}\n"
            f"<b>Side:</b> {side}\n"
            f"<b>Quantity:</b> {qty}\n"
            f"<b>Entry Price:</b> Rs.{entry_p:.2f}\n"
            f"<b>Stop Loss:</b> Rs.{sl:.2f}\n"
            f"<b>Target:</b> Rs.{target:.2f}"
        )
        self.send_message(msg)

    def notify_trailing_sl(self, symbol: str, old_sl: float, new_sl: float, current_p: float):
        """
        Notifies when Trailing Stop Loss is moved up to lock in profit.
        """
        msg = (
            f"<b>🔒 TRAILING STOP LOSS UPDATED</b>\n\n"
            f"<b>Stock:</b> {symbol.replace('.NS', '')}\n"
            f"<b>Current Price:</b> Rs.{current_p:.2f}\n"
            f"<b>Old SL:</b> Rs.{old_sl:.2f}\n"
            f"<b>New Locked SL:</b> Rs.{new_sl:.2f}\n"
            f"<i>Risk reduced / Profits locked in!</i>"
        )
        self.send_message(msg)

    def notify_trade_closed(self, trade: dict):
        """
        Notifies when Target or SL is hit.
        """
        is_profit = trade['pnl'] >= 0
        tag = "🏆 TARGET HIT / PROFIT" if is_profit else "🛑 STOP LOSS HIT"
        msg = (
            f"<b>{tag}</b>\n\n"
            f"<b>Stock:</b> {trade['symbol'].replace('.NS', '')}\n"
            f"<b>Exit Price:</b> Rs.{trade['exit_price']:.2f} (Entry: Rs.{trade['entry_price']:.2f})\n"
            f"<b>Net PnL:</b> Rs.{trade['pnl']:+.2f} ({trade['return_pct']}%)\n"
            f"<b>Reason:</b> {trade['reason']}"
        )
        self.send_message(msg)

    def notify_daily_summary(self, capital: float, daily_pnl: float, trades_count: int):
        """
        Daily summary at end of session.
        """
        status = "🟢 PROFITABLE DAY" if daily_pnl >= 0 else "🔴 LOSS DAY"
        msg = (
            f"<b>📊 INTRADAY SESSION SUMMARY</b>\n\n"
            f"<b>Status:</b> {status}\n"
            f"<b>Today's PnL:</b> Rs.{daily_pnl:+.2f}\n"
            f"<b>Total Capital:</b> Rs.{capital:.2f}\n"
            f"<b>Trades Taken:</b> {trades_count}"
        )
        self.send_message(msg)
