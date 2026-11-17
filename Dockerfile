FROM python:3.12-slim

# Set working directory inside container
WORKDIR /app

# Install cron and python dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends cron \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir requests

# Copy script and entrypoint into the container
COPY sync_nuvio_to_mdblist.py entrypoint.sh ./
RUN chmod +x /app/entrypoint.sh

# Schedule (standard 5-field cron expression), override with -e CRON_SCHEDULE or in .env
ENV CRON_SCHEDULE="0 0 * * *"

# Runs the sync once on start, then keeps cron running in the foreground
CMD ["/app/entrypoint.sh"]
