import sqlite3
from dataclasses import dataclass


@dataclass
class MatchRow:
    team1: str
    team2: str
    match_id: str
    match_url: str


class MatchStat:
    def __init__(self, match_id, status='', team1_count=0, team2_count=0, ):
        self.team1_count: int = team1_count
        self.team2_count: int = team2_count
        self.match_id: str = match_id
        self.status: str = status


class MatchesDataBaseCRUD:
    def __init__(self):
        self.con = sqlite3.connect("./scrapper/db/matches_database.db")
        self.cur = self.con.cursor()

    def write_data(self, data: MatchRow):
        self.cur.execute(f"""SELECT match_id FROM MatchProgressStat WHERE match_id='{data.match_id}'""")
        is_in = self.cur.fetchone()
        if is_in is not None:
            self.cur.execute(f"""
            UPDATE MatchProgressStat SET team1 ='{data.team1}', team2='{data.team2}',match_url='{data.match_url}' 
            WHERE match_id='{data.match_id}'  
            """)
            self.con.commit()
            return

        self.cur.execute("""INSERT INTO MatchProgressStat(team1, team2, match_id, match_url) VALUES (?,?,?,?)""",
                         (data.team1, data.team2, data.match_id, data.match_url))
        self.con.commit()
        print("add new match")

    def delete_row_by_id(self, match_id: str):
        self.cur.execute(f"""DELETE FROM MatchProgressStat WHERE match_id='{match_id}';""")
        self.con.commit()

    def get_names_by_id(self, match_id):
        self.cur.execute(f"""
        SELECT team1, team2 FROM MatchProgressStat WHERE match_id='{match_id}'
        """)
        return self.cur.fetchone()

    def write_new_match(self, match_id):
        self.cur.execute(f"""SELECT match_id FROM MatchProgressStat WHERE match_id={match_id}""")
        if self.cur.fetchone() is not None:
            return
        self.cur.execute(f"""
        INSERT INTO MatchProgressStat(match_id, status) VALUES('{match_id}', 'new_match')
        """)
        self.con.commit()

    def update_status(self, data: MatchStat):
        self.cur.execute(f"""SELECT match_id FROM MatchProgressStat WHERE match_id='{data.match_id}'""")
        is_id = self.cur.fetchone()
        if is_id is None:
            self.cur.execute(f"""
            INSERT INTO MatchProgressStat(match_id, status) VALUES (?,?)
            """, (data.match_id, data.status))
            self.con.commit()
            return

        self.cur.execute(f"""
        SELECT status FROM MatchProgressStat WHERE match_id='{data.match_id}'
        """)
        is_first_time_stat = self.cur.fetchone()
        if is_first_time_stat is not None and is_first_time_stat[0] == 'first_time_stat':
            return

        self.cur.execute(f"""
        UPDATE MatchProgressStat 
        SET status='{data.status}', team1_count={data.team1_count}, 
                        team2_count={data.team2_count}
         WHERE match_id='{data.match_id}'
        """)
        self.con.commit()

    def first_time_update_data(self, data: MatchStat):
        self.cur.execute(f"""
        UPDATE MatchProgressStat
        SET status=?, team1_count=?, team2_count=?
        WHERE match_id='{data.match_id}'
        """, (data.status, data.team1_count, data.team2_count))
        self.con.commit()

    def get_first_time_stat(self, match_id):
        self.cur.execute(f"""
        SELECT team1_count, team2_count FROM MatchProgressStat WHERE match_id='{match_id}'
        """)
        s = self.cur.fetchone()
        return s[0], s[1]

    def return_status_by_id(self, match_id):
        self.cur.execute(f"""
        SELECT status FROM MatchProgressStat WHERE match_id='{match_id}'
        """)
        return self.cur.fetchone()

    def check_match_id(self, match_id):
        self.cur.execute(f"""
        SELECT status FROM MatchProgressStat WHERE match_id='{match_id}'
        """)
        return self.cur.fetchone()

    def get_urls(self):
        self.cur.execute("""SELECT match_url FROM MatchProgressStat""")
        return self.cur.fetchall()


if __name__ == '__main__':
    db = MatchesDataBaseCRUD()
    row = MatchRow(team1="Borussia", team2='Spartak', match_id="4gh34g2h3",
                   match_url='https://mamy_ebal/jfkladjfl;kadjfklj3k/2j/34j32k4uj324/j/4jk23j4kl32j423/4j3k2j4kl32432jj42/j/')
    db.write_data(row)
    db.delete_row_by_id("4gh34g2h3")
