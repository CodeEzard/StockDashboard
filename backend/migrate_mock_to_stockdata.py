import sqlite3
from pathlib import Path

def migrate_stocks_to_stock_data(db_path=None):
    if db_path is None:
        db_path = str(Path(__file__).resolve().parent / "stocks.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Reset target table on each run to avoid duplicate accumulation
    cur.execute("DELETE FROM stock_data")
    # Read all rows from mock 'stocks' table
    cur.execute("SELECT symbol, date, open, high, low, close, volume FROM stocks")
    rows = cur.fetchall()
    # Insert into stock_data table
    normalized_rows = []
    for symbol, date, open_, high, low, close, volume in rows:
        # Convert date string to YYYY-MM-DD if needed
        if isinstance(date, str) and len(date) > 10:
            date = date[:10]
        normalized_rows.append((symbol, date, open_, high, low, close, volume))

    cur.executemany(
        """
        INSERT INTO stock_data (symbol, date, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        normalized_rows,
    )
    conn.commit()
    print(f"Migrated {len(normalized_rows)} rows from 'stocks' to 'stock_data'.")
    conn.close()

if __name__ == "__main__":
    migrate_stocks_to_stock_data()
