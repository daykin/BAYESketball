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
#Efficiency is updated every 30 second interval with priors based on KenPom data
#xMargin is normal, with mean modeled as a sum of poisson realizations with lambda updated at each interval, and SD decays with time

sigma_xPos_0 = games['xPos'].std() #About 4.27
sigma_adjem_0 = games['home_kenpom_adjem'].std() #About 12.0
sigma_adj_o_0 = games['home_kenpom_adj_o'].std() #About 7.0
sigma_adj_d_0 = games['home_kenpom_adj_d'].std() #About 6.5

sigma_tempo_0 = games['home_kenpom_adj_t'].std() #About 3.0

for game_ in games.head(5).iterrows():
    game = game_[1]
    xMargin = game['xMargin']
    plays = plays_[plays_['gameid']==game['id']]
    if len(plays) == 0:
        print("No plays for game " + str(game['id']))
        gc.execute("DELETE FROM games WHERE id = ?", (game['id'],))
        continue
    else:
        #sort plays by time. zeroth element of each array is initial prior
        plays = plays.sort_values(by=['time_interval','time_minutes','time_seconds'], ascending=[True, False, False])
        print(plays.head())
        if(game['neutral_site'] == 1):
            home_court_advantage = 0
        else:
            home_court_advantage = (game['home_kenpom_adj_o']*.01) + (game['home_kenpom_adj_d']*.01)
        time_step_models = [pm.Model() for _ in range(82)]
        home_adjem_priors = np.zeros(82, dtype=float)
        away_adjem_priors = np.zeros_like(home_adjem_priors)
        home_adjem_priors[0] = (game['home_kenpom_adjem'] + home_court_advantage)/82.
        away_adjem_priors[0] = game['away_kenpom_adjem']/82.
        home_tempo_priors = np.zeros_like(home_adjem_priors)
        away_tempo_priors = np.zeros_like(home_adjem_priors)
        home_tempo_priors[0] = game['home_kenpom_adj_t']/82.
        away_tempo_priors[0] = game['away_kenpom_adj_t']/82.
        plays_last_interval = plays[plays['time_interval']==0]
        home_score_last_interval = plays_last_interval['home_score'].max()
        away_score_last_interval = plays_last_interval['away_score'].max()
        home_possessions_last_interval = plays_last_interval['home_possessions'].max()
        away_possessions_last_interval = plays_last_interval['away_possessions'].max()
        home_adjem_last_interval = home_adjem_priors[0]
        away_adjem_last_interval = away_adjem_priors[0]
        home_tempo_last_interval = home_tempo_priors[0]
        away_tempo_last_interval = away_tempo_priors[0]
        for interval in range(1,82):
            time_decay = ((82-interval)/82)**0.5
            plays_this_interval = plays[plays['time_interval']==interval]
            home_score_this_interval = plays_this_interval['home_score'].max()-home_score_last_interval
            away_score_this_interval = plays_this_interval['away_score'].max()-away_score_last_interval
            home_possessions_this_interval = plays_this_interval['home_possessions'].max()-home_possessions_last_interval
            away_possessions_this_interval = plays_this_interval['away_possessions'].max()-away_possessions_last_interval

            with pm.Model() as model:
                 #Priors for possessions(tempo) and efficiency - Sigma gets stronger with time
                home_efficiency_margin = pm.Normal('home_adjem', mu=home_adjem_priors[interval-1], sd=sigma_adjem_0*time_decay)
                away_efficiency_margin = pm.Normal('away_adjem', mu=away_adjem_priors[interval-1], sd=sigma_adjem_0*time_decay)
                home_tempo = pm.Normal('tempo', mu=home_tempo_priors[interval-1], sd=sigma_tempo_0*time_decay)
                away_tempo = pm.Normal('tempo', mu=away_tempo_priors[interval-1], sd=sigma_tempo_0*time_decay)
                
                #Prior tempo starts as harmonic mean of KenPom tempos divided by 82 intervals 
                #Likelihood: poisson regression on lambda: 
                # X_i = possessions in a given interval by similar teams against similar opponents
                #Posterior: Negative-binomial(alpha = possessions remaining, beta = 82-interval)
