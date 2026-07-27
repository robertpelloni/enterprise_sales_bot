#!/bin/bash
echo "=== TEMPLATES ==="
su - postgres -c "psql -d sales_bot -c \"SELECT id, name, channel FROM templates;\""
echo ""
echo "=== DEALS BY CADENCE STEP ==="
su - postgres -c "psql -d sales_bot -c \"SELECT cadence_step, COUNT(*) FROM deals WHERE current_state IN ('Researched', 'Outreach_Sent', 'Engaged') GROUP BY cadence_step ORDER BY cadence_step;\""
echo ""
echo "=== DEALS AT STEP 3+ (ready for LinkedIn) ==="
su - postgres -c "psql -d sales_bot -c \"SELECT COUNT(*) FROM deals WHERE cadence_step >= 3 AND current_state IN ('Researched', 'Outreach_Sent', 'Engaged');\""
