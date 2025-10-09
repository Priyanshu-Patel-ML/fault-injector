# Use official Airflow image
FROM apache/airflow:2.10.2-python3.11

USER root

# Install curl and other dependencies + PostgreSQL client tools + iproute2 for tc
RUN apt-get update && \
    apt-get install -y curl ca-certificates apt-transport-https lsb-release gnupg tar \
    postgresql-client postgresql-contrib sudo iproute2 && \
    rm -rf /var/lib/apt/lists/*

# Install Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Install kubectl (latest stable)
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
    rm kubectl

# Install k6 binary (latest stable)
RUN curl -sL https://github.com/grafana/k6/releases/download/v0.46.0/k6-v0.46.0-linux-amd64.tar.gz \
    | tar -xz -C /usr/local/bin --strip-components=1 k6-v0.46.0-linux-amd64/k6

# Switch back to airflow user
USER airflow

# Copy experiment-apis folder first (before pip install)
COPY experiment-apis/ /opt/airflow/experiment-apis/

# Install Chaos Toolkit + All Extensions + Flask dependencies from requirements.txt
RUN pip install --no-cache-dir \
        chaostoolkit \
        chaostoolkit-kubernetes \
        chaostoolkit-k6 \
        kubernetes \
        dag-factory \
        psycopg2-binary \
        redis \
        pymongo && \
    pip install --no-cache-dir -r /opt/airflow/experiment-apis/requirements.txt

# Create src directory structure (if not mounted from host)
RUN mkdir -p /opt/airflow/src/pod /opt/airflow/src/node

# Switch back to airflow user
USER airflow

# Set Python path to include src directory
ENV PYTHONPATH="/opt/airflow/src/pod:/opt/airflow/src/node:${PYTHONPATH}"

# Copy experiment-apis folder
COPY experiment-apis/ /opt/airflow/experiment-apis/
