import os
from dotenv import load_dotenv

load_dotenv()

# --- API Keys ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_API_KEY")
LUNARCRUSH_API_KEY = os.getenv("LUNARCRUSH_API_KEY")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM", "briefing@resend.dev")
EMAIL_TO = os.getenv("EMAIL_TO")  # comma-separated list of recipient emails
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

# --- Twitter / KOL Tracking ---
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")

CRYPTO_KOLS = [
    {"handle": "CryptoHayes", "name": "Arthur Hayes"},
    {"handle": "VitalikButerin", "name": "Vitalik Buterin"},
    {"handle": "inversebrah", "name": "inversebrah"},
    {"handle": "GCRClassic", "name": "GCR"},
    {"handle": "Pentosh1", "name": "Pentoshi"},
    {"handle": "lightcrypto", "name": "Light"},
    {"handle": "DegenSpartan", "name": "Degen Spartan"},
    {"handle": "cburniske", "name": "Chris Burniske"},
]

# --- Portfolio Tokens ---
# Map your internal names to CoinGecko IDs and ticker symbols
PORTFOLIO_TOKENS = {
    "bitcoin":    {"symbol": "BTC", "quantity": 5.0,    "entry_price": 82000},
    "ethereum":   {"symbol": "ETH", "quantity": 50.0,   "entry_price": 3200},
    "solana":     {"symbol": "SOL", "quantity": 1000.0,  "entry_price": 145},
    "avalanche-2":{"symbol": "AVAX","quantity": 5000.0,  "entry_price": 38},
    "arbitrum":   {"symbol": "ARB", "quantity": 50000.0, "entry_price": 1.10},
}

# Binance perp symbols for funding rates (only tokens you trade perps on)
FUNDING_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "AVAXUSDT", "ARBUSDT"]

# Thresholds
PRICE_ALERT_THRESHOLD = 0.05   # flag tokens that moved > 5%
FUNDING_ALERT_THRESHOLD = 0.05 # flag funding rates > 0.05%
