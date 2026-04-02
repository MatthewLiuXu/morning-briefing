import requests
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import (SLACK_WEBHOOK_URL, RESEND_API_KEY, EMAIL_FROM, EMAIL_TO,
                    GMAIL_ADDRESS, GMAIL_APP_PASSWORD)


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


def _build_briefing_html(briefing: str) -> tuple[str, str, str]:
    """Return (date_str, timestamp, html) for a briefing email."""
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
    return date_str, timestamp, html


def _send_via_gmail(to_emails: list[str], subject: str, html: str) -> bool:
    """Send an email via Gmail SMTP using an App Password."""
    msg = MIMEMultipart("alternative")
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = ", ".join(to_emails)
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, to_emails, msg.as_string())
    return True


def _send_via_resend(to_emails: list[str], subject: str, html: str) -> bool:
    """Send an email via Resend API."""
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": EMAIL_FROM,
            "to": to_emails,
            "subject": subject,
            "html": html,
        },
        timeout=15,
    )
    if resp.status_code == 200:
        return True
    raise RuntimeError(f"Resend failed: {resp.status_code} — {resp.text}")


def send_email(briefing: str) -> bool:
    """Send the morning brief via email (Gmail SMTP or Resend fallback)."""
    if not EMAIL_TO:
        print("⏭️  Email delivery skipped (no EMAIL_TO)")
        return False

    recipients = [e.strip() for e in EMAIL_TO.split(",")]
    date_str, _, html = _build_briefing_html(briefing)
    subject = f"Crypto Morning Brief — {date_str}"

    try:
        if GMAIL_ADDRESS and GMAIL_APP_PASSWORD:
            _send_via_gmail(recipients, subject, html)
        elif RESEND_API_KEY:
            _send_via_resend(recipients, subject, html)
        else:
            print("⏭️  Email delivery skipped (no Gmail or Resend credentials)")
            return False
    except Exception as e:
        print(f"❌ Email delivery failed: {e}")
        return False

    print(f"✅ Brief emailed to {', '.join(recipients)}")
    return True


def send_email_to(briefing: str, to_email: str) -> bool:
    """Send the morning brief to a specific email address."""
    date_str, _, html = _build_briefing_html(briefing)
    subject = f"Crypto Morning Brief — {date_str}"

    if GMAIL_ADDRESS and GMAIL_APP_PASSWORD:
        _send_via_gmail([to_email], subject, html)
    elif RESEND_API_KEY:
        _send_via_resend([to_email], subject, html)
    else:
        raise RuntimeError("No email credentials configured (set GMAIL_ADDRESS + GMAIL_APP_PASSWORD, or RESEND_API_KEY)")
    return True
