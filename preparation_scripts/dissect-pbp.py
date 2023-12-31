import json
import sqlite3
from math import floor
import os

games_db = sqlite3.connect('data/ncaa.db')
cg=games_db.cursor()

ids = [id[0] for id in cg.execute('SELECT id FROM games').fetchall()]

conn = sqlite3.connect('data/pbp.db')
pc = conn.cursor()

HOME = 0
AWAY = 1

def check_home_away(play):
    return int(play['homeAway']=='away')

skip = []


pc.execute(f'DROP TABLE IF EXISTS pbp')
pc.execute(f'''CREATE TABLE pbp (
                playid INTEGER,
                gameid INTEGER,
                time_interval INTEGER,
                time_minutes INTEGER,
                time_seconds INTEGER,
                description TEXT,
                home_score INTEGER,
                away_score INTEGER,
                scoring_play INTEGER,
                who INTEGER,
                possession INTEGER,
                home_fgm INTEGER,
                home_fga INTEGER,
                home_3pm INTEGER,
                home_3pa INTEGER,
                home_ftm INTEGER,
                home_fta INTEGER,
                home_oreb INTEGER,
                home_to INTEGER,
                home_possessions REAL,
                away_fgm INTEGER,
                away_fga INTEGER,
                away_3pm INTEGER,
                away_3pa INTEGER,
                away_ftm INTEGER,
                away_fta INTEGER,
                away_oreb INTEGER,
                away_to INTEGER,
                away_possessions REAL)''')
n=0
for gameid in ids:
    if os.path.exists(f'data/pbp/{gameid}_raw'):
        with open(f'data/pbp/{gameid}_raw', 'r') as f:
            #get json embedded in html - find first instance of '{ and last instance of }'
            html = f.read()
            json_start = html.find('{')
            json_end = html.rfind('}')+1
            json_str = html[json_start:json_end]
            try:
                page = json.loads(json_str)
            except json.decoder.JSONDecodeError:
                print("JSONDecodeError, skipping")
                skip.append(gameid)
                continue
            #find start of play-by-play data
            pbp = page['page']['content']['gamepackage']['pbp']['playGrps']
            if len(pbp)!= 2:
                print("Incomplete or OT game, skipping")
                skip.append(gameid)
            else:
                home_3pm = 0
                home_3pa = 0
                away_3pm = 0
                away_3pa = 0
                home_fgm = 0
                home_fga = 0
                away_fgm = 0
                away_fga = 0
                home_ftm = 0
                home_fta = 0
                away_ftm = 0
                away_fta = 0
                home_oreb = 0
                away_oreb = 0
                home_to = 0
                away_to = 0
                home_possessions = 0.0
                away_possessions = 0.0
                for half in range(2):
                    h = pbp[half]
                    for play_zip in enumerate(h):
                        idx = play_zip[0]
                        play = play_zip[1]
                        id = play['id']
                        half = play['period']['number']
                        time_minutes = int(play['clock']['displayValue'].split(':')[0])
                        time_seconds = int(play['clock']['displayValue'].split(':')[1])
                        time_total = time_minutes*60 + time_seconds + ((1-(half//2))*1200)
                        #subdivide last 30 seconds into 3 segments
                        if time_total <= 30:
                            time_segment = 41 - time_total//10
                        else:
                            time_segment = int(floor((2400-time_total)/60))
                        home_score = int(play['homeScore'])
                        away_score = int(play['awayScore'])
                        scoring_play = 0
                        three = 0
                        two = 0
                        free = 0
                        stoppage = 0
                        try:
                            home_away = check_home_away(play)
                        except KeyError:
                            stoppage = 0
                            continue
                        #determine resulting possession
                        #Home_away got ball
                        # Use KenPom possession formula: (FGA – OR) + TO + (.475 * FTA)
                        try:
                            ptext = play['text'].lower()
                        except KeyError:
                            ptext = "No Text"
                            print("No text?")
                            print(gameid)
                            print(play)
                        if('rebound' in ptext):
                            if home_away == HOME:
                                possession = HOME
                            else:
                                possession = AWAY
                            if 'offensive' in ptext:
                                if home_away == HOME:
                                    home_oreb += 1
                                else:
                                    away_oreb += 1
                        #home_away gave away ball
                        elif('turnover' in ptext):
                            if home_away == HOME:
                                possession = AWAY
                                home_to += 1
                            else:
                                possession = HOME
                                away_to += 1
                        #home_away got ball
                        elif('steal' in ptext):
                            if home_away == HOME:
                                possession = HOME
                            else:
                                possession = AWAY
                        elif('jump ball' in ptext):
                            possession = home_away
                        elif 'scoringPlay' in play:
                            #determine possession after scoring play
                            if play['scoringPlay']:
                                scoring_play = 1
                                #if next play is a foul, and the foul is on the other team, then the scoring team retains possession
                                if idx+1 < len(h):
                                    next_play = h[idx+1]
                                    if 'text' in next_play and 'foul' in next_play['text'].lower():
                                        if home_away == check_home_away(next_play):
                                            possession = int(not home_away)
                                        else:
                                            possession = home_away
                                    else:
                                        possession = int(not home_away)
                                if 'made three' in ptext:
                                    three = 1
                                    if home_away == HOME:
                                        home_3pm += 1
                                        home_3pa += 1
                                        home_fgm += 1
                                        home_fga += 1
                                    else:
                                        away_3pm += 1
                                        away_3pa += 1
                                        away_fgm += 1
                                        away_fga += 1
                                elif 'made free' in ptext:
                                    free = 1
                                    if home_away == HOME:
                                        home_ftm += 1
                                        home_fta += 1
                                    else:
                                        away_ftm += 1
                                        away_fta += 1
                                #any other 2 point shot
                                else:
                                    two = 1
                                    if home_away == HOME:
                                        home_fgm += 1
                                        home_fga += 1
                                    else:
                                        away_fgm += 1
                                        away_fga += 1
                        elif 'missed three' in ptext:
                            three = 1
                            if home_away == HOME:
                                home_3pa += 1
                                home_fga += 1
                            else:
                                away_3pa += 1
                                away_fga += 1
                        elif 'missed free' in ptext:
                            free = 1
                            if home_away == HOME:
                                home_fta += 1
                            else:
                                away_fta += 1
                        #fall through: any other 2 point shot
                        elif 'missed' in ptext:
                            two = 1
                            if home_away == HOME:
                                home_fga += 1
                            else:
                                away_fga += 1
                    #populate table with play
                        if not stoppage:
                            home_possessions = float(home_fga - home_oreb + home_to + 0.45*home_fta)
                            away_possessions = float(away_fga - away_oreb + away_to + 0.45*away_fta)
                            pc.execute('''INSERT INTO pbp VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                        (id, gameid, time_segment,time_minutes,time_seconds, ptext, home_score, away_score, scoring_play, home_away, possession,
                                        home_fgm, home_fga, home_3pm, home_3pa, home_ftm, home_fta, home_oreb, home_to, home_possessions, away_fgm, away_fga, away_3pm, away_3pa,
                                        away_ftm, away_fta, away_oreb, away_to, away_possessions))
                            
                            n += 1
                            if n % 1000 == 0:
                                print(n)

print(n)
for id in skip:
    print("removing " + str(id))
    cg.execute(f'DELETE FROM games WHERE id={id}')
conn.commit()
conn.close()