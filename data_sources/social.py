import requests
from config import PORTFOLIO_TOKENS

# CoinGecko ID → CoinPaprika ID mapping
COINPAPRIKA_IDS = {
    "bitcoin": "btc-bitcoin",
    "ethereum": "eth-ethereum",
    "solana": "sol-solana",
    "avalanche-2": "avax-avalanche",
    "arbitrum": "arb-arbitrum",
}


def get_social_metrics() -> list[dict]:
    """Fetch community data for portfolio tokens from CoinPaprika."""

    results = []
    for token_id, token in PORTFOLIO_TOKENS.items():
        cp_id = COINPAPRIKA_IDS.get(token_id)
        if not cp_id:
            continue

        url = f"https://api.coinpaprika.com/v1/coins/{cp_id}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        twitter_followers = 0
        reddit_subscribers = 0
        for link in data.get("links_extended", []):
            link_stats = link.get("stats", {})
            if link.get("type") == "twitter":
                twitter_followers = link_stats.get("followers", 0)
            elif link.get("type") == "reddit":
                reddit_subscribers = link_stats.get("subscribers", 0)

        results.append({
            "symbol": token["symbol"],
            "name": data.get("name", ""),
            "twitter_followers": twitter_followers,
            "reddit_subscribers": reddit_subscribers,
            # No free equivalent for social volume change
            "social_volume_change_pct": 0,
        })

    return results


def get_trending_tokens() -> list[dict]:
    """Fetch top trending tokens by search activity from CoinGecko."""

    url = "https://api.coingecko.com/api/v3/search/trending"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    coins = resp.json().get("coins", [])

    return [
        {
            "symbol": entry["item"]["symbol"].upper(),
            "name": entry["item"]["name"],
            "market_cap_rank": entry["item"].get("market_cap_rank"),
            "social_volume_24h": 0,
            "social_volume_change_pct": 0,
        }
        for entry in coins[:10]
    ]
