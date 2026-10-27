#!/usr/bin/env sh
# Nightly backup: Postgres dump + uploaded files. Usage: DATABASE_URL=... STORAGE_DIR=... ./backup.sh /backups
set -eu
DEST="${1:?destination directory}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$DEST"
# pg_dump understands postgresql:// URLs; strip the SQLAlchemy driver suffix.
pg_dump --format=custom --file "$DEST/db-$STAMP.dump" "$(echo "$DATABASE_URL" | sed 's/+psycopg//')"
tar -czf "$DEST/files-$STAMP.tar.gz" -C "$STORAGE_DIR" .
# Keep 14 days.
find "$DEST" -name 'db-*.dump' -mtime +14 -delete
find "$DEST" -name 'files-*.tar.gz' -mtime +14 -delete
echo "backup written to $DEST ($STAMP)"
