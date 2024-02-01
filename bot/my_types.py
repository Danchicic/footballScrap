class ChannelAnswerType:
    def __init__(self, country, championship, team1, team2, team1_score, team2_score, match_minute, forecast_team):
        self.country = country
        self.champ = championship
        self.match = f"{team1} - {team2}"
        self.score = f"{team1_score}:{team2_score}"
        self.match_minute = match_minute
        self.forecast_team = forecast_team
