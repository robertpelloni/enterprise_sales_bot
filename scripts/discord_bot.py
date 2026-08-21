#!/usr/bin/env python3
"""Discord Bot for HyperNexus Community"""
import os
import json
import urllib.request
from datetime import datetime

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
DISCORD_GUILD_ID = os.environ.get("DISCORD_GUILD_ID", "")
DISCORD_CHANNEL_ID = os.environ.get("DISCORD_CHANNEL_ID", "")

def send_message(channel_id, content):
    """Send a message to a Discord channel."""
    if not DISCORD_BOT_TOKEN:
        print("[Discord] No bot token configured")
        return False
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    data = json.dumps({"content": content}).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json",
    })
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        print(f"[Discord] Error: {e}")
        return False

def post_update(message):
    """Post an update to the community channel."""
    return send_message(DISCORD_CHANNEL_ID, message)

if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("DISCORD_BOT_TOKEN not set.")
        print("Setup guide: https://discord.com/developers/applications")
    else:
        print(f"Discord bot configured for guild {DISCORD_GUILD_ID}")
        send_message(DISCORD_CHANNEL_ID, "Bot online!")
