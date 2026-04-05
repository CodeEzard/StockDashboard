FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
ENV PYTHONPATH=/app
CMD ["/bin/sh", "-c", "python backend/mock_data.py && python backend/migrate_mock_to_stockdata.py && uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]