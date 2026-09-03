# Installation & Local Setup Guide

## Requirements
- Python 3.12+
- MetaTrader 5 Terminal (Windows) or Docker (Linux/VPS)

## Installation Steps

1. **Clone the repository:**
   ```bash
   git clone <repo_url>
   cd mt5-ai-auto-trader
   ```

2. **Create virtual environment & install dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Copy `.env.example` to `.env` and fill in your MT5 credentials:
   ```bash
   cp .env.example .env
   ```

4. **Run Platform:**
   ```bash
   python run.py
   ```
   Open your browser at `http://localhost:8000` to access the interactive web dashboard.
