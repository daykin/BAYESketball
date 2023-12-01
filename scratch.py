import sqlite3
import pandas as pd

conn = sqlite3.connect('data/pbp_with_interval_stats.db')

df = pd.read_sql("SELECT * FROM pbp", conn)
df = df.drop_duplicates(subset=['gameid','time_interval'])
print(df.columns)