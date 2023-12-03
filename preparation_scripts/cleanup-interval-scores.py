import sqlite3
import pandas as pd
import pickle

conn = sqlite3.connect('data/ncaa.db')
games = pd.read_sql_query("SELECT * FROM games", conn)
pc = sqlite3.connect('data/pbp_with_interval_stats.db')
game_plays = pd.read_sql_query("SELECT * FROM pbp", pc)

#get the number of points scored in each interval for each gameid and each team
    #filter for gameid and time_interval >= 1
for id in game_plays['gameid'].unique():
    game_plays.loc[game_plays['gameid']==id, 'home_score_this_interval'] = game_plays['home_score'] - game_plays['home_score'].shift(1)
    game_plays.loc[game_plays['gameid']==id, 'away_score_this_interval'] = game_plays['away_score'] - game_plays['away_score'].shift(1)
    game_plays.loc[game_plays['gameid']==id, 'home_possessions_this_interval'] = game_plays['home_possessions'] - game_plays['home_possessions'].shift(1)
    game_plays.loc[game_plays['gameid']==id, 'away_possessions_this_interval'] = game_plays['away_possessions'] - game_plays['away_possessions'].shift(1)

game_plays.loc[game_plays['time_interval'] == 0, 'home_score_this_interval'] = game_plays['home_score']
game_plays.loc[game_plays['time_interval'] == 0, 'away_score_this_interval'] = game_plays['away_score']
game_plays.loc[game_plays['time_interval'] == 0, 'home_possessions_this_interval'] = game_plays['home_possessions']
game_plays.loc[game_plays['time_interval'] == 0, 'away_possessions_this_interval'] = game_plays['away_possessions']

interval_scores = game_plays.groupby(['gameid', 'time_interval']).agg({
    'home_score_this_interval': 'sum',
    'away_score_this_interval': 'sum',
    'home_possessions_this_interval': 'sum',
    'away_possessions_this_interval': 'sum',
    'playid': 'count',
    'home_score': 'max',
    'away_score': 'max',
    'home_possessions': 'max',
    'away_possessions': 'max',
    'predicted_tempo': 'max',
    'live_tempo_prediction': 'mean',
    'time_decay': 'min',
    'live_tempo': 'mean',   
}).reset_index()

interval_scores.to_sql('interval_scores_test', pc, if_exists='replace', index=False)
