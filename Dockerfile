FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
ENV PYTHONPATH=/app
CMD ["/bin/sh", "-c", "python backend/data_collector.py && uvicorn backend.main:app --host 0.0.0.0 --port 8000"]