"""
LIVE BROKER INTEGRATION TEMPLATE (For Angel One SmartAPI / Dhan / Shoonya)

When you receive your PAN Card and open a Demat account in the future:
1. Choose a free API broker (Angel One, Dhan, or Shoonya).
2. Generate your API Key & Secret from the broker's developer portal.
3. Put those keys into your local .env file.
4. Set TRADING_MODE=LIVE in .env.
"""

from config import Config

class LiveBroker:
    def __init__(self):
        self.api_key = Config.BROKER_API_KEY
        self.client_code = Config.BROKER_CLIENT_CODE
        self.connected = False
        self._authenticate()

    def _authenticate(self):
        """
        Connects to broker API (e.g. SmartAPI, DhanHQ, or Shoonya pyNoren).
        """
        if not self.api_key or self.api_key == "your_api_key_here":
            print("[LiveBroker] Notice: No API credentials found in .env. Running in Safe Sandbox mode.")
            return

        print(f"[LiveBroker] Connecting to {Config.BROKER_CHOICE} for client {self.client_code}...")
        # Example for Angel One SmartAPI:
        # from SmartApi import SmartConnect
        # self.smart_api = SmartConnect(api_key=self.api_key)
        # data = self.smart_api.generateSession(self.client_code, Config.BROKER_PIN)
        # self.connected = True
        # print("[LiveBroker] Successfully authenticated!")

    def place_order(self, symbol: str, side: str, qty: int, entry_price: float, sl: float, target: float, reason: str):
        """
        Executes live order on exchange via broker API.
        """
        print(f"[LIVE BROKER READY] Place {side} {qty} shares of {symbol} (Target: {target}, SL: {sl})")
        # In live mode:
        # order_params = {
        #     "variety": "NORMAL",
        #     "tradingsymbol": symbol.replace('.NS', '-EQ'),
        #     "symboltoken": "3045",
        #     "transactiontype": side,
        #     "exchange": "NSE",
        #     "ordertype": "MARKET",
        #     "producttype": "INTRADAY",
        #     "duration": "DAY",
        #     "quantity": str(qty)
        # }
        # order_id = self.smart_api.placeOrder(order_params)
        # return order_id
