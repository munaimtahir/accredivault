#!/usr/bin/env sh
set -eu

mkdir -p /app/logs

TMP_LOG="/tmp/compliance_daily_$(date +%s).log"
set +e
python manage.py recompute_control_statuses --latest > "$TMP_LOG" 2>&1
status=$?
set -e

cat "$TMP_LOG" >> /app/logs/compliance_daily.log
rm -f "$TMP_LOG"

exit "$status"
