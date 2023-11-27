import sqlite3
import pymc as pm
import pandas as pd

#Database of scorelines and priors
games_conn = sqlite3.connect('data/ncaa.db')
gc = games_conn.cursor()
games = pd.read_sql_query("SELECT * FROM games", games_conn)
#Database of play-by-play data
pbp_conn = sqlite3.connect('data/pbp.db')
pc = pbp_conn.cursor()

model = pm.Model()

for game in games.iterrows():
    
#with model:
#    pass