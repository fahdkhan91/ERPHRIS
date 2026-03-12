# Use Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies for Oracle and Pandas
RUN apt-get update && apt-get install -y libaio1 wget unzip && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download and Setup Oracle Instant Client (Linux)
RUN mkdir -p /opt/oracle && \
    wget https://download.oracle.com/otn_software/linux/instantclient/211000/instantclient-basiclite-linux.x64-21.1.0.0.0.zip && \
    unzip instantclient-basiclite-linux.x64-21.1.0.0.0.zip -d /opt/oracle && \
    rm instantclient-basiclite-linux.x64-21.1.0.0.0.zip

# Set Oracle environment variables
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_21_1
ENV ORACLE_HOME=/opt/oracle/instantclient_21_1

# Copy project files
COPY . .

# Start the application using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]
