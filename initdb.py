import sqlite3

# Connect to (or create) the database
conn = sqlite3.connect("prices.db")
cursor = conn.cursor()

# Create table if it doesn’t exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS prices (
        sku TEXT,
        time_key INTEGER,
        pvp_is_competitorA REAL,
        pvp_is_competitorB REAL,
        pvp_is_competitorA_actual REAL,
        pvp_is_competitorB_actual REAL,
        PRIMARY KEY (sku, time_key)
    )
""")

# Example data (you can replace these with actual test values)
example_data = [
    ("2123", 20250523, 5.0, 9.0),
    ("2456", 20250524, 5.0, 9.0),
]

# Insert example data into the database
cursor.executemany("""
    INSERT OR IGNORE INTO prices (sku, time_key, pvp_is_competitorA, pvp_is_competitorB) 
    VALUES (?, ?, ?, ?)
""", example_data)

# Commit and close connection
conn.commit()
conn.close()

print("Database initialized successfully.")
