#!/bin/bash
echo "=== FIRST 10 DEALS BY CADENCE ORDER ==="
su - postgres -c "psql -d sales_bot -c \"SELECT DISTINCT d.id, d.cadence_step, d.current_state FROM deals d JOIN companies c ON d.company_id = c.id JOIN contacts co ON co.company_id = c.id WHERE d.current_state IN ('Researched', 'Outreach_Sent', 'Engaged') AND co.email IS NOT NULL AND co.email != '' ORDER BY d.cadence_step ASC, d.updated_at ASC LIMIT 10;\""
echo "=== STEP 0 DEALS COUNT ==="
su - postgres -c "psql -d sales_bot -c \"SELECT COUNT(DISTINCT d.id) FROM deals d JOIN companies c ON d.company_id = c.id JOIN contacts co ON co.company_id = c.id WHERE d.current_state = 'Researched' AND d.cadence_step = 0 AND co.email IS NOT NULL AND co.email != '';\""
