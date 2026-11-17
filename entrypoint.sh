#!/bin/sh
set -e

# Standard 5-field cron expression. Default: every day at 00:00.
CRON_SCHEDULE="${CRON_SCHEDULE:-0 0 * * *}"

# cron jobs don't inherit the container environment, so dump it to a file
# that the job sources before running the script.
export -p > /app/env.sh
chmod 600 /app/env.sh

# Write the cron job. Output goes to PID 1's stdout/stderr so it shows up in `docker logs`.
echo "${CRON_SCHEDULE} root . /app/env.sh; cd /app && /usr/local/bin/python -u sync_nuvio_to_mdblist.py > /proc/1/fd/1 2>&1" > /etc/cron.d/nuvio-sync
chmod 0644 /etc/cron.d/nuvio-sync

echo "Cron schedule: ${CRON_SCHEDULE}"

# Run once on startup, then hand over to cron.
python -u /app/sync_nuvio_to_mdblist.py || true

exec cron -f
