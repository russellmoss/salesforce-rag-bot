# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and Salesforce CLI
RUN apt-get update && apt-get install -y curl xz-utils && \
    curl -sS https://developer.salesforce.com/media/salesforce-cli/sf/channels/stable/sf-linux-x64.tar.xz -o sf.tar.xz && \
    mkdir -p /usr/local/sf && tar -xf sf.tar.xz -C /usr/local/sf --strip-components=1 && \
    ln -s /usr/local/sf/sf /usr/local/bin/sf && \
    rm sf.tar.xz && apt-get remove -y curl xz-utils && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy pipeline script
COPY src/pipeline/build_schema_library_end_to_end.py .

# Make script executable
RUN chmod +x build_schema_library_end_to_end.py

# Set entrypoint
ENTRYPOINT ["python", "./build_schema_library_end_to_end.py"]
