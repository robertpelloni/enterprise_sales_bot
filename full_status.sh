#!/bin/bash
echo "=========================================="
echo "       FULL SYSTEM STATUS REPORT"
echo "=========================================="
echo ""

echo "=== SERVER ==="
echo "Hostname: $(hostname)"
echo "Uptime: $(uptime -p)"
echo "Disk: $(df -h / | tail -1 | awk '{print $3 "/" $2 " (" $5 " used)"}')"
echo ""

echo "=== SERVICES ==="
for svc in marketing-agent tormentnexus postgresql nginx ollama; do
	status=$(systemctl is-active $svc 2>/dev/null)
	echo "  $svc: $status"
done
echo ""

echo "=== WEBSITES ==="
for url in "https://hypernexus.site/" "https://cloud.hypernexus.site/" "https://tormentnexus.site/"; do
	code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
	echo "  $code $url"
done
echo ""

echo "=== MARKETING AGENT (24h stats) ==="
echo "  Emails sent: $(journalctl -u marketing-agent --since '24 hours ago' 2>/dev/null | grep -c 'Email sent')"
echo "  New leads: $(journalctl -u marketing-agent --since '24 hours ago' 2>/dev/null | grep -c 'New lead discovered')"
echo "  Blog posts: $(journalctl -u marketing-agent --since '24 hours ago' 2>/dev/null | grep -c 'Published')"
echo "  GitHub comments: $(journalctl -u marketing-agent --since '24 hours ago' 2>/dev/null | grep -c 'GitHub.*comment')"
echo "  LinkedIn messages: $(journalctl -u marketing-agent --since '24 hours ago' 2>/dev/null | grep -ic 'linkedin')"
echo "  Cadence runs: $(journalctl -u marketing-agent --since '24 hours ago' 2>/dev/null | grep -c 'CadenceAware')"
echo "  Stripe checkouts: $(journalctl -u marketing-agent --since '24 hours ago' 2>/dev/null | grep -c 'checkout')"
echo ""

echo "=== DATABASE ==="
su - postgres -c "psql -d sales_bot -t -c \"SELECT 'Contacts: ' || COUNT(*) FROM contacts;\""
su - postgres -c "psql -d sales_bot -t -c \"SELECT 'Deals: ' || COUNT(*) FROM deals;\""
su - postgres -c "psql -d sales_bot -t -c \"SELECT current_state || ': ' || COUNT(*) FROM deals GROUP BY current_state ORDER BY COUNT(*) DESC;\""
echo ""

echo "=== CADENCE STEPS ==="
su - postgres -c "psql -d sales_bot -t -c \"SELECT 'Step ' || cadence_step || ': ' || COUNT(*) FROM deals WHERE current_state IN ('Researched','Outreach_Sent','Engaged') GROUP BY cadence_step ORDER BY cadence_step;\""
echo ""

echo "=== MARKETING AGENT CAPABILITIES ==="
echo "  SMTP: $(journalctl -u marketing-agent | grep -c 'Initializing SMTP sender' | xargs -I{} echo '{} times initialized')"
echo "  IMAP: $(journalctl -u marketing-agent | grep -c 'IMAP receiver started' | xargs -I{} echo '{} times started')"
echo "  LinkedIn: $(journalctl -u marketing-agent | grep -c 'LinkedIn credentials configured' | xargs -I{} echo '{} times configured')"
echo "  BlogEngine: $(journalctl -u marketing-agent | grep -c 'Auto-blog generator started' | xargs -I{} echo '{} times started')"
echo "  SocialPoster: $(journalctl -u marketing-agent | grep -c 'Social media posting' | xargs -I{} echo '{} times started')"
echo ""

echo "=== RECENT ACTIVITY (1 hour) ==="
journalctl -u marketing-agent --since '1 hour ago' 2>/dev/null | grep -iE "sent|published|discovered|checkout|linkedin|email" | tail -10
echo ""

echo "=== WHAT'S NOT RUNNING ==="
echo "  tormentnexus-bot: $(systemctl is-active tormentnexus-bot 2>/dev/null) (disabled - dead binary)"
echo "  Twitter bot: $(journalctl -u marketing-agent | grep -c 'Twitter' | xargs -I{} echo '{} references (402 credits depleted)')"
echo ""

echo "=== BLOCKERS ==="
echo "  Apollo API: Fixed (v1/mixed_people/search)"
echo "  GitHub API: Working (timeouts on some searches)"
echo "  Twitter API: 402 credits depleted"
echo "  Disk: $(df -h / | tail -1 | awk '{print $5}') used"
echo ""
