#!/bin/bash
echo "=== MARKETING AGENT CAPABILITIES ==="
journalctl -u marketing-agent | grep -iE "Initializing|started|configured" | tail -15

echo ""
echo "=== OUTREACH STATS (24h) ==="
echo "Emails sent: $(journalctl -u marketing-agent --since '24 hours ago' | grep -c 'Email sent')"
echo "New leads: $(journalctl -u marketing-agent --since '24 hours ago' | grep -c 'New lead discovered')"
echo "Blog posts: $(journalctl -u marketing-agent --since '24 hours ago' | grep -c 'Published')"
echo "GitHub outreach: $(journalctl -u marketing-agent --since '24 hours ago' | grep -c 'GitHub.*comment')"
echo "Cadence runs: $(journalctl -u marketing-agent --since '24 hours ago' | grep -c 'CadenceAware')"

echo ""
echo "=== STRIPE ACTIVITY ==="
journalctl -u marketing-agent --since '24 hours ago' | grep -iE "checkout|subscription|payment" | tail -5

echo ""
echo "=== WHAT COULD BE RUNNING ==="
echo "1. tormentnexus-bot: $(systemctl is-active tormentnexus-bot 2>/dev/null)"
echo "2. Twitter bot: $(journalctl -u marketing-agent | grep -c 'Twitter')"
echo "3. LinkedIn outreach: $(journalctl -u marketing-agent | grep -c 'LinkedIn')"
echo "4. Reddit posting: $(journalctl -u marketing-agent | grep -c 'Reddit')"
