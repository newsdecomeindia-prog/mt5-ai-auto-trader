from fastapi import APIRouter
from fastapi.responses import HTMLResponse

dashboard_router = APIRouter()

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MT5 AI Auto Trader - Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        :root {
            --bg-color: #0d1117;
            --card-bg: #161b22;
            --border-color: #30363d;
            --text-color: #c9d1d9;
            --accent-color: #58a6ff;
            --green-color: #238636;
            --red-color: #da3633;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 15px;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 10px;
        }
        h1 { margin: 0; font-size: 1.5rem; color: #ffffff; }
        .controls button {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            font-weight: bold;
            cursor: pointer;
            margin-left: 5px;
        }
        .btn-start { background-color: var(--green-color); color: white; }
        .btn-stop { background-color: var(--red-color); color: white; }
        .btn-restart { background-color: var(--accent-color); color: white; }

        .grid-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }
        .card-title { font-size: 0.85rem; color: #8b949e; text-transform: uppercase; }
        .card-value { font-size: 1.5rem; font-weight: bold; margin-top: 5px; color: #ffffff; }

        .chart-container {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            background-color: var(--card-bg);
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 20px;
            font-size: 0.9rem;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }
        th { background-color: #21262d; color: #8b949e; }
        tr:hover { background-color: #21262d; }
        .buy { color: #3fb950; font-weight: bold; }
        .sell { color: #f85149; font-weight: bold; }
    </style>
</head>
<body>
    <header>
        <h1>🤖 MT5 AI AUTO TRADER</h1>
        <div class="controls">
            <button class="btn-start" onclick="fetchAPI('/start', 'POST')">START</button>
            <button class="btn-stop" onclick="fetchAPI('/stop', 'POST')">STOP</button>
            <button class="btn-restart" onclick="fetchAPI('/restart', 'POST')">RESTART</button>
        </div>
    </header>

    <div class="grid-cards">
        <div class="card">
            <div class="card-title">Balance</div>
            <div class="card-value" id="val-balance">$10,000.00</div>
        </div>
        <div class="card">
            <div class="card-title">Equity</div>
            <div class="card-value" id="val-equity">$10,000.00</div>
        </div>
        <div class="card">
            <div class="card-title">Win Rate</div>
            <div class="card-value" id="val-winrate">0.0%</div>
        </div>
        <div class="card">
            <div class="card-title">Profit Factor</div>
            <div class="card-value" id="val-pf">0.00</div>
        </div>
    </div>

    <div class="chart-container">
        <div id="equityChart" style="width:100%; height:350px;"></div>
    </div>

    <h2>Open Positions</h2>
    <table>
        <thead>
            <tr>
                <th>Ticket</th>
                <th>Symbol</th>
                <th>Type</th>
                <th>Volume</th>
                <th>Open Price</th>
                <th>S/L</th>
                <th>T/P</th>
                <th>Profit</th>
            </tr>
        </thead>
        <tbody id="openTradesBody">
            <tr><td colspan="8" style="text-align:center;">No open trades</td></tr>
        </tbody>
    </table>

    <script>
        async function fetchAPI(endpoint, method = 'GET') {
            try {
                const res = await fetch(endpoint, { method });
                const data = await res.json();
                console.log(data);
                refreshDashboard();
            } catch (err) {
                console.error(err);
            }
        }

        async function refreshDashboard() {
            try {
                const [statusRes, statsRes, openRes] = await Promise.all([
                    fetch('/status').then(r => r.json()),
                    fetch('/statistics').then(r => r.json()),
                    fetch('/open-trades').then(r => r.json())
                ]);

                if (statusRes.account) {
                    document.getElementById('val-balance').innerText = '$' + statusRes.account.balance.toFixed(2);
                    document.getElementById('val-equity').innerText = '$' + statusRes.account.equity.toFixed(2);
                }

                document.getElementById('val-winrate').innerText = (statsRes.win_rate || 0).toFixed(1) + '%';
                document.getElementById('val-pf').innerText = (statsRes.profit_factor || 0).toFixed(2);

                const tbody = document.getElementById('openTradesBody');
                if (openRes.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;">No open trades</td></tr>';
                } else {
                    tbody.innerHTML = openRes.map(t => `
                        <tr>
                            <td>${t.ticket}</td>
                            <td>${t.symbol}</td>
                            <td class="${t.order_type.toLowerCase()}">${t.order_type}</td>
                            <td>${t.volume}</td>
                            <td>${t.open_price.toFixed(5)}</td>
                            <td>${t.stop_loss ? t.stop_loss.toFixed(5) : '-'}</td>
                            <td>${t.take_profit ? t.take_profit.toFixed(5) : '-'}</td>
                            <td style="color:${t.profit >= 0 ? '#3fb950' : '#f85149'}">$${t.profit.toFixed(2)}</td>
                        </tr>
                    `).join('');
                }

                const curve = statsRes.equity_curve || [10000];
                Plotly.newPlot('equityChart', [{
                    x: curve.map((_, i) => i),
                    y: curve,
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: { color: '#58a6ff', width: 3 }
                }], {
                    title: 'Equity Growth Curve',
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: { color: '#c9d1d9' },
                    margin: { t: 40, r: 20, l: 40, b: 40 }
                });

            } catch (e) {
                console.error("Dashboard refresh error:", e);
            }
        }

        refreshDashboard();
        setInterval(refreshDashboard, 5000);
    </script>
</body>
</html>
"""


@dashboard_router.get("/", response_class=HTMLResponse)
async def render_dashboard():
    return HTML_DASHBOARD
