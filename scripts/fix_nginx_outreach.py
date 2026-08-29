#!/usr/bin/env python3
"""Fix the nginx location block for /dashboard/outreach on the server."""

import sys

CONFIG = "/etc/nginx/sites-enabled/hypernexus.site"

OLD = """    # Dashboard
t# Outreach dashboard (Go agent)
\tlocation = /dashboard/outreach {
\t\tproxy_pass http://127.0.0.1:8084;
\t\tproxy_set_header Host ;
\t\tproxy_set_header X-Real-IP ;
\t}
    location /dashboard {"""

NEW = """    # Dashboard
    # Outreach dashboard (Go agent)
    location = /dashboard/outreach {
        proxy_pass http://127.0.0.1:8084;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    location /dashboard {"""


def main():
    try:
        with open(CONFIG, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print("config not found")
        sys.exit(1)

    if OLD in content:
        content = content.replace(OLD, NEW)
        with open(CONFIG, "w") as f:
            f.write(content)
        print("fixed")
    else:
        print("pattern not found — checking current state")
        print(content[:2000])


if __name__ == "__main__":
    main()
