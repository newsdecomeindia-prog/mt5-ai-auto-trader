# Deployment Guide

## Docker Compose VPS Deployment

1. **Deploy using Docker Compose:**
   ```bash
   docker-compose up -d --build
   ```

2. **Check container logs & health:**
   ```bash
   docker-compose logs -f mt5-trader
   docker-compose ps
   ```

## Systemd Service (Linux VPS)

To run as a background Linux service:

```ini
[Unit]
Description=MT5 AI Auto Trading Platform
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/app
ExecStart=/app/venv/bin/python run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
