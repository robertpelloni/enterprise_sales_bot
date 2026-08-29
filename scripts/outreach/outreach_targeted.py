#!/usr/bin/env python3
"""
outreach_targeted.py — Personalized CTO pitches for HyperNexus.

Sends highly personalized outreach to CTOs and technical decision-makers
from the contacts database. Uses role + company to customize the pitch.

Usage:
  python outreach_targeted.py            # send to all CTO/technical contacts
  python outreach_targeted.py --dry-run  # preview
  python outreach_targeted.py --limit 5  # send to first 5
"""

import sys

from outreach_smtp import logger, send_email, get_db


def get_cto_contacts(limit=None):
    """Fetch CTO/technical decision-maker contacts from the DB."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """SELECT c.name, c.email, c.role, co.name AS company
           FROM contacts c
           LEFT JOIN companies co ON c.company_id = co.id
           WHERE c.email IS NOT NULL
             AND c.email != ''
             AND (
               LOWER(c.role) LIKE '%cto%'
               OR LOWER(c.role) LIKE '%chief technology%'
               OR LOWER(c.role) LIKE '%founder%'
               OR LOWER(c.role) LIKE '%head of engineering%'
               OR LOWER(c.role) LIKE '%vp engineering%'
               OR LOWER(c.role) LIKE '%architect%'
             )
           ORDER BY c.id
           LIMIT %s""",
        (limit if limit else 1000,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"name": r[0], "email": r[1], "role": r[2], "company": r[3] or ""}
        for r in rows
    ]


def subject_for(contact):
    return f"HyperNexus for {contact['company']} — local AI, no cloud"


def body_for(contact):
    name = contact["name"] or "there"
    role = contact["role"] or "your team"
    company = contact["company"] or "your company"
    return (
        f"Hi {name},\n\n"
        f"As {role} at {company}, you probably deal with the same problem "
        f"we set out to solve: AI tools that send your data to the cloud.\n\n"
        f"HyperNexus is a local-first AI control plane that runs entirely "
        f"on your infrastructure:\n\n"
        f"  • Persistent L2 vector memory — shared across all AI tools\n"
        f"  • Progressive tool routing — up to 60% token savings\n"
        f"  • Model-agnostic — works with Ollama, vLLM, llama.cpp\n"
        f"  • Zero-downtime self-hosted deployment\n\n"
        f"For a team like {company}, that means full control over your AI "
        f"stack with no vendor lock-in and no data leaving your perimeter.\n\n"
        f"Would a 15-minute demo be useful? https://hypernexus.site\n\n"
        f"Best,\n"
        f"Robert Pelloni\n"
        f"Founder, HyperNexus\n"
        f"https://hypernexus.site"
    )


def main():
    dry_run = "--dry-run" in sys.argv
    limit = None
    if "--limit" in sys.argv:
        try:
            idx = sys.argv.index("--limit")
            limit = int(sys.argv[idx + 1])
        except (ValueError, IndexError):
            logger.warning("Invalid --limit value, ignoring")

    contacts = get_cto_contacts(limit)
    print(f"Found {len(contacts)} CTO/technical contacts")

    if dry_run:
        for c in contacts:
            print(f"  {c['name']} <{c['email']}> — {c['role']} @ {c['company']}")
        return

    sent = 0
    for c in contacts:
        subject = subject_for(c)
        body = body_for(c)
        ok = send_email(
            c["email"],
            subject,
            body,
            company_name=c["company"],
            category="targeted-cto",
        )
        if ok:
            sent += 1

    print(f"Targeted outreach complete: sent {sent}/{len(contacts)}")


if __name__ == "__main__":
    main()
