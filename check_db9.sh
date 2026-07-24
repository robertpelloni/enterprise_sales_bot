#!/bin/bash
echo "=== RESERCHED DEALS WITH CONTACTS (first 10) ==="
su - postgres -c "psql -d sales_bot -c \"SELECT d.id, c.name, d.cadence_step, d.updated_at, co.email FROM deals d JOIN companies c ON d.company_id = c.id JOIN contacts co ON co.company_id = c.id WHERE d.current_state = 'Researched' AND co.email IS NOT NULL AND co.email != '' ORDER BY d.updated_at DESC LIMIT 10;\""
echo "=== STEP 0 DEALS WITH CONTACTS ==="
su - postgres -c "psql -d sales_bot -c \"SELECT COUNT(*) FROM deals d JOIN companies c ON d.company_id = c.id JOIN contacts co ON co.company_id = c.id WHERE d.current_state = 'Researched' AND d.cadence_step = 0 AND co.email IS NOT NULL AND co.email != '';\""
