import numpy as np
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

SYMBOLS = {
    "TCS.NS": 3800,
    "INFY.NS": 1500,
    "RELIANCE.NS": 2900,
    "HDFCBANK.NS": 1600,
    "WIPRO.NS": 450,
}

TRADING_DAYS = 180
VOLUME_MIN = 500_000
VOLUME_MAX = 5_000_000


def stable_seed(symbol: str) -> int:
    return int(hashlib.sha256(symbol.encode("utf-8")).hexdigest()[:8], 16)


def generate_trading_days(start_date, num_days):
    days = []
    date = start_date
    while len(days) < num_days:
        if date.weekday() < 5:  # Weekday
            days.append(date)
        date += timedelta(days=1)
    return days


def simulate_stock(symbol, start_price, trading_days):
    rng = np.random.default_rng(stable_seed(symbol))
    dates = generate_trading_days(datetime.today() - timedelta(days=365), trading_days)

    # More realistic daily dynamics
    drift = 0.00035
    vol = 0.012
    log_returns = rng.normal(drift, vol, trading_days)

    close = np.empty(trading_days)
    close[0] = float(start_price)
    for i in range(1, trading_days):
        close[i] = max(1.0, close[i - 1] * np.exp(log_returns[i]))

    # Open near previous close with small overnight gap
    overnight_gap = rng.normal(0, 0.0035, trading_days)
    open_ = np.empty(trading_days)
    open_[0] = close[0] * (1 + overnight_gap[0])
    open_[1:] = close[:-1] * (1 + overnight_gap[1:])

    # Intraday high/low around open-close envelope
    intraday_range = np.abs(rng.normal(0.006, 0.002, trading_days))
    high = np.maximum(open_, close) * (1 + intraday_range)
    low = np.minimum(open_, close) * (1 - intraday_range)
    low = np.maximum(1.0, low)

    # Symbol-specific but bounded volume profiles
    symbol_scale = {
        "RELIANCE.NS": 1.25,
        "HDFCBANK.NS": 1.15,
        "INFY.NS": 1.0,
        "TCS.NS": 0.9,
        "WIPRO.NS": 0.85,
    }.get(symbol, 1.0)
    raw_volume = rng.lognormal(mean=14.3, sigma=0.35, size=trading_days) * symbol_scale
    volume = np.clip(raw_volume, VOLUME_MIN, VOLUME_MAX).astype(int)

    open_ = np.round(open_, 2)
    high = np.round(np.maximum(high, np.maximum(open_, close)), 2)
    low = np.round(np.minimum(low, np.minimum(open_, close)), 2)
    close = np.round(close, 2)
    df = pd.DataFrame({
        "symbol": symbol,
        "date": [d.strftime("%Y-%m-%d") for d in dates],
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })
    df["daily_return"] = (df["close"] - df["open"]) / df["open"]
    df["ma_7"] = df["close"].rolling(window=7).mean()
    df["ma_30"] = df["close"].rolling(window=30).mean()
    df["volatility_score"] = df["daily_return"].rolling(window=30).std() * 100
    df["momentum_score"] = (df["close"] / df["close"].shift(30) - 1) * 100
    return df


def save_to_sqlite(df, db_path=None):
    if db_path is None:
        db_path = str(Path(__file__).resolve().parent / "stocks.db")
    with sqlite3.connect(db_path) as conn:
        df.to_sql("stocks", conn, if_exists="replace", index=False)


def main():
    all_dfs = []
    total_rows = 0
    for symbol, start_price in SYMBOLS.items():
        df = simulate_stock(symbol, start_price, TRADING_DAYS)
        print(f"Mock data saved: {symbol} - {len(df)} rows")
        all_dfs.append(df)
        total_rows += len(df)

    if all_dfs:
        full_df = pd.concat(all_dfs, ignore_index=True)
        save_to_sqlite(full_df)

    print(f"Total rows saved: {total_rows}")

if __name__ == "__main__":
    main()
