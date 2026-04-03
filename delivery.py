import base64
import requests
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import (SLACK_WEBHOOK_URL, RESEND_API_KEY, EMAIL_FROM, EMAIL_TO,
                    GMAIL_ADDRESS, GMAIL_APP_PASSWORD, SENDGRID_API_KEY,
                    GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN)


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


def _send_via_gmail_api(to_emails: list[str], subject: str, html: str) -> bool:
    """Send an email via Gmail API (OAuth2, HTTPS — no SMTP ports needed)."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials(
        token=None,
        refresh_token=GMAIL_REFRESH_TOKEN,
        client_id=GMAIL_CLIENT_ID,
        client_secret=GMAIL_CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
    )
    creds.refresh(Request())
    service = build("gmail", "v1", credentials=creds)

    for to_email in to_emails:
        msg = MIMEText(html, "html")
        msg["to"] = to_email
        msg["from"] = GMAIL_ADDRESS
        msg["subject"] = subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return True


def _send_via_sendgrid(to_emails: list[str], subject: str, html: str) -> bool:
    """Send an email via SendGrid API."""
    resp = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "personalizations": [{"to": [{"email": e} for e in to_emails]}],
            "from": {"email": EMAIL_FROM},
            "subject": subject,
            "content": [{"type": "text/html", "value": html}],
        },
        timeout=15,
    )
    if resp.status_code in (200, 202):
        return True
    raise RuntimeError(f"SendGrid failed: {resp.status_code} — {resp.text}")


def _send_via_gmail(to_emails: list[str], subject: str, html: str) -> bool:
    """Send an email via Gmail SMTP using an App Password."""
    msg = MIMEMultipart("alternative")
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = ", ".join(to_emails)
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
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


def _try_send(to_emails: list[str], subject: str, html: str) -> bool:
    """Try each configured email provider in order: Gmail API > SendGrid > Gmail SMTP > Resend."""
    providers = []
    if GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET and GMAIL_REFRESH_TOKEN:
        providers.append(("Gmail API", lambda: _send_via_gmail_api(to_emails, subject, html)))
    if SENDGRID_API_KEY:
        providers.append(("SendGrid", lambda: _send_via_sendgrid(to_emails, subject, html)))
    if GMAIL_ADDRESS and GMAIL_APP_PASSWORD:
        providers.append(("Gmail SMTP", lambda: _send_via_gmail(to_emails, subject, html)))
    if RESEND_API_KEY:
        providers.append(("Resend", lambda: _send_via_resend(to_emails, subject, html)))

    if not providers:
        raise RuntimeError("No email credentials configured (set SENDGRID_API_KEY, GMAIL_ADDRESS + GMAIL_APP_PASSWORD, or RESEND_API_KEY)")

    for name, send_fn in providers:
        try:
            print(f"[email] Trying {name}...")
            send_fn()
            print(f"[email] {name} succeeded")
            return True
        except Exception as e:
            print(f"[email] {name} failed: {e}")

    raise RuntimeError("All email providers failed — check server logs for details")


def send_email(briefing: str) -> bool:
    """Send the morning brief via email."""
    if not EMAIL_TO:
        print("⏭️  Email delivery skipped (no EMAIL_TO)")
        return False

    recipients = [e.strip() for e in EMAIL_TO.split(",")]
    date_str, _, html = _build_briefing_html(briefing)
    subject = f"Crypto Morning Brief — {date_str}"

    try:
        _try_send(recipients, subject, html)
    except Exception as e:
        print(f"❌ Email delivery failed: {e}")
        return False

    print(f"✅ Brief emailed to {', '.join(recipients)}")
    return True


def send_email_to(briefing: str, to_email: str) -> bool:
    """Send the morning brief to a specific email address."""
    date_str, _, html = _build_briefing_html(briefing)
    subject = f"Crypto Morning Brief — {date_str}"
    _try_send([to_email], subject, html)
    return True
