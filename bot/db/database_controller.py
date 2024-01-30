import time
import sqlite3


class UserRow:
    def __init__(self, user_id, user_name):
        self.user_id = user_id
        self.user_name = user_name


class UserDataBase:
    def __init__(self):
        self.conn = sqlite3.connect(database='../test_database.db')
        self.cur = self.conn.cursor()

    def check_user(self, user: UserRow):
        if not self.cur.execute(f"SELECT user_id FROM Users WHERE user_id={user.user_id}").fetchall():
            unix_now = int(time.time())
            self.cur.execute("INSERT INTO Users (user_id, user_name, date_join_UNIX) VALUES (?, ?, ?)",
                             (user.user_id, user.user_name, unix_now))
            self.conn.commit()


if __name__ == '__main__':
    d = UserDataBase()
    d.check_user(123)
