import sqlite3
import pandas as pd

#create a mini database for testing on pbp_with_interval_stats.db and ncaa.db, 100 games
conn = sqlite3.connect('data/ncaa.db')
out_conn = sqlite3.connect('data/ncaa_mini.db')
df = pd.read_sql_query("SELECT * FROM games", conn)
df = df.head(1000)
out_conn.execute("DROP TABLE IF EXISTS games")
df.to_sql('games', out_conn, index=False)
pc = sqlite3.connect('data/pbp_with_interval_stats.db')
out_pc = sqlite3.connect('data/pbp_with_interval_stats_mini.db')
pbp = pd.read_sql_query("SELECT * FROM pbp", pc)
pbp = pbp[pbp['gameid'].isin(df['id'])]
out_pc.execute("DROP TABLE IF EXISTS pbp")
pbp.to_sql('pbp', out_pc, index=False)