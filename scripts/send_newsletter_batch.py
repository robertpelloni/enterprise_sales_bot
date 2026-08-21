#!/usr/bin/env python3
import smtplib, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import psycopg2

SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = 'hypernexusofficialllc@gmail.com'
SMTP_PASS = 'amwz medv gvtu fmlj'

conn = psycopg2.connect(host='localhost', database='sales_bot', user='sales_bot', password='tormentnexus2026')
cur = conn.cursor()
cur.execute('SELECT email, name FROM contacts WHERE email IS NOT NULL AND email != %s LIMIT 542 OFFSET 10', ('',))
contacts = cur.fetchall()
cur.close()
conn.close()

with open('/opt/marketing_agent/scripts/marketing_bot/newsletter_latest.html', 'r') as f:
    html = f.read()

print(f'Sending to {len(contacts)} contacts...')
sent = 0
for email, name in contacts:
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f'HyperNexus Official <{SMTP_USER}>'
        msg['To'] = email
        msg['Subject'] = 'HyperNexus Weekly: Progressive Routing, Persistent Memory, Zero Downtime'
        msg.attach(MIMEText('Progressive tool routing cuts token usage by 60%. Read more: https://hypernexus.site', 'plain'))
        msg.attach(MIMEText(html, 'html'))
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        sent += 1
        if sent % 50 == 0:
            print(f'Progress: {sent}/{len(contacts)}')
    except Exception as e:
        print(f'Error: {e}')
    time.sleep(2)

print(f'Done! Sent: {sent}/{len(contacts)}')
