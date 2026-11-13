import sys
import os
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# Windows console encoding
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

# Global In-Memory State
risk_manager = RiskManager(initial_capital=Config.INITIAL_CAPITAL)
paper_broker = PaperBroker(initial_capital=Config.INITIAL_CAPITAL)
bot_running_state = "RUNNING"  # "RUNNING" or "PAUSED"
admin_token = None

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Intraday Trading Engine & Terminal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #0b0e14; color: #e2e8f0; }
        .font-mono { font-family: 'JetBrains Mono', monospace; }
        .glow-green { box-shadow: 0 0 15px rgba(34, 197, 94, 0.25); }
        .glow-red { box-shadow: 0 0 15px rgba(239, 68, 68, 0.25); }
        .glow-indigo { box-shadow: 0 0 15px rgba(99, 102, 241, 0.25); }
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">

    <!-- Top Navigation & Header -->
    <header class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center pb-6 border-b border-gray-800 gap-4">
        <div>
            <div class="flex items-center gap-3">
                <span id="botStateDot" class="inline-block w-3 h-3 rounded-full bg-emerald-500 animate-pulse"></span>
                <h1 class="text-2xl md:text-3xl font-bold tracking-tight text-white flex items-center gap-2">
                    AI INTRADAY TRADING ENGINE
                </h1>
                <span id="badgeTradingMode" class="text-xs bg-blue-950 text-blue-400 border border-blue-800 px-2.5 py-0.5 rounded-full font-mono font-semibold">PAPER MODE</span>
                <span class="text-xs bg-emerald-950 text-emerald-400 border border-emerald-800 px-2.5 py-0.5 rounded-full font-mono">NSE CASH</span>
            </div>
            <p class="text-xs md:text-sm text-gray-400 mt-1">Multi-Timeframe Analysis (15m + 5m) • Dynamic Trailing SL • Quantitative Risk Engine</p>
        </div>
        <div class="flex items-center gap-3">
            <button onclick="fetchScanData()" id="refreshBtn" class="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 text-white text-xs md:text-sm font-semibold px-3 py-2 rounded-lg transition-all border border-gray-700">
                <svg id="refreshIcon" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                Scan Now
            </button>
            <button onclick="openAdminModal()" class="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs md:text-sm font-semibold px-4 py-2 rounded-lg transition-all shadow-lg shadow-indigo-600/30">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>
                Admin Vault
            </button>
        </div>
    </header>

    <!-- Main Container -->
    <main class="max-w-7xl mx-auto mt-6 space-y-6">

        <!-- Top Metrics Cards -->
        <section class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="bg-gray-900/60 border border-gray-800/80 rounded-xl p-4">
                <p class="text-xs font-medium text-gray-400 uppercase tracking-wider">Trading Capital</p>
                <p class="text-2xl font-bold font-mono text-white mt-1" id="statCapital">Rs. 500.00</p>
                <p class="text-xs text-gray-500 mt-1" id="statMargin">5x Margin = Rs. 2,500 Buying Power</p>
            </div>
            <div class="bg-gray-900/60 border border-gray-800/80 rounded-xl p-4">
                <p class="text-xs font-medium text-gray-400 uppercase tracking-wider">Today's P&L</p>
                <p class="text-2xl font-bold font-mono text-emerald-400 mt-1" id="statPnL">+Rs. 0.00</p>
                <p class="text-xs text-gray-500 mt-1" id="statCircuit">Circuit Breaker: -Rs. 20.00</p>
            </div>
            <div class="bg-gray-900/60 border border-gray-800/80 rounded-xl p-4">
                <p class="text-xs font-medium text-gray-400 uppercase tracking-wider">Active Trades</p>
                <p class="text-2xl font-bold font-mono text-indigo-400 mt-1" id="statOpenPositions">0</p>
                <p class="text-xs text-gray-500 mt-1">Daily Limit: Max 3 Trades</p>
            </div>
            <div class="bg-gray-900/60 border border-gray-800/80 rounded-xl p-4">
                <p class="text-xs font-medium text-gray-400 uppercase tracking-wider">Strategy Engine</p>
                <p class="text-2xl font-bold font-mono text-amber-400 mt-1">1 : 2.0 RRR</p>
                <p class="text-xs text-gray-500 mt-1">Dynamic Trailing SL Active</p>
            </div>
        </section>

        <!-- NEW FEATURE 1: UNIVERSAL STOCK SEARCH & INSTANT DEEP-DIVE -->
        <section class="bg-gray-900/60 border border-gray-800/80 rounded-xl p-5 glow-indigo">
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-3 mb-4">
                <div>
                    <h2 class="text-base font-semibold text-white flex items-center gap-2">
                        <svg class="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                        Universal Stock Search & Instant Technical Deep-Dive
                    </h2>
                    <p class="text-xs text-gray-400">Search ANY NSE stock (e.g. TCS, HDFCBANK, ITC, IRFC, ADANIENT, ZOMATO) for instant price action breakdown.</p>
                </div>
            </div>
            <div class="flex gap-2">
                <input type="text" id="searchInput" placeholder="Enter stock ticker (e.g. TCS, HDFCBANK, ITC)..." class="bg-gray-950 border border-gray-800 text-white rounded-lg px-4 py-2.5 text-sm flex-1 font-mono uppercase focus:outline-none focus:border-indigo-500">
                <button onclick="searchStock()" id="btnSearch" class="bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-all flex items-center gap-2">
                    Analyze Stock
                </button>
            </div>

            <!-- Search Result Container -->
            <div id="searchResultCard" class="hidden mt-4 bg-gray-950 border border-gray-800 rounded-xl p-5">
                <!-- Dynamically populated -->
            </div>
        </section>

        <!-- NEW FEATURE 2: HEAD-TO-HEAD STOCK COMPARISON TOOL -->
        <section class="bg-gray-900/60 border border-gray-800/80 rounded-xl p-5">
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-3 mb-4">
                <div>
                    <h2 class="text-base font-semibold text-white flex items-center gap-2">
                        <svg class="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
                        Multi-Stock Head-to-Head Comparison (Relative Strength)
                    </h2>
                    <p class="text-xs text-gray-400">Compare 2 or 3 stocks simultaneously to find which setup has the highest probability & best Risk-Reward today.</p>
                </div>
            </div>
            <div class="flex flex-col md:flex-row gap-2">
                <input type="text" id="compareInputs" value="SBIN, PNB, RELIANCE" placeholder="Comma separated tickers (e.g. SBIN, PNB, HDFCBANK)..." class="bg-gray-950 border border-gray-800 text-white rounded-lg px-4 py-2 text-sm flex-1 font-mono uppercase focus:outline-none focus:border-amber-500">
                <button onclick="compareStocks()" id="btnCompare" class="bg-amber-600 hover:bg-amber-500 text-white text-sm font-semibold px-5 py-2 rounded-lg transition-all">
                    Compare Setups
                </button>
            </div>

            <!-- Comparison Table Container -->
            <div id="compareResultsCard" class="hidden mt-4 overflow-x-auto">
                <!-- Dynamically populated -->
            </div>
        </section>

        <!-- Live Watchlist & Signal Screener Table -->
        <section class="bg-gray-900/60 border border-gray-800/80 rounded-xl overflow-hidden">
            <div class="px-5 py-4 border-b border-gray-800 flex justify-between items-center bg-gray-900/80">
                <div class="flex items-center gap-2">
                    <span class="text-base font-semibold text-white">Core Watchlist Screener</span>
                    <span class="text-xs bg-gray-800 text-gray-300 px-2 py-0.5 rounded">Auto-Scanning</span>
                </div>
                <div class="flex items-center gap-2 text-xs text-gray-400">
                    <span class="w-2 h-2 rounded-full bg-emerald-400 inline-block"></span> 15m Trend Aligned
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
                            <th class="px-4 py-3">15m Macro Trend</th>
                            <th class="px-4 py-3">Pattern</th>
                            <th class="px-5 py-3 text-right">AI Recommendation</th>
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
                    <button onclick="runBacktest()" id="btnBacktest" class="bg-gray-800 hover:bg-gray-700 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-all border border-gray-700">
                        Run Test (60d)
                    </button>
                </div>
                <div id="backtestResults" class="hidden bg-gray-950 border border-gray-800 rounded-lg p-4 font-mono text-xs space-y-2">
                    <!-- Results dynamically loaded here -->
                </div>
            </section>
        </div>
    </main>

    <!-- ADMIN MODAL (SECURE ACCESS FOR OWNER ONLY) -->
    <div id="adminModal" class="hidden fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-gray-900 border border-gray-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl relative">
            <button onclick="closeAdminModal()" class="absolute top-5 right-5 text-gray-400 hover:text-white">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>

            <!-- Step 1: PIN Authentication -->
            <div id="adminAuthSection">
                <div class="flex items-center gap-3 mb-4">
                    <div class="w-10 h-10 rounded-xl bg-indigo-950 border border-indigo-700 flex items-center justify-center text-indigo-400 font-bold">
                        🔒
                    </div>
                    <div>
                        <h3 class="text-lg font-bold text-white">Owner Admin Portal</h3>
                        <p class="text-xs text-gray-400">Enter your secret Admin PIN to manage bot execution and license settings.</p>
                    </div>
                </div>
                <div class="space-y-4 mt-6">
                    <div>
                        <label class="text-xs font-mono text-gray-400 uppercase">Secret Admin PIN</label>
                        <input type="password" id="adminPinInput" placeholder="Enter PIN..." class="w-full mt-1.5 bg-gray-950 border border-gray-800 text-white rounded-lg px-4 py-2.5 text-center text-lg font-mono tracking-widest focus:outline-none focus:border-indigo-500">
                    </div>
                    <button onclick="verifyAdminPin()" id="btnPinVerify" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2.5 rounded-lg transition-all">
                        Unlock Admin Control
                    </button>
                    <p id="adminAuthError" class="hidden text-xs text-rose-400 text-center font-mono">Incorrect PIN. Access Denied!</p>
                </div>
            </div>

            <!-- Step 2: Unlocked Admin Controls -->
            <div id="adminPanelSection" class="hidden space-y-6">
                <div class="border-b border-gray-800 pb-3 flex justify-between items-center">
                    <div>
                        <h3 class="text-lg font-bold text-white flex items-center gap-2">
                            <span>🛡️ Owner Control Center</span>
                            <span class="text-xs bg-emerald-950 text-emerald-400 border border-emerald-800 px-2 py-0.5 rounded font-mono">AUTHENTICATED</span>
                        </h3>
                        <p class="text-xs text-gray-400">Shiva Tiwari • Full Execution Authority</p>
                    </div>
                    <button onclick="lockAdmin()" class="text-xs text-gray-400 hover:text-white underline">Lock</button>
                </div>

                <!-- Bot Execution Controls -->
                <div class="space-y-2">
                    <label class="text-xs font-mono text-gray-400 uppercase">Bot Execution State</label>
                    <div class="grid grid-cols-3 gap-2">
                        <button onclick="setBotControl('RESUME')" class="bg-emerald-900/60 hover:bg-emerald-800 border border-emerald-700 text-emerald-300 font-semibold py-2 rounded-lg text-xs">
                            ▶ Resume Bot
                        </button>
                        <button onclick="setBotControl('PAUSE')" class="bg-amber-900/60 hover:bg-amber-800 border border-amber-700 text-amber-300 font-semibold py-2 rounded-lg text-xs">
                            ⏸ Pause Bot
                        </button>
                        <button onclick="setBotControl('RESET_CAPITAL')" class="bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 font-semibold py-2 rounded-lg text-xs">
                            🔄 Reset (Rs.500)
                        </button>
                    </div>
                </div>

                <!-- Risk Management Limits -->
                <div class="space-y-3">
                    <label class="text-xs font-mono text-gray-400 uppercase">Quantitative Risk Parameters</label>
                    <div class="grid grid-cols-3 gap-2">
                        <div>
                            <label class="text-[10px] text-gray-500 font-mono">Risk % / Trade</label>
                            <input type="number" id="admRiskPerTrade" value="2.0" step="0.5" class="w-full bg-gray-950 border border-gray-800 text-white rounded p-1.5 text-xs font-mono">
                        </div>
                        <div>
                            <label class="text-[10px] text-gray-500 font-mono">Max Daily Loss (Rs)</label>
                            <input type="number" id="admMaxDailyLoss" value="20.0" step="5" class="w-full bg-gray-950 border border-gray-800 text-white rounded p-1.5 text-xs font-mono">
                        </div>
                        <div>
                            <label class="text-[10px] text-gray-500 font-mono">Max Trades / Day</label>
                            <input type="number" id="admMaxTrades" value="3" class="w-full bg-gray-950 border border-gray-800 text-white rounded p-1.5 text-xs font-mono">
                        </div>
                    </div>
                </div>

                <!-- FUTURE LIVE TRADING SWITCH -->
                <div class="bg-gray-950 border border-gray-800 rounded-xl p-4 space-y-3">
                    <div class="flex justify-between items-center">
                        <div>
                            <span class="text-sm font-bold text-white flex items-center gap-1.5">
                                🚀 Live Broker License Switch
                            </span>
                            <p class="text-[11px] text-gray-400">Switch to real money when your PAN card / Demat API is ready.</p>
                        </div>
                        <select id="admTradingModeSelect" class="bg-gray-900 border border-gray-700 text-white rounded px-2.5 py-1 text-xs font-mono font-bold">
                            <option value="PAPER">PAPER MODE (Virtual)</option>
                            <option value="LIVE">LIVE BROKER TRADING</option>
                        </select>
                    </div>
                    <div class="grid grid-cols-2 gap-2 text-xs">
                        <div>
                            <label class="text-[10px] text-gray-500 font-mono">Broker Choice</label>
                            <select id="admBrokerChoice" class="w-full bg-gray-900 border border-gray-800 text-white rounded p-1.5 text-xs">
                                <option value="ANGELONE">Angel One SmartAPI (Free)</option>
                                <option value="DHAN">DhanHQ API (Free)</option>
                                <option value="SHOONYA">Shoonya Finvasia (Zero Brokerage)</option>
                            </select>
                        </div>
                        <div>
                            <label class="text-[10px] text-gray-500 font-mono">Client ID / Code</label>
                            <input type="text" id="admClientCode" placeholder="e.g. S12345" class="w-full bg-gray-900 border border-gray-800 text-white rounded p-1.5 text-xs font-mono">
                        </div>
                    </div>
                </div>

                <button onclick="saveAdminSettings()" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-2.5 rounded-lg transition-all text-xs">
                    Save & Apply Settings
                </button>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <footer class="max-w-7xl mx-auto mt-10 pt-6 border-t border-gray-800/60 text-center text-xs text-gray-500">
        AI Intraday Trading Engine • Engineered by Shiva Tiwari • Open-source on <a href="https://github.com/SHIVA-TIWARI2403/ai-trading-bot" target="_blank" class="text-indigo-400 hover:underline">GitHub</a>
    </footer>

    <script>
        let currentAuthToken = null;

        // Auto-scan on load
        fetchScanData();
        setInterval(fetchScanData, 20000);

        async function fetchScanData() {
            const icon = document.getElementById('refreshIcon');
            icon.classList.add('animate-spin');

            try {
                const res = await fetch('/api/scan');
                const data = await res.json();
                
                document.getElementById('statCapital').innerText = 'Rs. ' + data.capital.toFixed(2);
                const pnlEl = document.getElementById('statPnL');
                pnlEl.innerText = (data.daily_pnl >= 0 ? '+Rs. ' : '-Rs. ') + Math.abs(data.daily_pnl).toFixed(2);
                pnlEl.className = 'text-2xl font-bold font-mono mt-1 ' + (data.daily_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400');
                document.getElementById('statOpenPositions').innerText = data.open_positions_count;

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

        // ==========================================
        // FEATURE 1: UNIVERSAL STOCK SEARCH
        // ==========================================
        async function searchStock() {
            let symbol = document.getElementById('searchInput').value.trim();
            if (!symbol) return;
            if (!symbol.toUpperCase().endsWith('.NS')) symbol += '.NS';

            const btn = document.getElementById('btnSearch');
            const card = document.getElementById('searchResultCard');
            btn.innerText = 'Analyzing...';
            btn.disabled = true;

            try {
                const res = await fetch('/api/search?symbol=' + encodeURIComponent(symbol));
                const d = await res.json();
                card.classList.remove('hidden');

                const trendColor = d.macro_trend === 'BULLISH' ? 'text-emerald-400' : (d.macro_trend === 'BEARISH' ? 'text-rose-400' : 'text-gray-400');
                let sigTag = '<span class="px-3 py-1 rounded bg-gray-800 text-gray-300 font-bold">HOLD / WATCH</span>';
                if (d.signal === 'BUY') {
                    sigTag = '<span class="px-3 py-1 rounded bg-emerald-950 text-emerald-400 border border-emerald-600 font-bold glow-green">STRONG BUY</span>';
                } else if (d.signal === 'SELL') {
                    sigTag = '<span class="px-3 py-1 rounded bg-rose-950 text-rose-400 border border-rose-600 font-bold glow-red">STRONG SHORT</span>';
                }

                card.innerHTML = `
                    <div class="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-gray-800 pb-4 mb-4 gap-2">
                        <div>
                            <div class="flex items-center gap-3">
                                <h3 class="text-xl font-bold text-white font-mono">${d.symbol.replace('.NS', '')}</h3>
                                <span class="text-lg font-bold text-white font-mono">Rs. ${d.current_price.toFixed(2)}</span>
                                <span class="text-xs font-bold font-mono ${trendColor}">15m Trend: ${d.macro_trend}</span>
                            </div>
                            <p class="text-xs text-gray-400 mt-1">${d.reason}</p>
                        </div>
                        <div>${sigTag}</div>
                    </div>
                    <div class="grid grid-cols-2 md:grid-cols-5 gap-4 font-mono text-xs">
                        <div class="bg-gray-900/80 p-3 rounded-lg border border-gray-800">
                            <span class="text-gray-500 block">Support</span>
                            <span class="text-white font-semibold">Rs. ${d.support.toFixed(1)}</span>
                        </div>
                        <div class="bg-gray-900/80 p-3 rounded-lg border border-gray-800">
                            <span class="text-gray-500 block">Resistance</span>
                            <span class="text-white font-semibold">Rs. ${d.resistance.toFixed(1)}</span>
                        </div>
                        <div class="bg-gray-900/80 p-3 rounded-lg border border-gray-800">
                            <span class="text-gray-500 block">VWAP</span>
                            <span class="text-white font-semibold">Rs. ${d.vwap.toFixed(1)}</span>
                        </div>
                        <div class="bg-gray-900/80 p-3 rounded-lg border border-gray-800">
                            <span class="text-gray-500 block">RSI (14)</span>
                            <span class="text-white font-semibold">${d.rsi.toFixed(1)}</span>
                        </div>
                        <div class="bg-gray-900/80 p-3 rounded-lg border border-gray-800">
                            <span class="text-gray-500 block">Pattern</span>
                            <span class="text-indigo-400 font-semibold">${d.pattern || 'Consolidation'}</span>
                        </div>
                    </div>
                    ${d.signal !== 'HOLD' ? `
                    <div class="mt-4 pt-3 border-t border-gray-800/80 flex flex-wrap gap-4 text-xs font-mono">
                        <span class="text-gray-400">Execution Plan: <strong class="text-white">Entry @ Rs. ${d.entry_price.toFixed(2)}</strong></span>
                        <span class="text-amber-400 font-semibold">Stop Loss: Rs. ${d.stop_loss.toFixed(2)}</span>
                        <span class="text-emerald-400 font-semibold">Target (1:2): Rs. ${d.target.toFixed(2)}</span>
                    </div>` : ''}
                `;
            } catch(e) {
                console.error(e);
            } finally {
                btn.innerText = 'Analyze Stock';
                btn.disabled = false;
            }
        }

        // ==========================================
        // FEATURE 2: MULTI-STOCK COMPARISON TOOL
        // ==========================================
        async function compareStocks() {
            const raw = document.getElementById('compareInputs').value.trim();
            if (!raw) return;

            const btn = document.getElementById('btnCompare');
            const card = document.getElementById('compareResultsCard');
            btn.innerText = 'Comparing...';
            btn.disabled = true;

            try {
                const res = await fetch('/api/compare?symbols=' + encodeURIComponent(raw));
                const d = await res.json();
                card.classList.remove('hidden');

                let rowsHtml = '';
                d.stocks.forEach(s => {
                    const isWinner = s.symbol === d.winner_symbol;
                    const winnerTag = isWinner ? '<span class="ml-2 px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-600 font-bold text-[10px]">🏆 TOP PICK</span>' : '';
                    const trendColor = s.macro_trend === 'BULLISH' ? 'text-emerald-400' : (s.macro_trend === 'BEARISH' ? 'text-rose-400' : 'text-gray-400');
                    rowsHtml += `
                        <tr class="${isWinner ? 'bg-amber-950/20' : 'hover:bg-gray-800/30'}">
                            <td class="px-4 py-3 font-bold text-white font-mono flex items-center">
                                ${s.symbol.replace('.NS', '')} ${winnerTag}
                            </td>
                            <td class="px-4 py-3 font-mono">Rs. ${s.current_price.toFixed(2)}</td>
                            <td class="px-4 py-3 font-mono font-bold ${trendColor}">${s.macro_trend}</td>
                            <td class="px-4 py-3 font-mono">${s.rsi.toFixed(1)}</td>
                            <td class="px-4 py-3 font-mono">Rs. ${s.vwap.toFixed(1)}</td>
                            <td class="px-4 py-3 font-mono text-gray-300">${s.pattern || 'None'}</td>
                            <td class="px-4 py-3 font-mono font-semibold">${s.signal}</td>
                        </tr>
                    `;
                });

                card.innerHTML = `
                    <div class="bg-gray-950 border border-gray-800 rounded-xl overflow-hidden">
                        <div class="p-3 bg-gray-900 border-b border-gray-800 text-xs font-mono text-amber-300">
                            <strong>AI Relative Strength Verdict:</strong> ${d.verdict}
                        </div>
                        <table class="w-full text-left text-xs">
                            <thead class="bg-gray-950 text-gray-400 uppercase font-mono border-b border-gray-800">
                                <tr>
                                    <th class="px-4 py-2.5">Stock</th>
                                    <th class="px-4 py-2.5">LTP</th>
                                    <th class="px-4 py-2.5">15m Trend</th>
                                    <th class="px-4 py-2.5">RSI</th>
                                    <th class="px-4 py-2.5">VWAP</th>
                                    <th class="px-4 py-2.5">Pattern</th>
                                    <th class="px-4 py-2.5">Signal</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-gray-800">
                                ${rowsHtml}
                            </tbody>
                        </table>
                    </div>
                `;
            } catch(e) {
                console.error(e);
            } finally {
                btn.innerText = 'Compare Setups';
                btn.disabled = false;
            }
        }

        // ==========================================
        // ADMIN PANEL FUNCTIONS (SECURE)
        // ==========================================
        function openAdminModal() {
            document.getElementById('adminModal').classList.remove('hidden');
            if (currentAuthToken) {
                document.getElementById('adminAuthSection').classList.add('hidden');
                document.getElementById('adminPanelSection').classList.remove('hidden');
            } else {
                document.getElementById('adminAuthSection').classList.remove('hidden');
                document.getElementById('adminPanelSection').classList.add('hidden');
            }
        }

        function closeAdminModal() {
            document.getElementById('adminModal').classList.add('hidden');
        }

        async function verifyAdminPin() {
            const pin = document.getElementById('adminPinInput').value;
            const err = document.getElementById('adminAuthError');

            const res = await fetch('/api/admin/auth', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pin: pin })
            });
            const d = await res.json();

            if (d.success) {
                currentAuthToken = d.token;
                err.classList.add('hidden');
                document.getElementById('adminAuthSection').classList.add('hidden');
                document.getElementById('adminPanelSection').classList.remove('hidden');
            } else {
                err.classList.remove('hidden');
            }
        }

        function lockAdmin() {
            currentAuthToken = null;
            document.getElementById('adminPinInput').value = '';
            document.getElementById('adminAuthSection').classList.remove('hidden');
            document.getElementById('adminPanelSection').classList.add('hidden');
        }

        async function setBotControl(action) {
            if (!currentAuthToken) return;
            const res = await fetch('/api/admin/control', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': currentAuthToken },
                body: JSON.stringify({ action: action })
            });
            const d = await res.json();
            alert(d.message);
            fetchScanData();
        }

        async function saveAdminSettings() {
            if (!currentAuthToken) return;
            const payload = {
                risk_pct: parseFloat(document.getElementById('admRiskPerTrade').value),
                max_daily_loss: parseFloat(document.getElementById('admMaxDailyLoss').value),
                max_trades: parseInt(document.getElementById('admMaxTrades').value),
                trading_mode: document.getElementById('admTradingModeSelect').value,
                broker: document.getElementById('admBrokerChoice').value,
                client_code: document.getElementById('admClientCode').value
            };

            const res = await fetch('/api/admin/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': currentAuthToken },
                body: JSON.stringify(payload)
            });
            const d = await res.json();
            alert(d.message);

            // Update mode badge
            const badge = document.getElementById('badgeTradingMode');
            if (payload.trading_mode === 'LIVE') {
                badge.innerText = 'LIVE BROKER MODE';
                badge.className = 'text-xs bg-rose-950 text-rose-400 border border-rose-800 px-2.5 py-0.5 rounded-full font-mono font-semibold';
            } else {
                badge.innerText = 'PAPER MODE';
                badge.className = 'text-xs bg-blue-950 text-blue-400 border border-blue-800 px-2.5 py-0.5 rounded-full font-mono font-semibold';
            }
            closeAdminModal();
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
    </script>
</body>
</html>
"""

class TradingWebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path in ["/", "/index.html"]:
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

            if bot_running_state == "RUNNING":
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

                    # Open virtual trade if signal detected
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

                # Update active positions with Trailing SL
                paper_broker.update_positions(market_prices)

            resp_data = {
                "bot_state": bot_running_state,
                "trading_mode": Config.TRADING_MODE,
                "capital": paper_broker.capital,
                "daily_pnl": risk_manager.daily_pnl,
                "open_positions_count": len(paper_broker.open_positions),
                "open_positions": list(paper_broker.open_positions.values()),
                "watchlist": results
            }
            self.wfile.write(json.dumps(resp_data).encode('utf-8'))

        # ==========================================
        # API: UNIVERSAL STOCK SEARCH
        # ==========================================
        elif parsed.path == "/api/search":
            query = urllib.parse.parse_qs(parsed.query)
            symbol = query.get("symbol", ["TCS.NS"])[0].upper()
            if not symbol.endswith(".NS"):
                symbol += ".NS"

            mtf_data = DataFeed.get_mtf_data(symbol)
            setup = StrategyEngine.analyze_setup(mtf_data['5m'], symbol, df_macro=mtf_data['15m'])

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(setup).encode('utf-8'))

        # ==========================================
        # API: MULTI-STOCK COMPARISON
        # ==========================================
        elif parsed.path == "/api/compare":
            query = urllib.parse.parse_qs(parsed.query)
            raw_symbols = query.get("symbols", ["SBIN,PNB,RELIANCE"])[0]
            tickers = [s.strip().upper() for s in raw_symbols.split(",") if s.strip()]

            analyzed = []
            best_pick = None
            highest_score = -999

            for sym in tickers:
                if not sym.endswith(".NS"):
                    sym_clean = sym + ".NS"
                else:
                    sym_clean = sym

                mtf_data = DataFeed.get_mtf_data(sym_clean)
                setup = StrategyEngine.analyze_setup(mtf_data['5m'], sym_clean, df_macro=mtf_data['15m'])

                # Confluence Scoring (Trend + RSI + Proximity to Support + Signal)
                score = 0
                if setup['macro_trend'] == "BULLISH": score += 3
                if setup['signal'] == "BUY": score += 5
                elif setup['signal'] == "SELL": score += 4
                if 45 <= setup['rsi'] <= 60: score += 2

                if score > highest_score:
                    highest_score = score
                    best_pick = sym_clean

                analyzed.append(setup)

            verdict = f"{best_pick.replace('.NS', '')} presents the highest-probability setup with macro trend alignment and healthy risk-to-reward."
            resp = {
                "stocks": analyzed,
                "winner_symbol": best_pick,
                "verdict": verdict
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp).encode('utf-8'))

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

    def do_POST(self):
        global bot_running_state, admin_token

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        body = json.loads(post_data) if post_data else {}

        # 1. Admin PIN Auth
        if self.path == "/api/admin/auth":
            pin = body.get("pin", "")
            if pin == Config.ADMIN_PIN:
                admin_token = "auth_token_shiva_2403"
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "token": admin_token}).encode('utf-8'))
            else:
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": "Invalid PIN"}).encode('utf-8'))

        # 2. Admin Bot Control (Pause, Resume, Reset)
        elif self.path == "/api/admin/control":
            auth = self.headers.get("Authorization", "")
            if auth != "auth_token_shiva_2403":
                self.send_response(403)
                self.end_headers()
                return

            action = body.get("action")
            if action == "PAUSE":
                bot_running_state = "PAUSED"
                msg = "Bot successfully PAUSED by Owner."
            elif action == "RESUME":
                bot_running_state = "RUNNING"
                msg = "Bot successfully RESUMED."
            elif action == "RESET_CAPITAL":
                paper_broker.capital = 500.0
                risk_manager.daily_pnl = 0.0
                msg = "Virtual Capital reset to Rs. 500.00."
            else:
                msg = "Action executed."

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "message": msg}).encode('utf-8'))

        # 3. Admin Settings & Future Live Broker License Toggle
        elif self.path == "/api/admin/settings":
            auth = self.headers.get("Authorization", "")
            if auth != "auth_token_shiva_2403":
                self.send_response(403)
                self.end_headers()
                return

            Config.RISK_PER_TRADE_PERCENT = float(body.get("risk_pct", 2.0))
            Config.MAX_DAILY_LOSS = float(body.get("max_daily_loss", 20.0))
            Config.MAX_TRADES_PER_DAY = int(body.get("max_trades", 3))
            Config.TRADING_MODE = body.get("trading_mode", "PAPER")
            Config.BROKER_CHOICE = body.get("broker", "NONE")
            Config.BROKER_CLIENT_CODE = body.get("client_code", "")

            msg = f"Settings saved! Trading Mode set to {Config.TRADING_MODE}."

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "message": msg}).encode('utf-8'))

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
