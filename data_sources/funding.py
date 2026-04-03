import requests
from config import FUNDING_SYMBOLS

def get_funding_rates(funding_symbols=None) -> list[dict]:
    """Fetch latest funding rates from Hyperliquid perps."""
    symbols = funding_symbols if funding_symbols is not None else FUNDING_SYMBOLS

    url = "https://api.hyperliquid.xyz/info"
    resp = requests.post(url, json={"type": "metaAndAssetCtxs"}, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    # Response is [meta, asset_contexts]
    # meta["universe"] has asset names; asset_contexts has funding rates
    meta = data[0]["universe"]
    contexts = data[1]

    # Map symbols (e.g. "BTCUSDT") to bare names (e.g. "BTC")
    target_names = {sym.replace("USDT", ""): sym for sym in symbols}

    results = []
    for asset_info, ctx in zip(meta, contexts):
        name = asset_info["name"]
        if name in target_names:
            funding_rate = float(ctx["funding"])
            results.append({
                "symbol": target_names[name],
                "funding_rate": funding_rate,
                "funding_rate_pct": funding_rate * 100,
                "next_funding_time": None,
            })

    return results
