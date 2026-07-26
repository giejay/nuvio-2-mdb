FROM python:3.12-slim

# Set working directory inside container
WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir requests

# Copy script into the container
COPY sync_nuvio_to_mdblist.py .

# Run the script
CMD ["python", "-u", "sync_nuvio_to_mdblist.py"]
