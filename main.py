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


def run_for_email(email: str):
    """Run the pipeline and email the result to a specific address."""
    print(f"  Generating briefing for {email}...")
    errors = []

    try:
        market = get_market_data()
    except Exception as e:
        errors.append(f"Market data failed: {e}")
        market = {"tokens": [], "btc_dominance": 0, "total_market_cap_usd": 0,
                  "market_cap_change_24h_pct": 0}

    try:
        funding = get_funding_rates()
    except Exception as e:
        errors.append(f"Funding rates failed: {e}")
        funding = []

    try:
        social = get_social_metrics()
    except Exception as e:
        errors.append(f"Social metrics failed: {e}")
        social = []

    try:
        trending = get_trending_tokens()
    except Exception as e:
        errors.append(f"Trending failed: {e}")
        trending = []

    try:
        news = get_news()
    except Exception as e:
        errors.append(f"News failed: {e}")
        news = []

    try:
        kol_tweets = get_kol_tweets()
    except Exception as e:
        errors.append(f"KOL tweets failed: {e}")
        kol_tweets = []

    portfolio = get_portfolio()

    enriched = enrich_data(market, funding, social, trending, news, portfolio,
                           kol_tweets=kol_tweets)
    enriched["data_source_errors"] = errors

    briefing = synthesize_briefing(enriched)
    send_email_to(briefing, email)
    print(f"  ✅ Briefing sent to {email}")


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
