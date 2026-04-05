
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import StockData
from backend.mock_data import SYMBOLS
from sqlalchemy import func, desc, asc
from datetime import datetime, timedelta
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

app = FastAPI()
class PredictionPoint(BaseModel):
    day: int
    date: str
    predicted: float
    lower: float
    upper: float

class PredictionResponse(BaseModel):
    symbol: str
    predictions: list[PredictionPoint]

@app.get("/predict/{symbol}", response_model=PredictionResponse, status_code=200)
def predict_prices(symbol: str, days: int = Query(14, gt=0, le=30)):
    """Predict next N days of closing prices using linear regression. Returns ±1 stddev confidence band."""
    session = SessionLocal()
    q = (
        session.query(StockData)
        .filter(StockData.symbol == symbol)
        .order_by(desc(StockData.date))
        .limit(90)
    )
    rows = q.all()
    session.close()
    if not rows or len(rows) < 30:
        raise HTTPException(status_code=404, detail="Not enough data for prediction")
    # Reverse to chronological order
    rows = list(reversed(rows))
    closes = np.array([r.close for r in rows])
    X = np.arange(len(closes)).reshape(-1, 1)
    y = closes
    model = LinearRegression()
    model.fit(X, y)
    preds = []
    # Residuals stddev for confidence
    y_pred = model.predict(X)
    stddev = float(np.std(y - y_pred))
    last_date = rows[-1].date
    for i in range(1, days+1):
        day_idx = len(closes) + i - 1
        pred = float(model.predict(np.array([[day_idx]]))[0])
        pred_date = (last_date + timedelta(days=i)).strftime('%Y-%m-%d')
        preds.append(PredictionPoint(
            day=i,
            date=pred_date,
            predicted=pred,
            lower=pred - stddev,
            upper=pred + stddev
        ))
    return PredictionResponse(symbol=symbol, predictions=preds)

# Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

COMPANY_NAMES = {
    "TCS.NS": "Tata Consultancy Services",
    "INFY.NS": "Infosys",
    "RELIANCE.NS": "Reliance Industries",
    "HDFCBANK.NS": "HDFC Bank",
    "WIPRO.NS": "Wipro"
}

class CompanyInfo(BaseModel):
    symbol: str
    name: str

class OHLCVData(BaseModel):
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    daily_return: Optional[float] = None
    ma_7: Optional[float] = None
    ma_30: Optional[float] = None

class SummaryData(BaseModel):
    symbol: str
    week52_high: float
    week52_low: float
    avg_close: float
    current_price: float
    volatility_score: float
    momentum_score: float
    pct_change_30d: float

class CompareData(BaseModel):
    date: datetime
    symbol1: float
    symbol2: float

class TopMover(BaseModel):
    symbol: str
    name: str
    daily_return: float

class TopMoversResponse(BaseModel):
    gainers: List[TopMover]
    losers: List[TopMover]

## Removed startup event that could trigger yfinance/data_collector. Only mock data is used. No yfinance/data_collector code remains.


@app.get("/companies", response_model=List[CompanyInfo], status_code=200)
def get_companies():
    """List all stock symbols and company names."""
    return [CompanyInfo(symbol=s, name=COMPANY_NAMES.get(s, s)) for s in SYMBOLS]


@app.get("/data/{symbol}", response_model=List[OHLCVData], status_code=200)
def get_data(symbol: str, days: int = Query(30, gt=0, le=180)):
    """Get OHLCV + daily_return + ma_7 + ma_30 for N days."""
    session = SessionLocal()
    q = (
        session.query(StockData)
        .filter(StockData.symbol == symbol)
        .order_by(desc(StockData.date))
        .limit(days + 30)
    )
    rows = q.all()
    session.close()
    if not rows:
        raise HTTPException(status_code=404, detail="Symbol not found or no data")
    # Reverse to chronological order
    rows = list(reversed(rows))
    # Calculate daily_return, ma_7, and ma_30
    closes = [r.close for r in rows]
    opens = [r.open for r in rows]
    ma_7 = pd.Series(closes).rolling(window=7).mean().tolist()
    ma_30 = pd.Series(closes).rolling(window=30).mean().tolist()
    daily_return = [(c - o) / o if o else None for c, o in zip(closes, opens)]

    # Trim back to requested days
    rows = rows[-days:]
    ma_7 = ma_7[-days:]
    ma_30 = ma_30[-days:]
    daily_return = daily_return[-days:]

    return [OHLCVData(
        date=r.date,
        open=r.open,
        high=r.high,
        low=r.low,
        close=r.close,
        volume=r.volume,
        daily_return=daily_return[i],
        ma_7=ma_7[i],
        ma_30=ma_30[i]
    ) for i, r in enumerate(rows)]


@app.get("/summary/{symbol}", response_model=SummaryData, status_code=200)
def get_summary(symbol: str):
    """Get 52w high/low, avg close, current price, volatility, momentum, % change from 30d ago."""
    session = SessionLocal()
    q = (
        session.query(StockData)
        .filter(StockData.symbol == symbol)
        .order_by(desc(StockData.date))
        .limit(252)
    )
    rows = q.all()
    session.close()
    if not rows or len(rows) < 2:
        raise HTTPException(status_code=404, detail="Not enough data")
    closes = [r.close for r in rows]
    week52_high = max(closes)
    week52_low = min(closes)
    avg_close = sum(closes) / len(closes)
    current_price = closes[0]
    # Volatility: 30-day std of daily_return * 100
    daily_returns = [(closes[i] - rows[i].open) / rows[i].open if rows[i].open else 0 for i in range(min(30, len(rows)))]
    volatility_score = float(pd.Series(daily_returns).std() * 100)
    # Momentum: (close / close.shift(30) - 1) * 100
    momentum_score = ((closes[0] / closes[29]) - 1) * 100 if len(closes) > 30 else 0
    pct_change_30d = ((closes[0] / closes[29]) - 1) * 100 if len(closes) > 30 else 0
    return SummaryData(
        symbol=symbol,
        week52_high=week52_high,
        week52_low=week52_low,
        avg_close=avg_close,
        current_price=current_price,
        volatility_score=volatility_score,
        momentum_score=momentum_score,
        pct_change_30d=pct_change_30d
    )


@app.get("/compare", response_model=List[CompareData], status_code=200)
def compare(symbol1: str, symbol2: str):
    """Side-by-side normalized price performance (both start at 100)."""
    session = SessionLocal()
    q1 = (
        session.query(StockData)
        .filter(StockData.symbol == symbol1)
        .order_by(asc(StockData.date))
        .all()
    )
    q2 = (
        session.query(StockData)
        .filter(StockData.symbol == symbol2)
        .order_by(asc(StockData.date))
        .all()
    )
    session.close()
    if not q1 or not q2:
        raise HTTPException(status_code=404, detail="One or both symbols not found")
    # Align by date
    d1 = {r.date: r.close for r in q1}
    d2 = {r.date: r.close for r in q2}
    common_dates = sorted(set(d1.keys()) & set(d2.keys()))
    if not common_dates:
        raise HTTPException(status_code=404, detail="No overlapping dates")
    base1 = d1[common_dates[0]]
    base2 = d2[common_dates[0]]
    result = [CompareData(
        date=dt,
        symbol1=(d1[dt] / base1) * 100 if base1 else None,
        symbol2=(d2[dt] / base2) * 100 if base2 else None
    ) for dt in common_dates]
    return result


@app.get("/top-movers", response_model=TopMoversResponse, status_code=200)
def top_movers():
    """Top 3 gainers and losers by daily_return today."""
    session = SessionLocal()
    today = session.query(func.max(StockData.date)).scalar()
    if not today:
        session.close()
        raise HTTPException(status_code=404, detail="No data available")
    q = session.query(StockData).filter(StockData.date == today).all()
    session.close()
    movers = []
    for r in q:
        if r.open:
            dr = (r.close - r.open) / r.open
            movers.append({
                'symbol': r.symbol,
                'name': COMPANY_NAMES.get(r.symbol, r.symbol),
                'daily_return': dr
            })
    movers.sort(key=lambda x: x['daily_return'], reverse=True)
    gainers = [TopMover(**m) for m in movers[:3]]
    losers = [TopMover(**m) for m in movers[-3:][::-1]]
    return TopMoversResponse(gainers=gainers, losers=losers)


@app.get("/")
def read_root():
    return {"message": "Stock Dashboard Backend Running"}
