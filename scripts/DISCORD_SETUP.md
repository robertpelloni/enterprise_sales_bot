# Discord Community Setup Guide

## Step 1: Create Discord Application

1. Go to https://discord.com/developers/applications
2. Click "New Application"
3. Name it "HyperNexus"
4. Click "Create"

## Step 2: Create Bot

1. Go to "Bot" tab
2. Click "Reset Token" to get your bot token
3. Copy the token (you'll need it later)
4. Enable these intents:
   - MESSAGE CONTENT INTENT
   - SERVER MEMBERS INTENT
   - PRESENCE INTENT

## Step 3: Generate Invite URL

1. Go to "OAuth2" -> "URL Generator"
2. Select scopes:
   - bot
   - applications.commands
3. Select permissions:
   - Send Messages
   - Embed Links
   - Read Message History
   - Add Reactions
   - Use Slash Commands
4. Copy the generated URL

## Step 4: Create Server & Invite Bot

1. Create a new Discord server called "HyperNexus Community"
2. Create channels:
   - #announcements
   - #general
   - #support
   - #feature-requests
   - #showcase
3. Open the invite URL from Step 3
4. Select your server and authorize

## Step 5: Configure Environment

Add to /opt/marketing_agent/.env:


To get IDs:
1. Enable Developer Mode in Discord (Settings -> Advanced -> Developer Mode)
2. Right-click server -> Copy Server ID
3. Right-click channel -> Copy Channel ID

## Step 6: Test Bot



## Step 7: Add to Marketing Agent

The bot will automatically post:
- New blog articles
- Release announcements
- Community updates
- Feature highlights

## Channels Structure



## Bot Commands (Future)

- /help - Show available commands
- /docs - Link to documentation
- /status - System status
- /blog - Latest blog posts
- /pricing - Pricing information
