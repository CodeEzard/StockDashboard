# Stock Dashboard

A simple stock dashboard with FastAPI backend and static frontend.

## Backend
- FastAPI for API
- yfinance for stock data
- SQLAlchemy + SQLite for storage

## Frontend
- Static HTML (placeholder)

## Setup
1. Install requirements: `pip install -r requirements.txt`
2. Run data collector: `python backend/data_collector.py`
3. Start backend: `uvicorn backend.main:app --reload`
4. Open `frontend/index.html` in browser

---

## 🚀 Docker & Deployment

### Build and Run Locally with Docker

```bash
# Build the backend image
cd backend
docker build -t stock-dashboard-backend .

# Run with SQLite DB volume
cd ..
docker-compose up
```

- Backend will be available at http://localhost:8000
- SQLite DB is persisted via volume mount.

### 🌐 Deploy Free on Render.com

1. Push your repo to GitHub
2. Go to [Render.com](https://render.com/)
3. Create a new Web Service from your repo
4. Use the included `render.yaml` (auto-detected)
5. Health check path: `/companies`
6. Set environment variable: `PORT=8000`
7. Deploy!

**Live Demo:**
> _Paste your Render.com link here after deploy_

---

**Pro Tips:**
- Render.com free tier: no credit card needed
- Add your live link above for maximum impact
- `.dockerignore` included for smaller, faster builds
- ML feature: Linear Regression price prediction with confidence band
- Professional UI, fintech color scheme, and real-time data
