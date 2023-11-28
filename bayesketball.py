import sqlite3
import pandas as pd
import pymc as pm
import numpy as np
print("imported pymc")

#games columns:
#       'id', 'date', 'home_id', 'away_id', 'home_name', 'away_name',
#       'home_score', 'away_score', 'neutral_site', 'home_win', 'away_win',
#       'home_kenpom', 'away_kenpom', 'home_record', 'away_record',
#       'home_kenpom_adjem', 'away_kenpom_adjem', 'home_kenpom_adj_o',
#       'away_kenpom_adj_o', 'home_kenpom_adj_d', 'away_kenpom_adj_d',
#       'home_kenpom_adj_t', 'away_kenpom_adj_t', 'home_fgm', 'home_fga',
#       'home_3pm', 'home_3pa', 'home_ftm', 'home_fta', 'xPos', 'differential',
#       'xMargin', 'home_underdog', 'upset', 'surprise', 'prior_home_win_prob',

#play-by-play columns:
#       'playid', 'gameid', 'time', 'description', 'home_score', 'away_score',
#       'scoring_play', 'who', 'possession', 'home_fgm', 'home_fga', 'home_3pm',
#       'home_3pa', 'home_ftm', 'home_fta', 'away_fgm', 'away_fga', 'away_3pm',
#       'away_3pa', 'away_ftm', 'away_fta'

#Database of scorelines and priors
games_conn = sqlite3.connect('data/ncaa.db')
gc = games_conn.cursor()
games = pd.read_sql_query("SELECT * FROM games", games_conn)
#Database of play-by-play data
pbp_conn = sqlite3.connect('data/pbp.db')
pc = pbp_conn.cursor()
plays_ = pd.read_sql_query("SELECT * FROM pbp", pbp_conn)

#PyMC model: Home Win probability is deterministic function of expected margin (erf(0) norm(xMargin, SD)))
# SD begins at 13.22 (see ref.) and decays proportional sqrt(possessions remaining)
# margin is deterministic function of possessions (Tempo), score per possession (Offensive Efficiency),
# opponent score per possession (Defensive Efficiency), and time remaining
# these three variables are stochastic with pre-computed priors
# at each time interval, observed score, number of possessions, and time remaining are used to update the priors
sigma_xPos_0 = games['xPos'].std() #About 4.27
sigma_adjem_0 = games['home_kenpom_adjem'].std() #About 12.0
sigma_adj_o_0 = games['home_kenpom_adj_o'].std() #About 7.0
sigma_adj_d_0 = games['home_kenpom_adj_d'].std() #About 6.5
home_court_advantage = (['home_kenpom_adj_o']*1.01) - (['home_kenpom_adj_d']*1.01)
for game_ in games.head(5).iterrows():
    game = game_[1]
    xMargin = game['xMargin']
    plays = plays_[plays_['gameid']==game['id']]
    if len(plays) == 0:
        print("No plays for game " + str(game['id']))
        gc.execute("DELETE FROM games WHERE id = ?", (game['id'],))
        continue
    else:
        #sort plays by time
        plays = plays.sort_values(by=['time_interval','time_minutes','time_seconds'], ascending=[True, False, False])
        time_step_models = [pm.Model() for _ in range(80)]
        home_adjem_priors = np.zeros(80, dtype=float)
        away_adjem_priors = np.zeros_like(home_adjem_priors)

        for interval in range(80):
            time_decay = (80-interval)**0.5
            with pm.Model() as model:
                #Priors for offensive efficiency, defensive efficiency, and tempo