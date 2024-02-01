import sqlite3

con = sqlite3.connect("matches_database.db")
cur = con.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS Matches(
id INTEGER PRIMARY KEY,
team1 TEXT,
team2 TEXT,
match_id TEXT,
match_url TEXT);
""")

con.commit()
