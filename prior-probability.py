import sqlite3
import pandas as pd
from scipy import stats

conn = sqlite3.connect('data/ncaa.db')
c = conn.cursor()

#convert the 'games' table to a pandas dataframe
games = pd.read_sql_query("SELECT * FROM games", conn)

#adjT = team expected possessions per 40 minutes, against an average team
#expected possessions in this game: harmonic mean of home and away adjT * 2
games['xPos'] = 2 * (2 / (1/games['home_kenpom_adj_t'] + 1/games['away_kenpom_adj_t']))

#differential per 100 possessions: (home adjEM + 1% home advantage*!neutral) - away adjEM
games['differential'] = games['home_kenpom_adjem']+((.01*games['home_kenpom_adj_o'] - .01*games['home_kenpom_adj_d']) * (1.0-games['neutral_site'])) - games['away_kenpom_adjem']

#expected margin: differential * expected possessions / 200
games['xMargin'] = games['differential'] * games['xPos'] / 200

#home_underdog: negative xMargin
games['home_underdog'] = games['xMargin'] < 0

#upset: home underdog wins, or home favorite loses
games['upset'] = (games['home_underdog'] & games['home_win']) | (~games['home_underdog'] & ~games['home_win'])

#surprise: absolute difference between xMargin and actual margin
games['surprise'] = abs(games['xMargin'] - (games['home_score']-games['away_score']))

#margin is normal(xMargin, 13.22) home win probability is P(X>0)
#See https://rpubs.com/Thom9567/1012507
games['prior_home_win_prob'] = 1 - stats.norm.cdf(0, games['xMargin'], 13.22)

#add columns xPos, xMargin, home_underdog, upset, surprise, home_win_prob to games table
games.to_sql('games', conn, if_exists='replace', index=False)

