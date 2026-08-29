#!/usr/bin/env python3
"""
outreach_followup.py — Automated follow-up emails for HyperNexus outreach.

Sends up to 3 follow-ups on a schedule (Day 5, Day 10, Day 15) to
contacts who received the initial outreach but haven't replied.

Usage:
  python outreach_followup.py            # send due follow-ups now
  python outreach_followup.py --dry-run  # preview what would be sent
  python outreach_followup.py --stats    # show follow-up stats
"""

import sys
from datetime import datetime, timedelta, timezone


from outreach_smtp import send_email, get_db

# Follow-up schedule: days after initial send
SCHEDULE = {1: 5, 2: 10, 3: 15}

FOLLOWUP_TEMPLATES = {
    1: (
        "Re: {subject}",
        """Hi {name},

Quick follow-up on my earlier note about HyperNexus — the self-hosted AI
control plane. I know you're busy, so let me be brief:

HyperNexus runs entirely on your infrastructure — no cloud, no data
exfiltration. It adds persistent memory and progressive tool routing to
any local AI stack.

Worth a quick look? https://hypernexus.site

Best,
Robert
""",
    ),
    2: (
        "Re: {subject}",
        """Hi {name},

Just circling back one more time. I wanted to make sure you saw my
earlier email about HyperNexus.

The TL;DR: a local-first AI control plane with persistent L2 vector
memory and 60% token savings through progressive routing. Fully
self-hosted, zero-downtime updates.

If HyperNexus isn't a fit right now, no worries — just let me know and
I'll stop reaching out.

https://hypernexus.site

Best,
Robert
""",
    ),
    3: (
        "Re: {subject}",
        """Hi {name},

Last follow-up from me on this. If HyperNexus could help your team run
AI entirely on-prem with persistent memory across all tools, I'd love
to set up a 15-minute demo.

If not, I'll respect your time and won't reach out again.

https://hypernexus.site

Thanks either way,
Robert
""",
    ),
}


def get_due_followups():
    """Return contacts due for a follow-up (sent initial, no reply, next attempt due)."""
    conn = get_db()
    cur = conn.cursor()
    now = datetime.now(timezone.utc)

    due = []
    for attempt in range(1, 4):
        days = SCHEDULE[attempt]
        # Initial send happened >= days ago, attempt N is the latest, no reply
        cur.execute(
            """SELECT DISTINCT ON (contact_email)
                 contact_email, company_name, category, subject, attempt, sent_at
               FROM outreach_log
               WHERE status = 'sent'
                 AND replied_at IS NULL
                 AND sent_at <= %s
               ORDER BY contact_email, sent_at DESC""",
            (now - timedelta(days=days),),
        )
        rows = cur.fetchall()
        for email, company, category, subject, last_attempt, sent_at in rows:
            if last_attempt < attempt:
                due.append(
                    {
                        "email": email,
                        "company": company,
                        "category": category,
                        "subject": subject,
                        "attempt": attempt,
                        "sent_at": sent_at,
                    }
                )

    cur.close()
    conn.close()
    return due


def main():
    dry_run = "--dry-run" in sys.argv
    stats_only = "--stats" in sys.argv

    if stats_only:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT attempt, count(*) FROM outreach_log GROUP BY attempt ORDER BY attempt"
        )
        rows = cur.fetchall()
        cur.execute(
            "SELECT count(*) FROM outreach_log WHERE replied_at IS NOT NULL"
        )
        replies_row = cur.fetchone()
        replies = replies_row[0] if replies_row else 0
        cur.close()
        conn.close()
        print("Follow-up stats:")
        for attempt, count in rows:
            print(f"  Attempt {attempt}: {count} emails")
        print(f"  Replies received: {replies}")
        return

    due = get_due_followups()
    print(f"Found {len(due)} contacts due for follow-up")

    if dry_run:
        for d in due:
            print(
                f"  [Follow-up {d['attempt']}] {d['email']} ({d['company']}) — "
                f"re: {d['subject']}"
            )
        return

    sent = 0
    for d in due:
        subject_tpl, body_tpl = FOLLOWUP_TEMPLATES[d["attempt"]]
        subject = subject_tpl.format(subject=d["subject"])
        body = body_tpl.format(name="there", subject=d["subject"])
        ok = send_email(
            d["email"],
            subject,
            body,
            company_name=d["company"],
            category=d["category"],
        )
        if ok:
            sent += 1

    print(f"Follow-up complete: sent {sent}/{len(due)}")


if __name__ == "__main__":
    main()
