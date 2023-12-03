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

#for home and away, develop three probit regressions: one for FT, one for 2PT, one for 3PT


def main():
    import sqlite3
    import pandas as pd
    import pymc as pm
    import numpy as np
    import arviz as az
    import os
    import bambi as bmb
    import matplotlib.pyplot as plt
    import formulae
    import cloudpickle

    gc = sqlite3.connect('data/ncaa.db')
    pc = sqlite3.connect('data/pbp_with_interval_stats.db')
    pbp = pd.read_sql_query("SELECT * FROM pbp", pc)
    
    def predict_sigma(stats, df):
        df['em_sigma2'] = stats['mean']['Intercept'] + stats['mean']['time_interval']*df['time_interval']+stats['mean']['interval_squared']*df['time_interval']**2
        #em_sigma2 is max of original and 0.25
        df['em_sigma2'] = np.maximum(df['em_sigma2'], 0.25)
        return df
    
    #estimate variance of scoring efficiency margin vs interval
    
    pbp['live_scoring_efficiency_margin'] = ((pbp['home_score']/pbp['home_possessions'])-(pbp['away_score']/pbp['away_possessions']))
    pbp['actual_scoring_efficiency_margin'] = ((pbp['final_home_score']/pbp['final_home_possessions'])-(pbp['final_away_score']/pbp['final_away_possessions']))
    #delete rows with  infinite values
    pbp.fillna(0, inplace=True)
    pbp = pbp.replace([np.inf, -np.inf], np.nan)
    pbp = pbp.dropna()
    #if possessions = 0, then efficiency margin = 0
    pbp['squared_efficiency_margin_deviation'] = .1+(pbp['live_scoring_efficiency_margin']-pbp['actual_scoring_efficiency_margin'])**2
    print(np.max(pbp['squared_efficiency_margin_deviation']))
    print(np.min(pbp['squared_efficiency_margin_deviation']))
    pbp['interval_squared'] = pbp['time_interval']**2
    if not os.path.exists("efficiency_model_quad.pkl"):
        variance_fml = bmb.Formula('squared_efficiency_margin_deviation ~ time_interval+interval_squared')
        #for a known mean and unknown variance, i'd guess a T-distribution posterior but I don't know how to do that in pymc
        #instead, a normal will be close enough. with this many observations, they're essentially the same
        variance_model = bmb.Model(variance_fml, pbp, family = 'gaussian')
        variance_trace = variance_model.fit(inference_method='vi', init='advi+adapt_diag', chains=4, n=50000, random_seed=42)
        smpl = variance_trace.sample(5000)
        stats = az.summary(smpl, kind='stats')
        with open("efficiency_model_quad.pkl", "wb") as f:
            cloudpickle.dump(variance_trace, f)
        print(stats)
    else:
        with open("efficiency_model_quad.pkl", "rb") as f:
            variance_trace = cloudpickle.load(f)
    smpl = variance_trace.sample(5000)
    stats = az.summary(smpl, kind='stats')
    print(stats)
    pbp = predict_sigma(stats, pbp)
    #pbp['mean_predicted_em'] = pbp['time_decay']*pbp['adjem_difference']/100. + (1-pbp['time_decay'])*pbp['live_scoring_efficiency_margin']
    #pbp.to_sql('pbp', pc, if_exists='replace', index=False)
if __name__ == '__main__':
    main()