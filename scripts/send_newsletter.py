#!/usr/bin/env python3
"""Send newsletter to remaining contacts"""
import os
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import psycopg2

SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = 'hypernexusofficialllc@gmail.com'
SMTP_PASS = 'amwz medv gvtu fmlj'
FROM_NAME = 'HyperNexus Official'

def get_contacts(limit=552):
    conn = psycopg2.connect(host='localhost', database='sales_bot', user='sales_bot', password='tormentnexus2026')
    cur = conn.cursor()
    cur.execute('SELECT email, name FROM contacts WHERE email IS NOT NULL AND email != %s LIMIT %s', ('', limit))
    contacts = cur.fetchall()
    cur.close()
    conn.close()
    return contacts

def send_newsletter(contact_email, contact_name, html_content):
    msg = MIMEMultipart('alternative')
    msg['From'] = f'{FROM_NAME} <{SMTP_USER}>'
    msg['To'] = contact_email
    msg['Subject'] = 'HyperNexus Weekly: Progressive Routing, Persistent Memory, Zero Downtime'
    text = 'HyperNexus Weekly - Progressive tool routing cuts token usage by 60%. Read more: https://hypernexus.site'
    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html_content, 'html'))
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f'Error: {e}')
        return False

def main():
    with open('/opt/marketing_agent/scripts/marketing_bot/newsletter_latest.html', 'r') as f:
        html_content = f.read()
    contacts = get_contacts(552)
    print(f'Sending to {len(contacts)} contacts...')
    sent = 0
    for email, name in contacts:
        if send_newsletter(email, name, html_content):
            sent += 1
            print(f'[{sent}] Sent to {email}')
        time.sleep(2)
    print(f'Done! Sent: {sent}/{len(contacts)}')

if __name__ == '__main__':
    main()
