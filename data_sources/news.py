import requests


def get_news() -> list[dict]:
    """Fetch recent crypto news from CoinGecko."""

    url = "https://api.coingecko.com/api/v3/news"
    params = {"page": 1}

    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    results = resp.json().get("data", resp.json())

    headlines = []
    for item in results[:15]:
        headlines.append({
            "title": item["title"],
            "url": item.get("url", ""),
            "source": item.get("news_site", "Unknown"),
            "published_at": item.get("created_at", ""),
            "currencies": [],
            "sentiment": {},
        })

    return headlines
