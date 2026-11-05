from config import Config

class RiskManager:
    """
    Capital Protection Engine:
    1. Enforces strict 1-2% risk per trade on ₹500 capital.
    2. Daily Loss Limit Circuit Breaker (stops trading if daily loss hits threshold).
    3. Over-trading protection (max 2-3 trades per day).
    4. Intraday margin position sizing.
    """

    def __init__(self, initial_capital: float = None):
        self.capital = initial_capital if initial_capital else Config.INITIAL_CAPITAL
        self.daily_pnl = 0.0
        self.trades_taken_today = 0
        self.is_circuit_broken = False

    def check_trade_allowed(self) -> tuple[bool, str]:
        """
        Validates if bot is permitted to take a new trade.
        """
        # 1. Circuit Breaker: Max daily loss reached
        if self.daily_pnl <= -Config.MAX_DAILY_LOSS:
            self.is_circuit_broken = True
            return False, f"CIRCUIT BREAKER: Daily loss limit reached (-Rs.{abs(self.daily_pnl):.2f}). Trading paused for today."

        # 2. Over-trading check
        if self.trades_taken_today >= Config.MAX_TRADES_PER_DAY:
            return False, f"MAX TRADES: Reached maximum daily trade limit ({Config.MAX_TRADES_PER_DAY} trades). Rest for the day."

        return True, "Trading allowed"

    def calculate_position_size(self, entry_price: float, stop_loss: float) -> tuple[int, float]:
        """
        Calculates safe quantity based on 2% risk rule and intraday 5x leverage.
        Returns: (quantity, total_risk_rupees)
        """
        risk_per_trade_rupees = self.capital * (Config.RISK_PER_TRADE_PERCENT / 100.0)
        risk_per_share = abs(entry_price - stop_loss)

        if risk_per_share <= 0:
            return 0, 0.0

        # Quantity based purely on risk
        qty_by_risk = int(risk_per_trade_rupees / risk_per_share)

        # Quantity limited by intraday margin buying power
        # With 5x leverage on ₹500, total buying power = ₹2500
        max_buying_power = self.capital * Config.INTRADAY_MARGIN_LEVERAGE
        qty_by_margin = int(max_buying_power / entry_price)

        # Safe quantity is minimum of both, but at least 1 share if margin allows
        final_qty = min(qty_by_risk, qty_by_margin)
        if final_qty <= 0 and qty_by_margin >= 1:
            final_qty = 1

        total_risk = round(final_qty * risk_per_share, 2)
        return final_qty, total_risk

    def record_trade_result(self, pnl: float):
        """
        Updates daily P&L and trade counter.
        """
        self.daily_pnl += pnl
        self.capital += pnl
        self.trades_taken_today += 1
        if self.daily_pnl <= -Config.MAX_DAILY_LOSS:
            self.is_circuit_broken = True
