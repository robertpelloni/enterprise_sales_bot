#!/bin/bash
# Website Backup Script
# Backs up all websites to /opt/backups/

set -e

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/websites_${DATE}"

echo "Creating backup: ${BACKUP_DIR}"
mkdir -p "${BACKUP_DIR}"

# Backup HyperNexus
echo "Backing up hypernexus.site..."
cp -r /var/www/hypernexus.site "${BACKUP_DIR}/hypernexus_site"

# Backup TormentNexus
echo "Backing up tormentnexus.site..."
cp -r /var/www/tormentnexus.site "${BACKUP_DIR}/tormentnexus_site"

# Backup Cloud HyperNexus
echo "Backing up cloud.hypernexus.site..."
cp -r /var/www/cloud.hypernexus.site "${BACKUP_DIR}/cloud_hypernexus"

# Backup nginx configs
echo "Backing up nginx configs..."
cp -r /etc/nginx/sites-enabled "${BACKUP_DIR}/nginx_configs"

# Create tarball
echo "Creating tarball..."
tar -czf "${BACKUP_DIR}.tar.gz" -C /opt/backups "websites_${DATE}"
rm -rf "${BACKUP_DIR}"

# Calculate size
SIZE=$(du -sh "${BACKUP_DIR}.tar.gz" | cut -f1)
echo "Backup complete: ${BACKUP_DIR}.tar.gz (${SIZE})"

# Clean up old backups (keep last 7 days)
echo "Cleaning old backups..."
find /opt/backups -name "websites_*.tar.gz" -mtime +7 -delete 2>/dev/null || true

echo "Done!"
