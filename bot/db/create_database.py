import datetime
import sqlite3
from datetime import time

con = sqlite3.connect('test_database.db')
cur = con.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS Users(
    id INTEGER PRIMARY KEY,
    user_id INT UNIQUE,
    user_name TEXT,
    date_join_UNIX INT 
)""")

cur.execute(f'''INSERT INTO Users VALUES(?,?,?,?)''', (None, 1223, 'Данечка2', 4343))
con.commit()
