import sqlite3
import pandas as pd

conn = sqlite3.connect('data/ncaa.db')
df = pd.read_sql_query("SELECT * FROM games", conn)
pc = sqlite3.connect('data/pbp_with_interval_stats.db')
pbp = pd.read_sql_query("SELECT * FROM pbp", pc)

#fix adjem stats
pbp['home_adjem'] = pbp.merge(df[['id','home_kenpom_adjem']], left_on='gameid', right_on='id', how='left')['home_kenpom_adjem']
pbp['away_adjem'] = pbp.merge(df[['id','away_kenpom_adjem']], left_on='gameid', right_on='id', how='left')['away_kenpom_adjem']
pbp['home_adjem'] *= 1.01

print(pbp['home_adjem'].head(100))