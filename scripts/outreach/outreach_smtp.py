#!/usr/bin/env python3
"""
outreach_smtp.py — SMTP automation core for HyperNexus outreach.

Handles all email sending with:
  - Gmail SMTP (STARTTLS) with app password
  - Rate limiting (max N emails/hour)
  - Delivery tracking in PostgreSQL (outreach_log table)
  - Retry with exponential backoff
  - Plain-text + HTML support
"""

import os
import smtplib
import time
import logging
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    import psycopg2
except ImportError:  # pragma: no cover - server-only dependency
    psycopg2 = None

logger = logging.getLogger("outreach_smtp")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ─── Config (overridable via env) ────────────────────────────────────────────
def _safe_int(value, default):
    """Parse an int from env, falling back to default on error."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value, default):
    """Parse a float from env, falling back to default on error."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = _safe_int(os.environ.get("SMTP_PORT"), 587)
SMTP_USER = os.environ.get("SMTP_USERNAME", "hypernexusofficialllc@gmail.com")
SMTP_PASS = os.environ.get("SMTP_PASSWORD", "amwz medv gvtu fmlj")
SMTP_FROM_NAME = os.environ.get("SMTP_FROM_NAME", "HyperNexus Official")

DB_DSN = os.environ.get(
    "DATABASE_URL",
    "postgres://sales_bot:tormentnexus2026@localhost:5432/sales_bot",
)

# Rate limiting: max emails per window
MAX_PER_HOUR = _safe_int(os.environ.get("OUTREACH_MAX_PER_HOUR"), 30)
DELAY_BETWEEN = _safe_float(os.environ.get("OUTREACH_DELAY"), 12.0)  # seconds

# Track last send timestamps for rate limiting
_send_times = []


def _rate_limited():
    """Return True if we should wait before sending next email."""
    global _send_times
    now = time.time()
    # Keep only sends from the last hour
    _send_times = [t for t in _send_times if now - t < 3600]
    return len(_send_times) >= MAX_PER_HOUR


def get_db():
    """Return a fresh DB connection."""
    if psycopg2 is None:
        raise RuntimeError("psycopg2 is not installed — install with: pip install psycopg2-binary")
    return psycopg2.connect(DB_DSN)


def log_outreach(contact_email, company_name, category, subject, body, status="sent", attempt=1, error=None):
    """Record an outreach email in the outreach_log table."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO outreach_log
               (contact_email, company_name, category, subject, body, status, attempt, sent_at, error)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (contact_email, company_name, category, subject, body, status, attempt, datetime.now(timezone.utc), error),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:  # noqa: BLE001 - logging must never crash the send
        logger.warning("Failed to log outreach to DB: %s", e)


def send_email(to_email, subject, body_plain, body_html=None, reply_to=None, company_name=None, category=None):
    """
    Send a single email via SMTP and log it.

    Returns True on success, False on failure.
    """
    # Rate limit: wait until under limit
    while _rate_limited():
        wait = 60
        logger.info("Rate limit hit — sleeping %ss", wait)
        time.sleep(wait)

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    if reply_to:
        msg["Reply-To"] = reply_to

    msg.attach(MIMEText(body_plain, "plain"))
    if body_html:
        msg.attach(MIMEText(body_html, "html"))

    # Send with retries (3 attempts, exponential backoff)
    last_err = None
    for attempt in range(1, 4):
        try:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            server.quit()
            log_outreach(to_email, company_name, category, subject, body_plain, status="sent", attempt=attempt)
            _send_times.append(time.time())
            logger.info("Sent: %s", to_email)
            time.sleep(DELAY_BETWEEN)
            return True
        except Exception as e:  # noqa: BLE001 - retry on any SMTP error
            last_err = e
            logger.warning("Attempt %d failed for %s: %s", attempt, to_email, e)
            if attempt < 3:
                time.sleep(30 * attempt)

    log_outreach(to_email, company_name, category, subject, body_plain, status="failed", error=str(last_err))
    logger.error("Failed to send after 3 attempts: %s — %s", to_email, last_err)
    return False


def send_bulk(contacts, subject_fn, body_fn, category="general", max_sends=None):
    """
    Send emails to a list of contacts.

    contacts: list of dicts with keys: email, name, company
    subject_fn: callable(contact) -> subject string
    body_fn: callable(contact) -> body string (plain text)
    """
    sent = 0
    failed = 0
    total = len(contacts) if max_sends is None else min(max_sends, len(contacts))

    logger.info("Starting bulk send: %d emails (category=%s)", total, category)
    for i, contact in enumerate(contacts[:total]):
        try:
            subject = subject_fn(contact)
            body = body_fn(contact)
            ok = send_email(
                contact["email"],
                subject,
                body,
                company_name=contact.get("company"),
                category=category,
            )
            if ok:
                sent += 1
            else:
                failed += 1
        except Exception as e:  # noqa: BLE001
            logger.error("Error processing contact %s: %s", contact.get("email"), e)
            failed += 1

        if (i + 1) % 10 == 0:
            logger.info("Progress: %d/%d (sent=%d failed=%d)", i + 1, total, sent, failed)

    logger.info("Bulk send complete: sent=%d failed=%d total=%d", sent, failed, total)
    return {"sent": sent, "failed": failed, "total": total}


def get_stats():
    """Return outreach stats from the DB."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT status, count(*) FROM outreach_log GROUP BY status")
        rows = cur.fetchall()
        cur.execute("SELECT count(DISTINCT contact_email) FROM outreach_log")
        unique_row = cur.fetchone()
        unique = unique_row[0] if unique_row else 0
        cur.execute("SELECT count(*) FROM outreach_log WHERE replied_at IS NOT NULL")
        replies_row = cur.fetchone()
        replies = replies_row[0] if replies_row else 0
        cur.execute("SELECT count(*) FROM outreach_log WHERE opened_at IS NOT NULL")
        opens_row = cur.fetchone()
        opens = opens_row[0] if opens_row else 0
        cur.close()
        conn.close()
        return {"status_counts": dict(rows), "unique_contacts": unique, "replies": replies, "opens": opens}
    except Exception as e:  # noqa: BLE001
        logger.error("Failed to get stats: %s", e)
        return {}


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--stats":
        print(json.dumps(get_stats(), indent=2))
    else:
        print("outreach_smtp.py — SMTP automation core for HyperNexus outreach")
        print("Usage:")
        print("  python outreach_smtp.py --stats   # show delivery stats")
        print("Import send_email / send_bulk into your outreach scripts.")
