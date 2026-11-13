import sys
import os
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# Console encoding
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
from backtester import BacktestEngine

risk_manager = RiskManager(initial_capital=Config.INITIAL_CAPITAL)
paper_broker = PaperBroker(initial_capital=Config.INITIAL_CAPITAL)

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Intraday Trading Engine | Live Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #0b0e14; color: #e2e8f0; }
        .font-mono { font-family: 'JetBrains Mono', monospace; }
        .glow-green { box-shadow: 0 0 15px rgba(34, 197, 94, 0.2); }
        .glow-red { box-shadow: 0 0 15px rgba(239, 68, 68, 0.2); }
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">
    <!-- Header -->
    <header class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center pb-6 border-b border-gray-800 gap-4">
        <div>
            <div class="flex items-center gap-3">
                <span class="inline-block w-3 h-3 rounded-full bg-emerald-500 animate-pulse"></span>
                <h1 class="text-2xl md:text-3xl font-bold tracking-tight text-white flex items-center gap-2">
                    AI INTRADAY TRADING ENGINE
                </h1>
                <span class="text-xs bg-emerald-950 text-emerald-400 border border-emerald-800 px-2.5 py-0.5 rounded-full font-mono">NSE / CASH</span>
                <span class="text-xs bg-blue-950 text-blue-400 border border-blue-800 px-2.5 py-0.5 rounded-full font-mono">PAPER MODE</span>
            </div>
            <p class="text-sm text-gray-400 mt-1">Multi-Timeframe Analysis (15m + 5m) • Dynamic Trailing SL • 2% Capital Preservation</p>
        </div>
        <div class="flex items-center gap-3">
            <button onclick="fetchScanData()" id="refreshBtn" class="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-all shadow-lg shadow-indigo-600/30">
                <svg id="refreshIcon" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                Scan Market
            </button>
            <span id="lastUpdated" class="text-xs text-gray-500 font-mono">Updating...</span>
        </div>
    </header>

    <!-- Main Container -->
    <main class="max-w-7xl mx-auto mt-6 space-y-6">
        <!-- Top Metrics Cards -->
        <section class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="bg-gray-900/60 border border-gray-800/80 rounded-xl p-4">
                <p class="text-xs font-medium text-gray-400 uppercase tracking-wider">Virtual Capital</p>
                <p class="text-2xl font-bold font-mono text-white mt-1" id="statCapital">Rs. 500.00</p>
                <p class="text-xs text-gray-500 mt-1">5x Margin = Rs. 2,500 Buying Power</p>
            </div>
            <div class="bg-gray-900/60 border border-gray-800/80 rounded-xl p-4">
                <p class="text-xs font-medium text-gray-400 uppercase tracking-wider">Today's P&L</p>
                <p class="text-2xl font-bold font-mono text-emerald-400 mt-1" id="statPnL">+Rs. 0.00</p>
                <p class="text-xs text-gray-500 mt-1">Circuit Breaker at -Rs. 20.00</p>
            </div>
            <div class="bg-gray-900/60 border border-gray-800/80 rounded-xl p-4">
                <p class="text-xs font-medium text-gray-400 uppercase tracking-wider">Open Positions</p>
                <p class="text-2xl font-bold font-mono text-indigo-400 mt-1" id="statOpenPositions">0</p>
                <p class="text-xs text-gray-500 mt-1">Max 3 Trades / Day</p>
            </div>
            <div class="bg-gray-900/60 border border-gray-800/80 rounded-xl p-4">
                <p class="text-xs font-medium text-gray-400 uppercase tracking-wider">Risk / Reward System</p>
                <p class="text-2xl font-bold font-mono text-amber-400 mt-1">1 : 2.0</p>
                <p class="text-xs text-gray-500 mt-1">Trailing SL: Active (Cost-to-Cost)</p>
            </div>
        </section>

        <!-- Live Watchlist & Signal Screener Table -->
        <section class="bg-gray-900/60 border border-gray-800/80 rounded-xl overflow-hidden">
            <div class="px-5 py-4 border-b border-gray-800 flex justify-between items-center bg-gray-900/80">
                <div class="flex items-center gap-2">
                    <span class="text-base font-semibold text-white">NSE Watchlist Screener</span>
                    <span class="text-xs bg-gray-800 text-gray-300 px-2 py-0.5 rounded">Real-Time</span>
                </div>
                <div class="flex items-center gap-2 text-xs text-gray-400">
                    <span class="w-2 h-2 rounded-full bg-emerald-400 inline-block"></span> 15m MTF Trend Confluence
                </div>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-sm">
                    <thead class="bg-gray-950 text-gray-400 text-xs uppercase font-mono border-b border-gray-800">
                        <tr>
                            <th class="px-5 py-3">Symbol</th>
                            <th class="px-4 py-3">Price (LTP)</th>
                            <th class="px-4 py-3">Support</th>
                            <th class="px-4 py-3">Resistance</th>
                            <th class="px-4 py-3">VWAP</th>
                            <th class="px-4 py-3">RSI (14)</th>
                            <th class="px-4 py-3">15m Trend</th>
                            <th class="px-4 py-3">Pattern</th>
                            <th class="px-5 py-3 text-right">AI Signal</th>
                        </tr>
                    </thead>
                    <tbody id="screenerBody" class="divide-y divide-gray-800 font-mono text-xs">
                        <tr>
                            <td colspan="9" class="px-5 py-8 text-center text-gray-500">
                                Scanning market data...
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </section>

        <!-- Active Positions & Backtest Section -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Active Positions -->
            <section class="bg-gray-900/60 border border-gray-800/80 rounded-xl p-5">
                <h2 class="text-base font-semibold text-white mb-3 flex items-center justify-between">
                    <span>Active Virtual Trades</span>
                    <span class="text-xs font-normal text-gray-400">Auto-trailing stop loss enabled</span>
                </h2>
                <div id="activePositionsList" class="space-y-3">
                    <p class="text-xs text-gray-500 py-4 text-center">No active positions open right now.</p>
                </div>
            </section>

            <!-- Quick Historical Backtester -->
            <section class="bg-gray-900/60 border border-gray-800/80 rounded-xl p-5">
                <h2 class="text-base font-semibold text-white mb-3">Historical Strategy Backtest</h2>
                <div class="flex gap-2 mb-4">
                    <select id="backtestSymbol" class="bg-gray-950 border border-gray-800 text-white rounded-lg px-3 py-2 text-sm flex-1 font-mono">
                        <option value="TATASTEEL.NS">TATASTEEL.NS</option>
                        <option value="RELIANCE.NS">RELIANCE.NS</option>
                        <option value="SBIN.NS">SBIN.NS</option>
                        <option value="PNB.NS">PNB.NS</option>
                        <option value="IOC.NS">IOC.NS</option>
                        <option value="INFY.NS">INFY.NS</option>
                    </select>
                    <button onclick="runBacktest()" id="btnBacktest" class="bg-gray-800 hover:bg-gray-700 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-all">
                        Run Test (60d)
                    </button>
                </div>
                <div id="backtestResults" class="hidden bg-gray-950 border border-gray-800 rounded-lg p-4 font-mono text-xs space-y-2">
                    <!-- Results dynamically loaded here -->
                </div>
            </section>
        </div>
    </main>

    <!-- Footer -->
    <footer class="max-w-7xl mx-auto mt-10 pt-6 border-t border-gray-800/60 text-center text-xs text-gray-500">
        AI Intraday Trading Bot • Built for Educational & Portfolio Showcase • Open-source on <a href="https://github.com/SHIVA-TIWARI2403/ai-trading-bot" target="_blank" class="text-indigo-400 hover:underline">GitHub</a>
    </footer>

    <script>
        async function fetchScanData() {
            const btn = document.getElementById('refreshBtn');
            const icon = document.getElementById('refreshIcon');
            icon.classList.add('animate-spin');

            try {
                const res = await fetch('/api/scan');
                const data = await res.json();
                
                // Update top stats
                document.getElementById('statCapital').innerText = 'Rs. ' + data.capital.toFixed(2);
                const pnlEl = document.getElementById('statPnL');
                pnlEl.innerText = (data.daily_pnl >= 0 ? '+Rs. ' : '-Rs. ') + Math.abs(data.daily_pnl).toFixed(2);
                pnlEl.className = 'text-2xl font-bold font-mono mt-1 ' + (data.daily_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400');
                document.getElementById('statOpenPositions').innerText = data.open_positions_count;
                document.getElementById('lastUpdated').innerText = 'Updated: ' + new Date().toLocaleTimeString();

                // Populate Table
                const tbody = document.getElementById('screenerBody');
                tbody.innerHTML = '';
                
                data.watchlist.forEach(row => {
                    const tr = document.createElement('tr');
                    tr.className = 'hover:bg-gray-800/40 transition-colors';

                    let sigBadge = '<span class="px-2 py-0.5 rounded text-gray-400 bg-gray-800">HOLD</span>';
                    if (row.signal === 'BUY') {
                        sigBadge = '<span class="px-2.5 py-1 rounded bg-emerald-950 text-emerald-400 border border-emerald-700 font-bold glow-green">BUY</span>';
                    } else if (row.signal === 'SELL') {
                        sigBadge = '<span class="px-2.5 py-1 rounded bg-rose-950 text-rose-400 border border-rose-700 font-bold glow-red">SELL</span>';
                    }

                    const trendColor = row.macro_trend === 'BULLISH' ? 'text-emerald-400' : (row.macro_trend === 'BEARISH' ? 'text-rose-400' : 'text-gray-400');

                    tr.innerHTML = `
                        <td class="px-5 py-3.5 font-bold text-white flex items-center gap-1.5">
                            ${row.symbol.replace('.NS', '')}
                        </td>
                        <td class="px-4 py-3.5 text-white font-semibold">Rs. ${row.price.toFixed(2)}</td>
                        <td class="px-4 py-3.5 text-gray-400">Rs. ${row.support ? row.support.toFixed(1) : '-'}</td>
                        <td class="px-4 py-3.5 text-gray-400">Rs. ${row.resistance ? row.resistance.toFixed(1) : '-'}</td>
                        <td class="px-4 py-3.5 text-gray-400">Rs. ${row.vwap.toFixed(1)}</td>
                        <td class="px-4 py-3.5 text-gray-400">${row.rsi.toFixed(1)}</td>
                        <td class="px-4 py-3.5 font-bold ${trendColor}">${row.macro_trend}</td>
                        <td class="px-4 py-3.5 text-gray-400">${row.pattern || 'None'}</td>
                        <td class="px-5 py-3.5 text-right">${sigBadge}</td>
                    `;
                    tbody.appendChild(tr);
                });

                // Update Active Positions
                const posList = document.getElementById('activePositionsList');
                if (data.open_positions.length === 0) {
                    posList.innerHTML = '<p class="text-xs text-gray-500 py-4 text-center">No active positions open right now.</p>';
                } else {
                    posList.innerHTML = '';
                    data.open_positions.forEach(pos => {
                        const sideColor = pos.side === 'BUY' ? 'text-emerald-400' : 'text-rose-400';
                        posList.innerHTML += `
                            <div class="bg-gray-950 border border-gray-800 rounded-lg p-3.5 flex justify-between items-center text-xs font-mono">
                                <div>
                                    <span class="font-bold text-white text-sm">${pos.symbol.replace('.NS', '')}</span>
                                    <span class="ml-2 font-bold ${sideColor}">${pos.side} ${pos.qty} Shares</span>
                                    <div class="text-gray-400 mt-1">Entry: Rs. ${pos.entry_price.toFixed(2)} | Target: Rs. ${pos.target.toFixed(2)}</div>
                                </div>
                                <div class="text-right">
                                    <div class="text-amber-400 font-semibold">SL: Rs. ${pos.stop_loss.toFixed(2)}</div>
                                    <div class="text-gray-500 text-[10px] mt-0.5">🔒 Trailing Active</div>
                                </div>
                            </div>
                        `;
                    });
                }

            } catch (err) {
                console.error(err);
            } finally {
                icon.classList.remove('animate-spin');
            }
        }

        async function runBacktest() {
            const sym = document.getElementById('backtestSymbol').value;
            const btn = document.getElementById('btnBacktest');
            const resBox = document.getElementById('backtestResults');
            btn.innerText = 'Calculating...';
            btn.disabled = true;

            try {
                const res = await fetch('/api/backtest?symbol=' + encodeURIComponent(sym));
                const d = await res.json();
                resBox.classList.remove('hidden');
                resBox.innerHTML = `
                    <div class="flex justify-between border-b border-gray-800 pb-1 text-white font-semibold">
                        <span>Report for ${d.symbol.replace('.NS','')}</span>
                        <span class="${d.net_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}">${d.net_pnl >= 0 ? '+' : ''}${d.net_pnl} INR (${d.return_pct}%)</span>
                    </div>
                    <div class="grid grid-cols-2 gap-2 pt-1 text-gray-300">
                        <div>Total Trades: <span class="text-white">${d.total_trades}</span></div>
                        <div>Win Rate: <span class="text-emerald-400 font-bold">${d.win_rate}%</span></div>
                        <div>Profit Factor: <span class="text-white">${d.profit_factor}</span></div>
                        <div>Max Drawdown: <span class="text-rose-400">${d.max_drawdown_pct}%</span></div>
                    </div>
                `;
            } catch(e) {
                console.error(e);
            } finally {
                btn.innerText = 'Run Test (60d)';
                btn.disabled = false;
            }
        }

        // Auto-scan on load
        fetchScanData();
        // Auto refresh every 20 seconds
        setInterval(fetchScanData, 20000);
    </script>
</body>
</html>
"""

class TradingWebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))

        elif parsed.path == "/api/scan":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            results = []
            market_prices = {}

            for symbol in Config.WATCHLIST:
                if Config.ENABLE_MTF:
                    mtf_data = DataFeed.get_mtf_data(symbol)
                    df_5m = mtf_data['5m']
                    df_15m = mtf_data['15m']
                else:
                    df_5m = DataFeed.get_intraday_data(symbol, interval=Config.TIMEFRAME)
                    df_15m = None

                setup = StrategyEngine.analyze_setup(df_5m, symbol, df_macro=df_15m)
                market_prices[symbol] = setup['current_price']

                results.append({
                    "symbol": symbol,
                    "price": setup['current_price'],
                    "support": setup['support'],
                    "resistance": setup['resistance'],
                    "vwap": setup['vwap'],
                    "rsi": setup['rsi'],
                    "macro_trend": setup.get('macro_trend', 'NEUTRAL'),
                    "pattern": setup['pattern'],
                    "signal": setup['signal'],
                    "entry_price": setup['entry_price'],
                    "stop_loss": setup['stop_loss'],
                    "target": setup['target']
                })

                # Check if signal should open paper trade
                if setup['signal'] in ["BUY", "SELL"] and symbol not in paper_broker.open_positions:
                    allowed, _ = risk_manager.check_trade_allowed()
                    if allowed:
                        qty, risk = risk_manager.calculate_position_size(setup['entry_price'], setup['stop_loss'])
                        if qty > 0:
                            paper_broker.place_order(
                                symbol=symbol,
                                side=setup['signal'],
                                qty=qty,
                                entry_price=setup['entry_price'],
                                sl=setup['stop_loss'],
                                target=setup['target'],
                                reason=setup['reason']
                            )

            # Update active positions
            paper_broker.update_positions(market_prices)

            resp_data = {
                "capital": paper_broker.capital,
                "daily_pnl": risk_manager.daily_pnl,
                "open_positions_count": len(paper_broker.open_positions),
                "open_positions": list(paper_broker.open_positions.values()),
                "watchlist": results
            }
            self.wfile.write(json.dumps(resp_data).encode('utf-8'))

        elif parsed.path == "/api/backtest":
            query = urllib.parse.parse_qs(parsed.query)
            symbol = query.get("symbol", ["TATASTEEL.NS"])[0]

            engine = BacktestEngine(initial_capital=Config.INITIAL_CAPITAL)
            rep = engine.run_backtest(symbol, period="60d", interval="15m")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(rep).encode('utf-8'))

        else:
            self.send_response(404)
            self.end_headers()

def run_server(port=5050):
    server = HTTPServer(('127.0.0.1', port), TradingWebHandler)
    print(f"\\n[SERVER STARTED] Trading Dashboard running at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    run_server(5050)
