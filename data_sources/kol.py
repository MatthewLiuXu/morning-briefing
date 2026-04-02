import time
import requests
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from config import CRYPTO_KOLS, TWITTER_API_KEY


def get_kol_tweets() -> list[dict]:
    """Fetch tweets from the last 24 hours for tracked crypto KOLs."""

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    headers = {"X-API-Key": TWITTER_API_KEY}
    results = []

    for kol in CRYPTO_KOLS:
        try:
            resp = requests.get(
                "https://api.twitterapi.io/twitter/user/last_tweets",
                params={"userName": kol["handle"]},
                headers=headers,
                timeout=15,
            )
            resp.raise_for_status()
            tweets = resp.json().get("data", {}).get("tweets", [])

            for tweet in tweets:
                try:
                    dt = parsedate_to_datetime(tweet["createdAt"])
                except (ValueError, TypeError):
                    continue

                if dt < cutoff:
                    continue

                # Skip pure retweets — they're someone else's content
                if tweet.get("text", "").startswith("RT @"):
                    continue

                results.append({
                    "kol": kol["name"],
                    "handle": kol["handle"],
                    "text": tweet["text"],
                    "created_at": tweet["createdAt"],
                    "likes": tweet.get("likeCount", 0),
                    "retweets": tweet.get("retweetCount", 0),
                    "views": tweet.get("viewCount", 0),
                })
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 429:
                # Rate limited — wait and retry once
                print(f"    ⏳ Rate limited on @{kol['handle']}, waiting 10s...")
                time.sleep(10)
                try:
                    resp = requests.get(
                        "https://api.twitterapi.io/twitter/user/last_tweets",
                        params={"userName": kol["handle"]},
                        headers=headers,
                        timeout=15,
                    )
                    resp.raise_for_status()
                    tweets = resp.json().get("data", {}).get("tweets", [])
                    for tweet in tweets:
                        try:
                            dt = parsedate_to_datetime(tweet["createdAt"])
                        except (ValueError, TypeError):
                            continue
                        if dt < cutoff:
                            continue
                        if tweet.get("text", "").startswith("RT @"):
                            continue
                        results.append({
                            "kol": kol["name"],
                            "handle": kol["handle"],
                            "text": tweet["text"],
                            "created_at": tweet["createdAt"],
                            "likes": tweet.get("likeCount", 0),
                            "retweets": tweet.get("retweetCount", 0),
                            "views": tweet.get("viewCount", 0),
                        })
                except Exception as retry_e:
                    print(f"    ⚠️ Retry failed for @{kol['handle']}: {retry_e}")
            else:
                print(f"    ⚠️ Could not fetch @{kol['handle']}: {e}")
            continue
        except Exception as e:
            print(f"    ⚠️ Could not fetch @{kol['handle']}: {e}")
            continue

        time.sleep(3)

    results.sort(key=lambda t: t["likes"] + t["retweets"], reverse=True)
    return results
