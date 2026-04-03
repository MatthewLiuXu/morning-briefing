import sys
import traceback
from datetime import datetime

from data_sources.market import get_market_data
from data_sources.funding import get_funding_rates
from data_sources.social import get_social_metrics, get_trending_tokens
from data_sources.news import get_news
from data_sources.kol import get_kol_tweets
from data_sources.portfolio import get_portfolio
from enrichment import enrich_data
from synthesizer import synthesize_briefing
from delivery import post_to_slack, send_email, send_email_to


def run_for_email(email: str, status_callback=None):
    """Run the pipeline and email the result to a specific address.

    If status_callback is provided, it's called with (step_name, status)
    for real-time progress updates.
    """
    def update(step_id, message, status="ok"):
        if status_callback:
            status_callback(step_id, message, status)
        print(f"  [{status}] {message}")

    errors = []

    steps = [
        ("market",   "Market data",    lambda: get_market_data()),
        ("funding",  "Funding rates",  lambda: get_funding_rates()),
        ("social",   "Social metrics", lambda: get_social_metrics()),
        ("trending", "Trending tokens",lambda: get_trending_tokens()),
        ("news",     "News",           lambda: get_news()),
        ("kol",      "KOL tweets",     lambda: get_kol_tweets()),
    ]

    defaults = {
        "market": {"tokens": [], "btc_dominance": 0, "total_market_cap_usd": 0,
                   "market_cap_change_24h_pct": 0},
        "funding": [], "social": [], "trending": [], "news": [], "kol": [],
    }

    results = {}
    for step_id, label, fetch_fn in steps:
        update(step_id, f"Fetching {label.lower()}...", "loading")
        try:
            results[step_id] = fetch_fn()
            count = len(results[step_id]) if isinstance(results[step_id], list) else None
            done_msg = f"{label} loaded"
            if count is not None:
                done_msg += f" — {count} items"
            update(step_id, done_msg, "ok")
        except Exception as e:
            errors.append(f"{label} failed: {e}")
            results[step_id] = defaults[step_id]
            update(step_id, f"{label} failed", "error")

    portfolio = get_portfolio()

    update("enrich", "Enriching data...", "loading")
    enriched = enrich_data(
        results["market"], results["funding"], results["social"],
        results["trending"], results["news"], portfolio,
        kol_tweets=results["kol"],
    )
    enriched["data_source_errors"] = errors
    update("enrich", "Data enriched", "ok")

    update("claude", "Generating brief with Claude AI...", "loading")
    briefing = synthesize_briefing(enriched)
    update("claude", "Brief generated", "ok")

    update("email", f"Sending to {email}...", "loading")
    try:
        send_email_to(briefing, email)
        update("email", f"Briefing sent to {email}!", "done")
    except Exception as e:
        update("email", f"Email failed: {e}", "error")
        update("done", "Briefing generated but email delivery failed. Check server logs for [email] details.", "done")


def run():
    print(f"[{datetime.now()}] Starting morning briefing...")
    errors = []

    # --- Stage 1: Gather ---
    print("  Fetching market data...")
    try:
        market = get_market_data()
    except Exception as e:
        errors.append(f"Market data failed: {e}")
        market = {"tokens": [], "btc_dominance": 0, "total_market_cap_usd": 0,
                  "market_cap_change_24h_pct": 0}

    print("  Fetching funding rates...")
    try:
        funding = get_funding_rates()
    except Exception as e:
        errors.append(f"Funding rates failed: {e}")
        funding = []

    print("  Fetching social metrics...")
    try:
        social = get_social_metrics()
    except Exception as e:
        errors.append(f"Social metrics failed: {e}")
        social = []

    print("  Fetching trending tokens...")
    try:
        trending = get_trending_tokens()
    except Exception as e:
        errors.append(f"Trending failed: {e}")
        trending = []

    print("  Fetching news...")
    try:
        news = get_news()
    except Exception as e:
        errors.append(f"News failed: {e}")
        news = []

    print("  Fetching KOL tweets...")
    try:
        kol_tweets = get_kol_tweets()
    except Exception as e:
        errors.append(f"KOL tweets failed: {e}")
        kol_tweets = []

    print("  Loading portfolio...")
    portfolio = get_portfolio()

    # --- Stage 2: Enrich ---
    print("  Enriching data...")
    enriched = enrich_data(market, funding, social, trending, news, portfolio,
                           kol_tweets=kol_tweets)

    # Attach any data source errors so Claude can mention gaps
    enriched["data_source_errors"] = errors

    # --- Stage 3: Synthesize ---
    print("  Generating brief with Claude...")
    briefing = synthesize_briefing(enriched)

    # --- Stage 4: Deliver ---
    print("  Delivering brief...")
    post_to_slack(briefing)
    send_email(briefing)

    if errors:
        print(f"  ⚠️ Completed with {len(errors)} data source errors:")
        for err in errors:
            print(f"    - {err}")
    else:
        print("  ✅ Completed successfully")


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
