import sqlite3
from datetime import datetime

def migrate_stocks_to_stock_data(db_path="stocks.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Read all rows from mock 'stocks' table
    cur.execute("SELECT symbol, date, open, high, low, close, volume FROM stocks")
    rows = cur.fetchall()
    # Insert into stock_data table
    inserted = 0
    for symbol, date, open_, high, low, close, volume in rows:
        # Convert date string to YYYY-MM-DD if needed
        if isinstance(date, str) and len(date) > 10:
            date = date[:10]
        cur.execute("""
            INSERT OR IGNORE INTO stock_data (symbol, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (symbol, date, open_, high, low, close, volume))
        inserted += 1
    conn.commit()
    print(f"Migrated {inserted} rows from 'stocks' to 'stock_data'.")
    conn.close()

if __name__ == "__main__":
    migrate_stocks_to_stock_data()
