#!/bin/bash
echo "=== Fixing deal states ==="
su - postgres -c "psql -d sales_bot -c \"UPDATE deals SET current_state = 'Researched', updated_at = NOW() WHERE current_state = 'Discovered' AND cadence_step = 0;\""
echo "=== New state distribution ==="
su - postgres -c "psql -d sales_bot -c \"SELECT current_state, COUNT(*) FROM deals GROUP BY current_state ORDER BY COUNT(*) DESC;\""
echo "=== Researched with contacts ==="
su - postgres -c "psql -d sales_bot -c \"SELECT COUNT(DISTINCT d.id) FROM deals d JOIN companies c ON d.company_id = c.id JOIN contacts co ON co.company_id = c.id WHERE d.current_state = 'Researched' AND d.cadence_step = 0 AND co.email != '';\""
