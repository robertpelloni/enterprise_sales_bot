#!/usr/bin/env python3
"""
Purchasing Agent Scraper
Finds purchasing agents, procurement managers, and software buyers at tech companies.
Uses Apollo.io, Hunter.io, and web scraping to build targeted email lists.
"""

import os
import time
import requests
import psycopg2
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgres://sales_bot:tormentnexus2026@localhost:5432/sales_bot"
)
APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY", "Hk2hKzzYIddTsygrnoufDw")
HUNTER_API_KEY = os.environ.get(
    "HUNTER_API_KEY", "6d2e42cff14189b3c2453e8e4155efa27e1f02b2"
)
HERMES_API_URL = os.environ.get(
    "HERMES_API_URL", "https://token-plan-sgp.xiaomimimo.com/v1"
)
HERMES_API_KEY = os.environ.get(
    "HERMES_API_KEY", "tp-s0jae9p6m9d8pirs67549as0ewk9a1up0i1379o1kcg4u6r3"
)
HERMES_MODEL = os.environ.get("HERMES_MODEL", "mimo-v2.5")

# Target roles (purchasing-focused)
TARGET_ROLES = [
    "purchasing",
    "procurement",
    "vendor",
    "sourcing",
    "buyer",
    "purchasing agent",
    "purchasing manager",
    "procurement manager",
    "software buyer",
    "it procurement",
    "technology procurement",
    "vendor management",
    "supplier",
    "acquisition",
    "vp procurement",
    "director procurement",
    "head of procurement",
    "chief procurement",
    "cpo",
    "procurement analyst",
    "software asset",
    "it asset",
    "license management",
    "it sourcing",
    "cloud procurement",
    "saas procurement",
]

# Target company types
TARGET_INDUSTRIES = [
    "technology",
    "software",
    "saas",
    "ai",
    "machine learning",
    "fintech",
    "healthtech",
    "edtech",
    "cybersecurity",
    "cloud",
    "data",
    "analytics",
    "enterprise",
    "consulting",
    "financial services",
    "banking",
    "insurance",
    "healthcare",
    "pharmaceutical",
    "biotech",
]

# Target company sizes (employees)
TARGET_SIZES = ["51-200", "201-500", "501-1000", "1001-5000", "5001-10000", "10001+"]

# ═══════════════════════════════════════════════════════════════
# DATABASE OPERATIONS
# ═══════════════════════════════════════════════════════════════


def get_db():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL)


def init_db():
    """Initialize database tables for purchasing contacts"""
    conn = get_db()
    cur = conn.cursor()

    # Create purchasing_contacts table if not exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchasing_contacts (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            role TEXT,
            company_name TEXT,
            company_domain TEXT,
            company_size TEXT,
            company_industry TEXT,
            linkedin_url TEXT,
            phone TEXT,
            source TEXT,
            source_id TEXT,
            verified BOOLEAN DEFAULT FALSE,
            contacted BOOLEAN DEFAULT FALSE,
            contact_count INTEGER DEFAULT 0,
            last_contacted TIMESTAMP,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_purchasing_contacts_email ON purchasing_contacts(email);
        CREATE INDEX IF NOT EXISTS idx_purchasing_contacts_company ON purchasing_contacts(company_domain);
        CREATE INDEX IF NOT EXISTS idx_purchasing_contacts_role ON purchasing_contacts(role);
        CREATE INDEX IF NOT EXISTS idx_purchasing_contacts_verified ON purchasing_contacts(verified);
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("Database initialized")


def insert_contacts(contacts):
    """Insert contacts into database, skip duplicates"""
    if not contacts:
        return 0

    conn = get_db()
    cur = conn.cursor()

    inserted = 0
    for contact in contacts:
        try:
            cur.execute(
                """
                INSERT INTO purchasing_contacts 
                (name, email, role, company_name, company_domain, company_size, 
                 company_industry, linkedin_url, phone, source, source_id, verified)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (email) DO UPDATE SET
                    role = COALESCE(EXCLUDED.role, purchasing_contacts.role),
                    company_name = COALESCE(EXCLUDED.company_name, purchasing_contacts.company_name),
                    linkedin_url = COALESCE(EXCLUDED.linkedin_url, purchasing_contacts.linkedin_url),
                    updated_at = CURRENT_TIMESTAMP
            """,
                (
                    contact.get("name", ""),
                    contact.get("email", ""),
                    contact.get("role", ""),
                    contact.get("company_name", ""),
                    contact.get("company_domain", ""),
                    contact.get("company_size", ""),
                    contact.get("company_industry", ""),
                    contact.get("linkedin_url", ""),
                    contact.get("phone", ""),
                    contact.get("source", "scraper"),
                    contact.get("source_id", ""),
                    contact.get("verified", False),
                ),
            )
            inserted += 1
        except Exception as e:
            print(f"  Error inserting {contact.get('email', 'unknown')}: {e}")

    conn.commit()
    cur.close()
    conn.close()
    return inserted


def get_uncontacted_contacts(limit=50):
    """Get contacts that haven't been contacted yet"""
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, name, email, role, company_name, company_domain, company_industry
        FROM purchasing_contacts
        WHERE contacted = FALSE 
          AND email IS NOT NULL 
          AND email != ''
          AND verified = TRUE
        ORDER BY created_at DESC
        LIMIT %s
    """,
        (limit,),
    )

    contacts = []
    for row in cur.fetchall():
        contacts.append(
            {
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "role": row[3],
                "company_name": row[4],
                "company_domain": row[5],
                "company_industry": row[6],
            }
        )

    cur.close()
    conn.close()
    return contacts


def mark_contacted(contact_id):
    """Mark a contact as contacted"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE purchasing_contacts 
        SET contacted = TRUE, contact_count = contact_count + 1, last_contacted = NOW()
        WHERE id = %s
    """,
        (contact_id,),
    )
    conn.commit()
    cur.close()
    conn.close()


def get_stats():
    """Get scraping statistics"""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN email IS NOT NULL AND email != '' THEN 1 END) as with_email,
            COUNT(CASE WHEN verified = TRUE THEN 1 END) as verified,
            COUNT(CASE WHEN contacted = TRUE THEN 1 END) as contacted,
            COUNT(CASE WHEN contacted = FALSE AND verified = TRUE THEN 1 END) as ready_to_contact
        FROM purchasing_contacts
    """)

    row = cur.fetchone()
    cur.close()
    conn.close()

    return {
        "total": row[0],
        "with_email": row[1],
        "verified": row[2],
        "contacted": row[3],
        "ready_to_contact": row[4],
    }


# ═══════════════════════════════════════════════════════════════
# APOLLO.IO SCRAPER
# ═══════════════════════════════════════════════════════════════


def scrape_apollo_purchasing(limit=100):
    """Search Apollo.io for purchasing contacts at tech companies"""
    print("\n=== Apollo.io Purchasing Search ===")

    if not APOLLO_API_KEY:
        print("  No Apollo API key configured")
        return []

    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": APOLLO_API_KEY,
    }

    contacts = []

    # Search for purchasing roles at tech companies
    for role_keyword in [
        "purchasing manager",
        "procurement manager",
        "software buyer",
        "it procurement",
        "vendor management",
        "sourcing manager",
    ]:
        try:
            payload = {
                "q_organization_keyword_tags": ["technology", "software", "saas", "ai"],
                "title": role_keyword,
                "person_seniorities": ["manager", "director", "vp", "head"],
                "per_page": 25,
                "page": 1,
            }

            resp = requests.post(
                "https://api.apollo.io/v1/mixed_people/api_search",
                headers=headers,
                json=payload,
                timeout=30,
            )

            if resp.status_code == 200:
                data = resp.json()
                people = data.get("people", [])

                for person in people:
                    email = person.get("email", "")
                    if email and email != "email_not_unlocked@apollo.io":
                        contacts.append(
                            {
                                "name": f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                                "email": email,
                                "role": person.get("title", role_keyword),
                                "company_name": person.get("organization", {}).get(
                                    "name", ""
                                ),
                                "company_domain": person.get("organization", {}).get(
                                    "primary_domain", ""
                                ),
                                "company_size": person.get("organization", {}).get(
                                    "estimated_num_employees", ""
                                ),
                                "company_industry": person.get("organization", {}).get(
                                    "industry", ""
                                ),
                                "linkedin_url": person.get("linkedin_url", ""),
                                "phone": person.get("phone_numbers", [{}])[0].get(
                                    "sanitized_number", ""
                                )
                                if person.get("phone_numbers")
                                else "",
                                "source": "apollo",
                                "source_id": str(person.get("id", "")),
                                "verified": person.get("email_status") == "verified",
                            }
                        )

                print(f"  Found {len(people)} contacts for '{role_keyword}'")
            else:
                print(f"  Apollo error for '{role_keyword}': {resp.status_code}")

            time.sleep(2)  # Rate limiting

        except Exception as e:
            print(f"  Error searching Apollo for '{role_keyword}': {e}")

    print(f"  Total Apollo contacts: {len(contacts)}")
    return contacts


# ═══════════════════════════════════════════════════════════════
# HUNTER.IO SCRAPER
# ═══════════════════════════════════════════════════════════════


def scrape_hunter_purchasing(domains, limit=100):
    """Search Hunter.io for purchasing contacts at specific domains"""
    print("\n=== Hunter.io Purchasing Search ===")

    if not HUNTER_API_KEY:
        print("  No Hunter API key configured")
        return []

    contacts = []

    for domain in domains[:20]:  # Limit to 20 domains per run
        try:
            resp = requests.get(
                "https://api.hunter.io/v2/domain-search",
                params={
                    "domain": domain,
                    "api_key": HUNTER_API_KEY,
                    "limit": 10,
                    "department": "executive",  # Purchasing often under executive
                    "type": "personal",
                },
                timeout=15,
            )

            if resp.status_code == 200:
                data = resp.json().get("data", {})
                emails = data.get("emails", [])

                for email_data in emails:
                    email = email_data.get("value", "")
                    position = email_data.get("position", "") or ""

                    # Filter for purchasing-related roles
                    role_lower = position.lower()
                    is_purchasing = any(kw in role_lower for kw in TARGET_ROLES)

                    if email and (is_purchasing or not position):
                        contacts.append(
                            {
                                "name": f"{email_data.get('first_name', '')} {email_data.get('last_name', '')}".strip(),
                                "email": email,
                                "role": position,
                                "company_name": data.get("organization", ""),
                                "company_domain": domain,
                                "company_industry": data.get("industry", ""),
                                "linkedin_url": email_data.get("linkedin", ""),
                                "source": "hunter",
                                "source_id": str(email_data.get("id", "")),
                                "verified": email_data.get("confidence", 0) > 80,
                            }
                        )

                print(f"  Found {len(emails)} contacts at {domain}")
            else:
                print(f"  Hunter error for {domain}: {resp.status_code}")

            time.sleep(1)  # Rate limiting

        except Exception as e:
            print(f"  Error searching Hunter for {domain}: {e}")

    print(f"  Total Hunter contacts: {len(contacts)}")
    return contacts


# ═══════════════════════════════════════════════════════════════
# WEB SCRAPING (LinkedIn via Google)
# ═══════════════════════════════════════════════════════════════


def find_tech_companies_google():
    """Find tech company domains via Google search"""
    print("\n=== Finding Tech Company Domains ===")

    # Top tech companies that likely have purchasing departments
    tech_domains = [
        "salesforce.com",
        "hubspot.com",
        "slack.com",
        "zoom.us",
        "datadog.com",
        "snowflake.com",
        "databricks.com",
        "confluent.io",
        "twilio.com",
        "sendgrid.com",
        "stripe.com",
        "squareup.com",
        "atlassian.com",
        "github.com",
        "gitlab.com",
        "bitbucket.org",
        "docker.com",
        "kubernetes.io",
        "terraform.io",
        "hashicorp.com",
        "newrelic.com",
        "dynatrace.com",
        "splunk.com",
        "elastic.co",
        "cloudflare.com",
        "fastly.com",
        "akamai.com",
        "imperva.com",
        "paloaltonetworks.com",
        "crowdstrike.com",
        "sentinelone.com",
        "zscaler.com",
        "netskope.com",
        "illumio.com",
        "notion.so",
        "airtable.com",
        "monday.com",
        "asana.com",
        "figma.com",
        "canva.com",
        "miro.com",
        "loom.com",
        "intercom.com",
        "zendesk.com",
        "freshworks.com",
        "servicenow.com",
        "workday.com",
        "successfactors.com",
        "bamboohr.com",
        "gusto.com",
        "brex.com",
        "ramp.com",
        "bill.com",
        "coupa.com",
        "salesforce.com",
        "oracle.com",
        "sap.com",
        "microsoft.com",
        "google.com",
        "amazon.com",
        "apple.com",
        "meta.com",
        "ibm.com",
        "cisco.com",
        "vmware.com",
        "dell.com",
        "hp.com",
        "lenovo.com",
        "nvidia.com",
        "amd.com",
        "intel.com",
        "qualcomm.com",
        "broadcom.com",
        "marvell.com",
    ]

    print(f"  Found {len(tech_domains)} tech company domains")
    return tech_domains


# ═══════════════════════════════════════════════════════════════
# CONTENT GENERATION (MiMo v2.5)
# ═══════════════════════════════════════════════════════════════


def generate_email_content(contact, brand="hypernexus"):
    """Generate personalized email content using MiMo v2.5"""

    if brand == "tormentnexus":
        system_prompt = """You are a technical marketing copywriter for TormentNexus, an open-source AI control plane for developers.

Key features to highlight:
- Progressive MCP tool routing (95% token savings)
- Persistent memory (14K+ memories survive restarts)
- LLM waterfall failover (zero downtime)
- Cross-harness parity (works with Claude Code, Cursor, Copilot, Gemini CLI, Windsurf, Kiro)
- Local-first architecture (privacy, speed, offline)
- Free for personal use, open source

Target audience: Independent developers, technologists, open-source contributors
Tone: Technical, direct, developer-friendly
Websites: https://tormentnexus.site, https://hypernexus.site
GitHub: https://github.com/MDMAtk/TormentNexus

Write a concise, informative email that provides value to the reader. Focus on technical benefits and developer experience. Keep it under 200 words."""

        user_prompt = f"""Write a personalized email for a developer/technologist at {contact.get("company_name", "a tech company")}.

Their name: {contact.get("name", "Developer")}
Their role: {contact.get("role", "Technologist")}
Their company: {contact.get("company_name", "Tech Company")}

Make it relevant to their role and company. Include a clear call-to-action to check out the GitHub repo or website."""

    else:  # hypernexus
        system_prompt = """You are an enterprise marketing copywriter for HyperNexus, the enterprise version of TormentNexus AI control plane.

Key features to highlight:
- Enterprise-grade security (SSO, RBAC, audit logs)
- Cloud-hosted with 99.9% uptime SLA
- Team collaboration and knowledge sharing
- Compliance-ready (SOC2, HIPAA, GDPR)
- Dedicated support and onboarding
- $5/seat/month for professional license

Target audience: Enterprise buyers, CTOs, VPs of Engineering, procurement managers
Tone: Professional, business-focused, ROI-oriented
Website: https://hypernexus.site
Pricing: https://hypernexus.site/pricing

Write a concise, professional email that focuses on business value and ROI. Keep it under 200 words."""

        user_prompt = f"""Write a personalized email for a procurement/business professional at {contact.get("company_name", "a technology company")}.

Their name: {contact.get("name", "Professional")}
Their role: {contact.get("role", "Procurement Manager")}
Their company: {contact.get("company_name", "Technology Company")}
Their industry: {contact.get("company_industry", "Technology")}

Make it relevant to their procurement role and company needs. Focus on cost savings, security, and team productivity. Include a clear CTA to schedule a demo or check pricing."""

    try:
        resp = requests.post(
            f"{HERMES_API_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {HERMES_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": HERMES_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 500,
                "temperature": 0.7,
            },
            timeout=30,
        )

        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            return content.strip()
        else:
            print(f"  LLM error: {resp.status_code}")
            return None

    except Exception as e:
        print(f"  LLM error: {e}")
        return None


def generate_subject_line(contact, brand="hypernexus"):
    """Generate email subject line"""
    if brand == "tormentnexus":
        subjects = [
            f"Open-source AI control plane for {contact.get('company_name', 'your team')}",
            "Save 95% on AI tool context - free for developers",
            "Persistent AI memory that survives restarts",
            "Zero-downtime LLM failover - open source",
            "One config for Claude Code, Cursor, Copilot + more",
        ]
    else:
        subjects = [
            f"Enterprise AI orchestration for {contact.get('company_name', 'your organization')}",
            "Reduce AI infrastructure costs by 60%",
            "SSO, RBAC, audit logs - enterprise AI control plane",
            "$5/seat/month - enterprise AI with SOC2 compliance",
            f"AI agent coordination for {contact.get('company_name', 'your team')}",
        ]

    import random

    return random.choice(subjects)


# ═══════════════════════════════════════════════════════════════
# EMAIL SENDING
# ═══════════════════════════════════════════════════════════════


def send_email(
    to_email,
    subject,
    body,
    from_email="hypernexusofficialllc@gmail.com",
    from_name="HyperNexus Official",
):
    """Send email via Gmail OAuth2 or SMTP"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import requests
    import base64

    # Try Gmail OAuth2 first
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN", "")
    
    if client_id and client_secret and refresh_token:
        try:
            # Get access token
            data = {
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
            resp = requests.post("https://oauth2.googleapis.com/token", data=data, timeout=10)
            if resp.status_code == 200:
                access_token = resp.json().get("access_token", "")
                
                # Build email
                msg = MIMEMultipart()
                msg["From"] = f"{from_name} <{from_email}>"
                msg["To"] = to_email
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain"))
                
                # Send via SMTP with XOAUTH2
                server = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
                server.starttls()
                
                # XOAUTH2 auth
                auth_string = f"user={from_email}\x01auth=Bearer {access_token}\x01\x01"
                auth_bytes = base64.b64encode(auth_string.encode()).decode()
                server.docmd("AUTH", "XOAUTH2 " + auth_bytes)
                
                server.send_message(msg)
                server.quit()
                print(f"  [OAUTH2] Sent to {to_email}")
                return True
        except Exception as e:
            print(f"  [OAUTH2] Failed: {e}, falling back to SMTP")
    
    # Fallback to SMTP with password
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USERNAME", from_email)
    smtp_pass = os.environ.get("SMTP_PASSWORD", "")

    if not smtp_pass:
        print(f"  [SIMULATION] Would send to {to_email}: {subject}")
        return True

    try:
        msg = MIMEMultipart()
        msg["From"] = f"{from_name} <{from_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        print(f"  [SMTP] Sent to {to_email}")
        return True

    except Exception as e:
        print(f"  Failed to send to {to_email}: {e}")
        return False


# ═══════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════


def run_scraper():
    """Main scraper loop"""
    print("=" * 60)
    print("PURCHASING AGENT SCRAPER")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Initialize database
    init_db()

    # Get tech company domains
    tech_domains = find_tech_companies_google()

    # Scrape Apollo
    apollo_contacts = scrape_apollo_purchasing(limit=100)

    # Scrape Hunter
    hunter_contacts = scrape_hunter_purchasing(tech_domains[:20], limit=100)

    # Combine and deduplicate
    all_contacts = apollo_contacts + hunter_contacts
    seen_emails = set()
    unique_contacts = []
    for contact in all_contacts:
        email = contact.get("email", "").lower()
        if email and email not in seen_emails:
            seen_emails.add(email)
            unique_contacts.append(contact)

    print(f"\nTotal unique contacts: {len(unique_contacts)}")

    # Insert into database
    inserted = insert_contacts(unique_contacts)
    print(f"Inserted into database: {inserted}")

    # Get statistics
    stats = get_stats()
    print("\n=== Database Statistics ===")
    print(f"  Total contacts: {stats['total']}")
    print(f"  With email: {stats['with_email']}")
    print(f"  Verified: {stats['verified']}")
    print(f"  Contacted: {stats['contacted']}")
    print(f"  Ready to contact: {stats['ready_to_contact']}")

    return stats


def run_email_campaign(limit=20):
    """Run email campaign for uncontacted purchasing agents"""
    print("\n" + "=" * 60)
    print("EMAIL CAMPAIGN")
    print("=" * 60)

    # Get uncontacted contacts
    contacts = get_uncontacted_contacts(limit)
    print(f"Contacts to contact: {len(contacts)}")

    if not contacts:
        print("No contacts ready for outreach")
        return

    # Determine brand based on role
    sent = 0
    for contact in contacts:
        role_lower = (contact.get("role") or "").lower()

        # Determine brand based on role
        if any(
            kw in role_lower
            for kw in ["cto", "vp", "director", "head", "chief", "ciso", "cpo"]
        ):
            brand = "hypernexus"
        elif any(
            kw in role_lower
            for kw in ["developer", "engineer", "architect", "technologist"]
        ):
            brand = "tormentnexus"
        else:
            brand = "hypernexus"  # Default to enterprise for purchasing roles

        # Generate content
        subject = generate_subject_line(contact, brand)
        body = generate_email_content(contact, brand)

        if not body:
            print(f"  Skipping {contact['email']} - content generation failed")
            continue

        # Send email
        if send_email(contact["email"], subject, body):
            mark_contacted(contact["id"])
            sent += 1

        time.sleep(5)  # Rate limiting

    print(f"\nEmails sent: {sent}/{len(contacts)}")


# ═══════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Purchasing Agent Scraper & Email Campaign"
    )
    parser.add_argument(
        "--scrape", action="store_true", help="Run scraper to find purchasing contacts"
    )
    parser.add_argument("--campaign", action="store_true", help="Run email campaign")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument(
        "--limit", type=int, default=20, help="Limit contacts per campaign run"
    )
    parser.add_argument(
        "--all", action="store_true", help="Run both scraper and campaign"
    )

    args = parser.parse_args()

    if args.stats:
        init_db()
        stats = get_stats()
        print("\n=== Database Statistics ===")
        print(f"  Total contacts: {stats['total']}")
        print(f"  With email: {stats['with_email']}")
        print(f"  Verified: {stats['verified']}")
        print(f"  Contacted: {stats['contacted']}")
        print(f"  Ready to contact: {stats['ready_to_contact']}")
    elif args.scrape:
        run_scraper()
    elif args.campaign:
        run_email_campaign(args.limit)
    elif args.all:
        run_scraper()
        run_email_campaign(args.limit)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
