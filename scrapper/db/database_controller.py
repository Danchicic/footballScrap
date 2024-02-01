import sqlite3
from dataclasses import dataclass


@dataclass
class MatchRow:
    team1: str
    team2: str
    match_id: str
    match_url: str


class MatchesDataBaseCRUD:
    def __init__(self):
        self.con = sqlite3.connect("matches_database.db")
        self.cur = self.con.cursor()

    def write_data(self, data: MatchRow):
        self.cur.execute("""INSERT INTO Matches(team1, team2, match_id, match_url) VALUES (?,?,?,?)""",
                         (data.team1, data.team2, data.match_id, data.match_url))
        self.con.commit()

    def delete_row_by_id(self, match_id: str):
        self.cur.execute(f"""DELETE FROM Matches WHERE match_id='{match_id}';""")
        self.con.commit()


if __name__ == '__main__':
    db = MatchesDataBaseCRUD()
    row = MatchRow(team1="Borussia", team2='Spartak', match_id="4gh34g2h3",
                   match_url='https://mamy_ebal/jfkladjfl;kadjfklj3k/2j/34j32k4uj324/j/4jk23j4kl32j423/4j3k2j4kl32432jj42/j/')
    db.write_data(row)
    db.delete_row_by_id("4gh34g2h3")
