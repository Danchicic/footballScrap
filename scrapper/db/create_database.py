import sqlite3

con = sqlite3.connect("matches_database.db")
cur = con.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS MatchProgressStat(
id INTEGER PRIMARY KEY,
team1 TEXT  DEFAULT NULL, 
team2 TEXT  DEFAULT NULL,
team1_count INT DEFAULT NULL,
team2_count INT DEFAULT NULL,
match_id TEXT UNIQUE DEFAULT NULL,
match_url TEXT UNIQUE DEFAULT  NULL,
status TEXT  DEFAULT NULL);
""")
con.commit()
