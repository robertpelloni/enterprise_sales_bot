#!/usr/bin/env python3
"""Direct email sender for new contacts - bypasses cadence."""

import smtplib
import psycopg2
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DB_CONFIG = {
    "dbname": "sales_bot",
    "user": "sales_bot",
    "password": "tormentnexus2026",
    "host": "localhost",
}

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "pelloni.robert@gmail.com"
SMTP_PASS = "jnfy pwri cyam fuul"
FROM_NAME = "Robert Pelloni"

EMAIL_TEMPLATE = """Hi {name},

I noticed {company} is working on some interesting AI/ML stuff. I wanted to reach out because we've built TormentNexus — a local-first cognitive control plane that coordinates multi-agent LLM workflows, MCP tool routing, and provider failover.

Teams using similar stacks have seen 3-5x improvements in agent coordination efficiency. Key features:
- Progressive MCP tool routing (cuts context by 95%)
- LLM waterfall with automatic failover (NVIDIA → OpenRouter → Ollama)
- Dual-tier memory with 14K+ persisted memories
- Cross-harness parity across Claude Code, Cursor, Codex, Gemini CLI

Would you be open to a quick 15-minute chat this week?

Best,
Robert Pelloni
HyperNexus — The Most Powerful AI Tool For Everything
https://hypernexus.site"""

def send_emails(limit=50, dry_run=False):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Get new contacts that haven't been contacted
    cur.execute("""
        SELECT co.id, co.name, co.email, c.name as company_name
        FROM contacts co
        JOIN companies c ON co.company_id = c.id
        WHERE co.email IS NOT NULL AND co.email != ''
        AND co.email NOT LIKE '%%@github.com'
        AND co.email NOT LIKE '%%@gmail.com'
        AND NOT EXISTS (
            SELECT 1 FROM interactions i 
            WHERE i.contact_id = co.id AND i.direction = 'Outbound'
        )
        AND EXISTS (
            SELECT 1 FROM deals d 
            WHERE d.company_id = c.id 
            AND d.current_state = 'Researched' 
            AND d.cadence_step = 0
        )
        ORDER BY co.id ASC
        LIMIT %s
    """, (limit,))
    
    contacts = cur.fetchall()
    print(f"Found {len(contacts)} contacts to email")
    
    sent = 0
    failed = 0
    
    if not dry_run:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
    
    for contact_id, name, email, company in contacts:
        body = EMAIL_TEMPLATE.format(
            name=name or "there",
            company=company or "your team"
        )
        
        msg = MIMEMultipart()
        msg['From'] = f"{FROM_NAME} <{SMTP_USER}>"
        msg['To'] = email
        msg['Subject'] = f"HyperNexus for {company} — Quick Question"
        msg.attach(MIMEText(body, 'plain'))
        
        if dry_run:
            print(f"[DRY RUN] Would send to {email} ({name} at {company})")
            sent += 1
        else:
            try:
                server.sendmail(SMTP_USER, [email], msg.as_string())
                
                # Record interaction
                cur.execute("""
                    INSERT INTO interactions (contact_id, channel, direction, raw_text, summary)
                    VALUES (%s, 'email', 'Outbound', %s, 'Direct send: intro-email')
                """, (contact_id, body))
                
                # Update deal cadence step
                cur.execute("""
                    UPDATE deals SET cadence_step = 1, updated_at = NOW()
                    WHERE company_id = (SELECT company_id FROM contacts WHERE id = %s)
                    AND cadence_step = 0
                """, (contact_id,))
                
                conn.commit()
                sent += 1
                print(f"[SENT] {email} ({name} at {company})")
                time.sleep(2)  # Rate limit
            except Exception as e:
                failed += 1
                print(f"[FAIL] {email}: {e}")
                conn.rollback()
    
    if not dry_run:
        server.quit()
    
    cur.close()
    conn.close()
    
    print(f"\nDone: {sent} sent, {failed} failed")

if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    dry_run = "--dry-run" in sys.argv
    send_emails(limit=limit, dry_run=dry_run)
