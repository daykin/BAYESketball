import sqlite3
import pandas as pd
import numpy as np

conn = sqlite3.connect('data/ncaa.db')
games = pd.read_sql_query("SELECT * FROM games", conn)
pc = sqlite3.connect('data/pbp_with_interval_stats.db')
pbp = pd.read_sql_query("SELECT * FROM pbp", pc)
tempo_error_sd = np.std(games['home_possessions'] + games['away_possessions'] - games['predicted_tempo'])

pbp['live_tempo']=0.5*(((pbp['home_possessions']+pbp['away_possessions'])*81)/(1+pbp['time_interval']))

pbp['live_tempo_prediction'] = 2*(pbp['predicted_tempo'] * (pbp['time_decay']) + pbp['live_tempo'] * (1-pbp['time_decay']))
print(pbp[['gameid','time_interval','live_tempo_prediction', 'live_tempo', 'time_decay', 'predicted_tempo']].head(100))
#sort by gameid and time_interval
pbp = pbp.sort_values(['gameid', 'time_interval'])
pbp.to_sql('pbp', pc, if_exists='replace', index=False)