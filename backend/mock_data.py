import numpy as np
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

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


def generate_trading_days(start_date, num_days):
    days = []
    date = start_date
    while len(days) < num_days:
        if date.weekday() < 5:  # Weekday
            days.append(date)
        date += timedelta(days=1)
    return days


def simulate_stock(symbol, start_price, trading_days):
    np.random.seed(hash(symbol) % 2**32)
    dates = generate_trading_days(datetime.today() - timedelta(days=365), trading_days)
    prices = [start_price]
    for _ in range(1, trading_days):
        drift = 0.0005
        shock = np.random.normal(0, 0.02)
        price = prices[-1] * (1 + drift + shock)
        prices.append(max(price, 1))
    prices = np.array(prices)
    open_ = prices * (1 + np.random.normal(0, 0.005, trading_days))
    close = prices * (1 + np.random.normal(0, 0.005, trading_days))
    high = np.maximum(open_, close) * (1 + np.abs(np.random.normal(0, 0.01, trading_days)))
    low = np.minimum(open_, close) * (1 - np.abs(np.random.normal(0, 0.01, trading_days)))
    volume = np.random.randint(VOLUME_MIN, VOLUME_MAX, trading_days)
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


def save_to_sqlite(df, db_path="stocks.db"):
    with sqlite3.connect(db_path) as conn:
        df.to_sql("stocks", conn, if_exists="append", index=False)


def main():
    all_dfs = []
    total_rows = 0
    for symbol, start_price in SYMBOLS.items():
        df = simulate_stock(symbol, start_price, TRADING_DAYS)
        save_to_sqlite(df)
        print(f"Mock data saved: {symbol} - {len(df)} rows")
        all_dfs.append(df)
        total_rows += len(df)
    print(f"Total rows saved: {total_rows}")

if __name__ == "__main__":
    main()
