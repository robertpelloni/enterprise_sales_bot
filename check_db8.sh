#!/bin/bash
echo "=== NEW DEALS UPDATED_AT ==="
su - postgres -c "psql -d sales_bot -c \"SELECT d.id, c.name, d.current_state, d.cadence_step, d.updated_at FROM deals d JOIN companies c ON d.company_id = c.id WHERE d.id > 3450 AND d.cadence_step = 0 ORDER BY d.updated_at DESC LIMIT 10;\""
echo "=== CADENCE STEP 0 COUNT ==="
su - postgres -c "psql -d sales_bot -c \"SELECT COUNT(*) FROM deals WHERE cadence_step = 0 AND current_state = 'Researched';\""
echo "=== LAST CADENCE RUN ==="
su - postgres -c "psql -d sales_bot -c \"SELECT MAX(updated_at) FROM deals WHERE cadence_step > 0;\""
