# Backup notes (MVP)

Minimum acceptable:
- Nightly Postgres dump (pg_dump -Fc)
- Nightly MinIO volume snapshot (minio_data)
- Copy backups offsite

You can later replace MinIO snapshot with bucket replication if needed.
