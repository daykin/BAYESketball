import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

conn = sqlite3.connect('data/pbp_with_interval_stats.db')

pbp = pd.read_sql_query("SELECT * FROM pbp", conn)

#Pick a random gameid
gameid = 401369891
g = pbp.loc[pbp['gameid']==gameid]
print(g.columns)
print(g['predicted_tempo'].iloc[0])

intervals = []
probabilities = []
for interval in range(0,82):
    #Simulate outcome of game 1000 times based on tempo and scoring efficiency margin
    if len(g.loc[g['time_interval']==interval]) == 0:
        continue
    intervals.append(interval)
    current_margin = g.loc[g['time_interval']==interval]['home_score'].iloc[0] - g.loc[g['time_interval']==interval]['away_score'].iloc[0]
    mean_tempo = g.loc[g['time_interval']==interval]['live_tempo_prediction'].iloc[0]/2.
    #estimated possessions remaining
    mean_tempo = mean_tempo*(1-(interval/82.0))
    sd_tempo = 3.0 * (1.0-np.sqrt(interval/82.0))
    mean_predicted_em = g.loc[g['time_interval']==interval]['mean_predicted_em'].iloc[0]
    #sd_em = g.loc[g['time_interval']==interval]['em_sigma2'].iloc[0]
    sd_em=0.255
    current_margin = g.loc[g['time_interval']==interval]['home_score'].iloc[0] - g.loc[g['time_interval']==interval]['away_score'].iloc[0]
    samples = np.zeros(10000, dtype = np.float64)
    for i in range(10000):
        #tempo: normal distribution with mean = mean_tempo, sd = sd_tempo
        tempo = np.random.normal(mean_tempo, sd_tempo)
        #scoring efficiency: normal distribution with mean = mean_predicted_em, sd = sd_em
        eff = np.random.normal(mean_predicted_em, sd_em)
        remaining_margin = current_margin + (tempo*eff)
        #print(tempo, eff, remaining_margin)
        samples[i] = remaining_margin
    #probability of winning: P(remaining_margin > 0)
    #home wins = count(remaining_margin > 0)/1000.
    home_win_prob = np.sum(samples > 0.)/10000.
    probabilities.append(home_win_prob)

# Plot probabilities vs. interval with green trace
plt.plot(intervals, probabilities, color='red', linewidth=3)
#dashed horizontal line at 50%
plt.axhline(y=0.5, color='black', linestyle='--')
plt.xlabel('Interval')
plt.ylabel('Probability')
plt.title('Probability of Winning vs. Interval')
plt.show()
