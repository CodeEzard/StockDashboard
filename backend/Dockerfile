FROM python:3.11-slim
WORKDIR /app
# Update system and install CA certificates for SSL
RUN apt-get update && \
	apt-get install -y --no-install-recommends ca-certificates curl && \
	update-ca-certificates && \
	rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
# Upgrade pip and install requirements
RUN pip install --upgrade pip && \
	pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
# Copy the pre-populated stocks.db to /app/stocks.db
COPY backend/stocks.db ./stocks.db
ENV PYTHONPATH=/app
# Set CA bundle env vars for yfinance/curl_cffi SSL fix
ENV CURL_CA_BUNDLE=/usr/local/lib/python3.11/site-packages/certifi/cacert.pem
ENV SSL_CERT_FILE=/usr/local/lib/python3.11/site-packages/certifi/cacert.pem
	# Run mock data and migration scripts before starting the backend
CMD ["/bin/sh", "-c", "python backend/mock_data.py && python backend/migrate_mock_to_stockdata.py && uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
# Run mock data and migration scripts before starting the backend (will append if already present)