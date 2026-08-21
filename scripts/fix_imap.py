#!/usr/bin/env python3
"""
Fix IMAP OAuth2 for Gmail
Generates new app password or OAuth2 token.
"""
import os
import sys

print('=== Gmail IMAP Setup Guide ===')
print()
print('Option 1: App Password (Easiest)')
print('-' * 40)
print('1. Go to https://myaccount.google.com/apppasswords')
print('2. Sign in with pelloni.robert@gmail.com')
print('3. Select app: Mail')
print('4. Select device: Other (Custom name) -> "Marketing Agent"')
print('5. Click Generate')
print('6. Copy the 16-character password')
print('7. Update IMAP_PASSWORD in /opt/marketing_agent/.env')
print()
print('Option 2: OAuth2 (More Secure)')
print('-' * 40)
print('1. Go to https://console.cloud.google.com')
print('2. Create/select project')
print('3. Enable Gmail API')
print('4. Create OAuth2 credentials')
print('5. Add redirect URI: http://localhost:8080/callback')
print('6. Run OAuth2 flow')
print()
print('Current IMAP config:')
print(f'  Host: imap.gmail.com')
print(f'  User: pelloni.robert@gmail.com')
print(f'  Password: ***hidden***')
print()
print('After updating, restart marketing agent:')
print('  systemctl restart marketing-agent')
