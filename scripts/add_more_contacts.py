#!/usr/bin/env python3
"""Add more tech company contacts to the database"""
import requests
import psycopg2
import time

HUNTER_API_KEY = "6d2e42cff14189b3c2453e8e4155efa27e1f02b2"
DATABASE_URL = "postgres://sales_bot:tormentnexus2026@localhost:5432/sales_bot"

# Additional tech domains to search
TECH_DOMAINS = [
    "uipath.com", "automationanywhere.com", "palantir.com", "c3.ai",
    "dataiku.com", "alteryx.com", "tableau.com", "looker.com",
    "sumologic.com", "grafana.com", "pagerduty.com", "launchdarkly.com",
    "segment.com", "amplitude.com", "mixpanel.com", "heap.io",
    "fullstory.com", "hotjar.com", "optimizely.com", "split.io",
    "shopify.com", "spotify.com", "netflix.com", "twitter.com",
    "linkedin.com", "pinterest.com", "reddit.com", "discord.com",
    "calendly.com", "typeform.com", "grammarly.com", "1password.com",
    "nordvpn.com", "protonmail.com", "notion.so", "airtable.com",
    "figma.com", "canva.com", "miro.com", "loom.com"
]

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    new_contacts = 0
    total_searched = 0
    
    for domain in TECH_DOMAINS:
        try:
            resp = requests.get(
                "https://api.hunter.io/v2/domain-search",
                params={"domain": domain, "api_key": HUNTER_API_KEY, "limit": 10, "type": "personal"},
                timeout=15
            )
            
            if resp.status_code == 200:
                emails = resp.json().get("data", {}).get("emails", [])
                total_searched += 1
                
                for e in emails:
                    email = e.get("value", "")
                    role = (e.get("position", "") or "").lower()
                    
                    # Look for purchasing-related roles
                    purchasing_keywords = ["purchas", "procure", "vendor", "sourc", "buyer", "acquisition", "it ", "software"]
                    if email and any(kw in role for kw in purchasing_keywords):
                        try:
                            name = (e.get("first_name", "") + " " + e.get("last_name", "")).strip()
                            cur.execute("""
                                INSERT INTO purchasing_contacts (name, email, role, company_name, company_domain, source, verified)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (email) DO NOTHING
                            """, (
                                name,
                                email,
                                e.get("position", ""),
                                domain.split(".")[0].title(),
                                domain,
                                "hunter",
                                e.get("confidence", 0) > 80
                            ))
                            
                            if cur.rowcount > 0:
                                new_contacts += 1
                                print(f"  Added: {email} - {e.get('position', '')} at {domain}")
                        except Exception as ex:
                            print(f"  Error inserting {email}: {ex}")
            
            time.sleep(1)  # Rate limiting
            
        except Exception as ex:
            print(f"  Error searching {domain}: {ex}")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"\nSearched {total_searched} domains")
    print(f"New contacts added: {new_contacts}")

if __name__ == "__main__":
    main()
