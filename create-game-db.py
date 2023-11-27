import glob
import json
import pandas as pd
import sqlite3

conn = sqlite3.connect('data/ncaa.db')

conn.execute('''CREATE TABLE IF NOT EXISTS games (
    id INTEGER,
    date TEXT,
    home_id INTEGER,
    away_id INTEGER,
    home_name TEXT,
    away_name TEXT,
    home_score INTEGER,
    away_score INTEGER,
    neutral_site INTEGER,
    home_win INTEGER,
    away_win INTEGER,
    home_kenpom REAL,
    away_kenpom REAL,
    home_record TEXT,
    away_record TEXT,
    home_kenpom_adjem REAL,
    away_kenpom_adjem REAL,
    home_kenpom_adj_o REAL,
    away_kenpom_adj_o REAL,
    home_kenpom_adj_d REAL,
    away_kenpom_adj_d REAL,
    home_kenpom_adj_t REAL,
    away_kenpom_adj_t REAL,
    home_fgm INTEGER,
    home_fga INTEGER,
    home_3pm INTEGER,
    home_3pa INTEGER,
    home_ftm INTEGER,
    home_fta INTEGER
)''')

for dir in glob.glob('data/days/*'):
    dts = dir[dir.rfind('/')+1:]
    kp = pd.read_csv(f"data/days/{dts}/kenpom_cleaned.csv")
    with open (f"data/days/{dts}/events_{dts}.json", 'r') as f:
        events = json.load(f)
        for event in events:
            competition = event['competitions'][0]
            gameID = int(competition['id'])
            date = competition['date']
            pbpAvailable = int(competition['playByPlayAvailable'])
            neutral = int(competition['neutralSite'])
            canceled = False
            nonD1 = False
            homeID, homeName, homeScore, homeWin, homeKenpom, homeRecord, homeKenpomAdjem, homeKenpomAdjO, homeKenpomAdjD, homeKenpomAdjT, homeFgm, homeFga, home3pm, home3pa, homeFtm, homeFta = [None] * 16
            awayID, awayName, awayScore, awayWin, awayKenpom, awayRecord, awayKenpomAdjem, awayKenpomAdjO, awayKenpomAdjD, awayKenpomAdjT, awayFgm, awayFga, away3pm, away3pa, awayFtm, awayFta = [None] * 16
            for competitor in event['competitions'][0]['competitors']:
                teamID = int(competitor['id'])
                
                try:
                    teamWin = int(competitor['winner'])
                except KeyError:
                    gameStatus = competition['status']['type']['name']
                    if gameStatus != "STATUS_FINAL":
                        continue
                    else:
                        print(gameID)
                        print(competitor)
                        raise
                team = competitor['team']
                teamScore = int(competitor['score'])
                teamKenpom = kp[kp['TeamID'].astype(int) == teamID]
                if teamKenpom.empty or canceled:
                    nonD1 = True
                    continue
                teamName = teamKenpom['Team'].values[0]
                teamRecord = teamKenpom['W-L'].values[0]
                teamKenpomRank = teamKenpom['Rk'].values[0]
                teamKenpomAdjem = teamKenpom['AdjEM'].values[0]
                teamKenpomAdjO = teamKenpom['AdjO'].values[0]
                teamKenpomAdjD = teamKenpom['AdjD'].values[0]
                teamKenpomAdjT = teamKenpom['AdjT'].values[0]
                stats = {}
                for stat in competitor['statistics']:
                    stats[stat['abbreviation']] = float(stat['displayValue'])
                if stats:
                    teamFgm = stats['FGM']
                    teamFga = stats['FGA']
                    team3pm = stats['3PM']
                    team3pa = stats['3PA']
                    teamFtm = stats['FTM']
                    teamFta = stats['FTA']
                    if competitor['homeAway'] == 'home':
                        homeID = teamID
                        homeName = teamName
                        homeScore = teamScore
                        homeWin = teamWin
                        homeKenpom = teamKenpomRank
                        homeRecord = teamRecord
                        homeKenpomAdjem = teamKenpomAdjem
                        homeKenpomAdjO = teamKenpomAdjO
                        homeKenpomAdjD = teamKenpomAdjD
                        homeKenpomAdjT = teamKenpomAdjT
                        homeFgm = teamFgm
                        homeFga = teamFga
                        home3pm = team3pm
                        home3pa = team3pa
                        homeFtm = teamFtm
                        homeFta = teamFta
                    else:
                        awayID = teamID
                        awayName = teamName
                        awayScore = teamScore
                        awayWin = teamWin
                        awayKenpom = teamKenpomRank
                        awayRecord = teamRecord
                        awayKenpomAdjem = teamKenpomAdjem
                        awayKenpomAdjO = teamKenpomAdjO
                        awayKenpomAdjD = teamKenpomAdjD
                        awayKenpomAdjT = teamKenpomAdjT
                        awayFgm = teamFgm
                        awayFga = teamFga
                        away3pm = team3pm
                        away3pa = team3pa
                        awayFtm = teamFtm
                        awayFta = teamFta
            # Insert row into games table if gameID doesn't already exist
            if not canceled and not nonD1 and pbpAvailable and homeID and awayID:
                conn.execute('''INSERT OR IGNORE INTO games (
                    id, date, home_id, away_id, home_name, away_name, home_score, away_score, neutral_site, home_win, away_win,
                    home_kenpom, away_kenpom, home_record, away_record, home_kenpom_adjem, away_kenpom_adjem, home_kenpom_adj_o,
                    away_kenpom_adj_o, home_kenpom_adj_d, away_kenpom_adj_d, home_kenpom_adj_t, away_kenpom_adj_t, home_fgm,
                    home_fga, home_3pm, home_3pa, home_ftm, home_fta
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (gameID, date, homeID, awayID, homeName, awayName, homeScore, awayScore, neutral, homeWin, awayWin,
                homeKenpom, awayKenpom, homeRecord, awayRecord, homeKenpomAdjem, awayKenpomAdjem, homeKenpomAdjO,
                awayKenpomAdjO, homeKenpomAdjD, awayKenpomAdjD, homeKenpomAdjT, awayKenpomAdjT, homeFgm, homeFga,
                home3pm, home3pa, homeFtm, homeFta))
                conn.commit()
conn.close()