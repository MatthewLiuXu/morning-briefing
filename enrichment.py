from config import PRICE_ALERT_THRESHOLD, FUNDING_ALERT_THRESHOLD


def enrich_data(market: dict, funding: list, social: list,
                trending: list, news: list, portfolio: dict,
                kol_tweets: list | None = None) -> dict:
    """
    Compute PnL, flag anomalies, and structure everything
    into a single dict ready for the Claude prompt.
    """

    # --- Portfolio PnL ---
    token_lookup = {t["symbol"]: t for t in market["tokens"]}
    positions = []
    total_current_value = 0
    total_entry_value = 0

    for token_id, pos in portfolio.items():
        symbol = pos["symbol"]
        market_data = token_lookup.get(symbol)
        if not market_data:
            continue

        current_value = market_data["price"] * pos["quantity"]
        entry_value = pos["entry_price"] * pos["quantity"]
        pnl = current_value - entry_value
        overnight_change = current_value * (market_data["change_24h_pct"] / 100)

        total_current_value += current_value
        total_entry_value += entry_value

        positions.append({
            "symbol": symbol,
            "quantity": pos["quantity"],
            "entry_price": pos["entry_price"],
            "current_price": market_data["price"],
            "change_24h_pct": market_data["change_24h_pct"],
            "overnight_pnl_usd": round(overnight_change, 2),
            "total_pnl_usd": round(pnl, 2),
            "current_value_usd": round(current_value, 2),
            "is_alert": abs(market_data["change_24h_pct"] / 100) > PRICE_ALERT_THRESHOLD,
        })

    positions.sort(key=lambda x: x["change_24h_pct"], reverse=True)

    total_overnight_pnl = sum(p["overnight_pnl_usd"] for p in positions)
    total_overnight_pct = (total_overnight_pnl / total_current_value * 100) if total_current_value else 0

    # --- Funding Rate Flags ---
    funding_alerts = [
        f for f in funding
        if abs(f["funding_rate_pct"]) > FUNDING_ALERT_THRESHOLD
    ]

    # --- Social Spikes ---
    social_alerts = [
        s for s in social
        if abs(s.get("social_volume_change_pct", 0)) > 100  # >100% change
    ]

    return {
        "portfolio_summary": {
            "total_value_usd": round(total_current_value, 2),
            "overnight_pnl_usd": round(total_overnight_pnl, 2),
            "overnight_pnl_pct": round(total_overnight_pct, 2),
            "positions": positions,
        },
        "market_context": {
            "btc_dominance": market["btc_dominance"],
            "total_market_cap_usd": market["total_market_cap_usd"],
            "market_cap_change_24h_pct": market["market_cap_change_24h_pct"],
        },
        "funding_rates": funding,
        "funding_alerts": funding_alerts,
        "social_metrics": social,
        "social_alerts": social_alerts,
        "trending_tokens": trending,
        "news_headlines": news,
        "kol_tweets": kol_tweets or [],
        "alerts_summary": {
            "price_alerts": [p["symbol"] for p in positions if p["is_alert"]],
            "funding_alerts": [f["symbol"] for f in funding_alerts],
            "social_spikes": [s["symbol"] for s in social_alerts],
        },
    }
