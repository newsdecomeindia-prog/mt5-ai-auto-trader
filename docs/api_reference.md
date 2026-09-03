# REST API & WebSocket Reference

## REST API Endpoints (`/api/v1`)

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/health` | `GET` | Health check for MT5 connection & platform state |
| `/status` | `GET` | Current account & operational status |
| `/start` | `POST` | Start auto trading engine |
| `/stop` | `POST` | Stop auto trading engine |
| `/restart` | `POST` | Reconnect MT5 & restart trading engine |
| `/open-trades` | `GET` | List active open positions |
| `/history` | `GET` | List closed trade history |
| `/statistics` | `GET` | Quantitative performance analytics |
| `/settings` | `GET` / `POST` | Read or update configuration settings |
| `/order` | `POST` | Execute market or pending order |

## WebSocket Endpoint

- `ws://localhost:8000/api/v1/ws/live`: Real-time JSON stream pushing live balance, equity, margin, and ticks.
