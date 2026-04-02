import requests
import json
from datetime import datetime
from config import SLACK_WEBHOOK_URL, RESEND_API_KEY, EMAIL_FROM, EMAIL_TO


def post_to_slack(briefing: str) -> bool:
    """Post the morning brief to a Slack channel via webhook."""

    if not SLACK_WEBHOOK_URL:
        print("⏭️  Slack delivery skipped (no SLACK_WEBHOOK_URL)")
        return False

    timestamp = datetime.now().strftime("%B %d, %Y — %I:%M %p EST")
    header = f"☀️ *Morning Brief — {timestamp}*\n{'—' * 40}\n\n"

    payload = {
        "text": header + briefing,
        "unfurl_links": False,
    }

    resp = requests.post(
        SLACK_WEBHOOK_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=15,
    )

    if resp.status_code == 200:
        print("✅ Brief posted to Slack")
        return True
    else:
        print(f"❌ Slack delivery failed: {resp.status_code} — {resp.text}")
        return False


def send_email(briefing: str) -> bool:
    """Send the morning brief via email using Resend."""

    if not RESEND_API_KEY or not EMAIL_TO:
        print("⏭️  Email delivery skipped (no RESEND_API_KEY or EMAIL_TO)")
        return False

    recipients = [e.strip() for e in EMAIL_TO.split(",")]
    date_str = datetime.now().strftime("%b %d, %Y")
    timestamp = datetime.now().strftime("%B %d, %Y — %I:%M %p EST")

    # Convert the plain-text briefing to simple HTML for readability
    html_body = briefing.replace("\n", "<br>\n")
    html = f"""<div style="font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
<h2>Morning Brief — {timestamp}</h2>
<hr>
<div style="font-size: 14px; line-height: 1.6;">
{html_body}
</div>
</div>"""

    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": EMAIL_FROM,
            "to": recipients,
            "subject": f"Crypto Morning Brief — {date_str}",
            "html": html,
        },
        timeout=15,
    )

    if resp.status_code == 200:
        print(f"✅ Brief emailed to {', '.join(recipients)}")
        return True
    else:
        print(f"❌ Email delivery failed: {resp.status_code} — {resp.text}")
        return False


def send_email_to(briefing: str, to_email: str) -> bool:
    """Send the morning brief to a specific email address via Resend."""

    if not RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY not configured")

    date_str = datetime.now().strftime("%b %d, %Y")
    timestamp = datetime.now().strftime("%B %d, %Y — %I:%M %p EST")

    html_body = briefing.replace("\n", "<br>\n")
    html = f"""<div style="font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
<h2>Crypto Morning Brief — {timestamp}</h2>
<hr>
<div style="font-size: 14px; line-height: 1.6;">
{html_body}
</div>
</div>"""

    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": EMAIL_FROM,
            "to": [to_email],
            "subject": f"Crypto Morning Brief — {date_str}",
            "html": html,
        },
        timeout=15,
    )

    if resp.status_code == 200:
        return True
    else:
        raise RuntimeError(f"Email failed: {resp.status_code} — {resp.text}")
