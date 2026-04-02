import requests
from config import PORTFOLIO_TOKENS

def get_market_data() -> dict:
    """Fetch 24h price, volume, market cap for portfolio tokens + BTC dominance."""

    ids = ",".join(PORTFOLIO_TOKENS.keys())
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ids,
        "order": "market_cap_desc",
        "sparkline": "false",
        "price_change_percentage": "24h",
    }

    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    tokens = resp.json()

    # Also grab global data for BTC dominance and total market cap
    global_resp = requests.get(
        "https://api.coingecko.com/api/v3/global", timeout=15
    )
    global_resp.raise_for_status()
    global_data = global_resp.json()["data"]

    return {
        "tokens": [
            {
                "id": t["id"],
                "symbol": t["symbol"].upper(),
                "price": t["current_price"],
                "change_24h_pct": t.get("price_change_percentage_24h", 0),
                "volume_24h": t["total_volume"],
                "market_cap": t["market_cap"],
            }
            for t in tokens
        ],
        "btc_dominance": global_data["market_cap_percentage"]["btc"],
        "total_market_cap_usd": global_data["total_market_cap"]["usd"],
        "market_cap_change_24h_pct": global_data["market_cap_change_percentage_24h_usd"],
    }
