#Poisson R^2:0.24200050078138832
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

#interval columns:
#    'index', 'playid', 'gameid', 'time_interval', 'time_minutes',
#    'time_seconds', 'description', 'home_score', 'away_score',
#    'scoring_play', 'who', 'possession', 'home_fgm', 'home_fga', 'home_3pm',
#    'home_3pa', 'home_ftm', 'home_fta', 'home_oreb', 'home_to',
#    'home_possessions', 'away_fgm', 'away_fga', 'away_3pm', 'away_3pa',
#    'away_ftm', 'away_fta', 'away_oreb', 'away_to', 'away_possessions',
#    'home_possessions_this_interval', 'away_possessions_this_interval',
#    'home_score_this_interval', 'away_score_this_interval'

def tempo_rsquared(games):
    from sklearn.metrics import r2_score
    predicted_tempo = games['predicted_tempo']
    total_possessions = games['home_possessions']
    r2 = r2_score(total_possessions, predicted_tempo)
    print("R^2:", r2)

def predict_tempo(x, tempo_stats):
    import numpy as np
    intercept = tempo_stats['mean']['Intercept']
    off_tempo = tempo_stats['mean']['home_adjT']
    def_tempo = tempo_stats['mean']['away_adjT']
    live_tempo = tempo_stats['mean']['live_tempo']
    site = tempo_stats['mean']['neutral_site']
    tempo = np.exp(intercept+off_tempo*(x['home_adjT'])+def_tempo*(x['away_adjT'])+site*(x['neutral_site'])+live_tempo*(x['live_tempo']))
    x['predicted_tempo'] = tempo
    #consistently off by about 3%, add this fudge factor (probably due to incomplete parsing of pbp data)
    diff = np.mean(x['final_home_possessions']/x['predicted_tempo'])
    x['predicted_tempo'] = x['predicted_tempo']*diff
    print(x.loc[x['time_interval']>75][['final_home_possessions', 'final_away_possessions', 'predicted_tempo']].head(100))
    print(diff)
    return x

def main():
    import sqlite3
    import pandas as pd

    import numpy as np
    import os
    from multiprocessing import freeze_support
    import matplotlib.pyplot as plt
    import pymc as pm
    import bambi as bmb
    import arviz as az
    import cloudpickle
    from formulae import design_matrices
    #Who controls the home team's tempo? the faster or slower team? Does site matter?
    games_conn = sqlite3.connect('data/ncaa.db')
    gc = games_conn.cursor()
    games = pd.read_sql_query("SELECT * FROM games", games_conn)
    #interval stats
    interval_stats_conn = sqlite3.connect('data/pbp_with_interval_stats.db')
    plays_full = pd.read_sql_query("SELECT * FROM pbp", interval_stats_conn)
    # plays_full['live_tempo'] = (plays_full['home_possessions']+plays_full['away_possessions'])/(plays_full['time_interval']+1)
    # plays_full['final_home_score'] = plays_full.merge(games[['id','home_score']], left_on='gameid', right_on='id', how='left')['home_score_y']
    # plays_full['final_away_score'] = plays_full.merge(games[['id','away_score']], left_on='gameid', right_on='id', how='left')['away_score_y']
    # plays_full['final_home_possessions'] = plays_full.merge(games[['id','home_possessions']], left_on='gameid', right_on='id', how='left')['home_possessions_y']
    # plays_full['final_away_possessions'] = plays_full.merge(games[['id','away_possessions']], left_on='gameid', right_on='id', how='left')['away_possessions_y']
    # plays_full['home_adjem'] = plays_full.merge(games[['id','home_kenpom_adjem']], left_on='gameid', right_on='id', how='left')['home_kenpom_adjem']
    # plays_full['away_adjem'] = plays_full.merge(games[['id','away_kenpom_adjem']], left_on='gameid', right_on='id', how='left')['away_kenpom_adjem']
    # plays_full['home_adjT'] = plays_full.merge(games[['id','home_kenpom_adj_t']], left_on='gameid', right_on='id', how='left')['home_kenpom_adj_t']
    # plays_full['away_adjT'] = plays_full.merge(games[['id','away_kenpom_adj_t']], left_on='gameid', right_on='id', how='left')['away_kenpom_adj_t']
    # plays_full['neutral_site'] = plays_full.merge(games[['id','neutral_site']], left_on='gameid', right_on='id', how='left')['neutral_site']
    # plays_full['adjem_difference'] = plays_full['home_adjem'] - plays_full['away_adjem']
    # plays_full['tempo_difference'] = plays_full['home_adjT'] - plays_full['away_adjT']
    # plays_full['intercept'] = 1
    #get 2000 random plays
    plays_ = plays_full#.sample(10000)
    print(min(plays_['home_adjT']))
    if not os.path.exists('predicted_tempo.pkl'):
        fml = 'final_home_possessions ~ home_adjT+away_adjT+neutral_site+live_tempo'
        dm = design_matrices(fml, plays_, na_action='error')
        history_tempo_model = bmb.Model(fml, plays_,family='poisson', link='log')
        history_tempo_trace = history_tempo_model.fit(draws=1000, tune=500, cores=8, chains=16, target_accept=.95, return_inferencedata=True)
        cloudpickle.dump(history_tempo_trace, open('predicted_tempo.pkl', 'wb'))
    else:
        history_tempo_trace = cloudpickle.load(open('predicted_tempo.pkl', 'rb'))
    
    stats = az.summary(history_tempo_trace.posterior, round_to=3,kind='stats')
    print(stats)
    new_df = predict_tempo(plays_full, stats)
    new_df.to_sql('pbp', interval_stats_conn, if_exists='replace', index=False)
if __name__ == "__main__":
    main()