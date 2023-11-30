import pandas as pd
import sqlite3
import numpy as np

conn = sqlite3.connect('data/pbp.db')
df = pd.read_sql("SELECT * FROM pbp", conn)

with_interval_stats = sqlite3.connect('data/pbp_with_interval_stats.db')

# Function to calculate possessions for an interval
def calculate_possessions(interval_df, homeAway):
    return interval_df[f'{homeAway}_possessions'].max() - interval_df[f'{homeAway}_possessions'].min()

def calculate_score(interval_df, homeAway):
    return interval_df[f'{homeAway}_score'].max() - interval_df[f'{homeAway}_score'].min()


df['home_possessions_this_interval'] = 0.
df['away_possessions_this_interval'] = 0.
df['home_score_this_interval'] = 0.
df['away_score_this_interval'] = 0.
# Iterate over each gameid and interval
i=0
for gameid in df['gameid'].unique():
    i+=1
    game_df = df[df['gameid'] == gameid]
    for interval in game_df['time_interval'].unique():
        interval_df = game_df[game_df['time_interval'] == interval]
        home_possessions = calculate_possessions(interval_df, 'home')
        away_possessions = calculate_possessions(interval_df, 'away')
        df.loc[(df['gameid'] == gameid) & (df['time_interval'] == interval), 'home_possessions_this_interval'] = home_possessions
        df.loc[(df['gameid'] == gameid) & (df['time_interval'] == interval), 'away_possessions_this_interval'] = away_possessions
        home_score = calculate_score(interval_df, 'home')
        away_score = calculate_score(interval_df, 'away')
        df.loc[(df['gameid'] == gameid) & (df['time_interval'] == interval), 'home_score_this_interval'] = home_score
        df.loc[(df['gameid'] == gameid) & (df['time_interval'] == interval), 'away_score_this_interval'] = away_score
    
    print(f"Finished game {i}/{len(df['gameid'].unique())}")

out_df = df[['gameid','time_interval','home_possessions_this_interval','away_possessions_this_interval','home_score_this_interval','away_score_this_interval']]
#get unique in gameid and time_interval
out_df = out_df.drop_duplicates(subset=['gameid','time_interval'])
#write updated df to pbp_with_interval_stats.db
df.to_sql('pbp', with_interval_stats, if_exists='replace', index=False)
