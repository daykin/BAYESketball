import pandas as pd
import glob
import json
import os

#Add the ESPN 'Team ID' to the KenPom data

teamIDs = {}
kp_to_espn_names = {'Bethune Cookman':'Bethune-Cookman','Maryland Eastern Shore':'Maryland-Eastern Shore','Arkansas Pine Bluff':'Arkansas-Pine Bluff','Tennessee Martin':'UT Martin','Texas A&M Corpus Chris':'Texas A&M-Corpus Christi','San Jose St.':'San José St.','Houston Baptist':'Houston Christian','St. Thomas':'St. Thomas-Minnesota','St. Francis NY':'St. Francis Brooklyn','USC Upstate':'South Carolina Upstate','Grambling St.':'Grambling','Nebraska Omaha':'Omaha','McNeese St.':'McNeese','Southeastern Louisiana':'SE Louisiana','Dixie St.':'Utah Tech', 'FIU':'Florida International','Illinois Chicago':'UIC', 'Cal St. Northridge':'Cal State Northridge', 'Loyola MD':'Loyola Maryland', 'Albany':'UAlbany','American':'American University','Hawaii':'Hawai\'i','UMKC':'Kansas City','Louisiana Monroe':'UL Monroe','LIU':'Long Island University','St. Francis PA':'St. Francis (PA)','Gardner Webb':'Gardner-Webb','UTSA':'Texas-San Antonio','VMI':'Virginia Military Institute','Nicholls St.':'Nicholls', 'USC':'Southern California','Cal Baptist':'California Baptist', 'Penn': 'Pennsylvania','Seattle':'Seattle U', 'Cal St. Bakersfield':'Cal State Bakersfield', 'Cal St. Fullerton':'Cal State Fullerton','Sam Houston St.':'Sam Houston', 'Miami FL':'Miami','Miami OH': 'Miami (OH)', 'Mississippi': 'Ole Miss', 'N.C. State': 'NC St.','Connecticut':'UConn','St. John\'s':'St. John\'s (NY)','Saint Louis':'Saint Louis','Saint Joseph\'s':'Saint Joseph\'s','Saint Mary\'s':'Saint Mary\'s (CA)','Saint Peter\'s':'Saint Peter\'s','SMU':'Southern Methodist','Southern Miss':'Southern Mississippi','TCU': 'Texas Christian','UTEP':'Texas-El Paso','UCLA':'UCLA','VCU':'Virginia Commonwealth','Virginia Tech':'Virginia Tech','Western Carolina':'Western Carolina','Western Illinois':'Western Illinois','Western Kentucky':'Western Kentucky','Western Michigan':'Western Michigan','Wichita State':'Wichita State','William & Mary':'William & Mary','Wisconsin':'Wisconsin','Green Bay':'Wisconsin-Green Bay','Milwaukee':'Wisconsin-Milwaukee','Wofford':'Wofford','Wright State':'Wright State','Wyoming':'Wyoming','Xavier':'Xavier','Yale':'Yale','Youngstown State':'Youngstown State'}
espn_to_kp_names = {v: k for k, v in kp_to_espn_names.items()}


for dir in glob.glob('data/days/*'):
    dts = dir[dir.rfind('/')+1:]
    with open (f"data/days/{dts}/raw_{dts}.json") as f:
        data = json.load(f)
        if 'events' in data.keys():
            #human readable format
            if not os.path.exists(f"data/days/{dts}/events_{dts}.json"):
                with open(f"data/days/{dts}/events_{dts}.json", "w") as f:
                    json.dump(data['events'],f,indent=4)
            events = data['events']
            for event in events:
                comps = event['competitions']
                competitors = comps[0]['competitors']
                for team in competitors:
                    id = int(team['id'])
                    name = team['team']['location']
                    #if name ends in 'State', change it to 'St.'
                    if name.endswith('State'):
                        name = name.replace('State','St.')
                    if name in espn_to_kp_names.keys():
                        #print("Changing " + name + " to " + espn_to_kp_names[name])
                        name = espn_to_kp_names[name]
                    if id not in teamIDs.keys():
                        teamIDs[id] = name

for dir in glob.glob('data/days/*'):
    dts = dir[dir.rfind('/')+1:]
    with open(f'data/days/{dts}/kenpom_cleaned.csv', 'r') as kp:
        df = pd.read_csv(kp)
        #check if 'TeamID' column already exists
        if not 'TeamID' in df.columns:
        #create 'TeamID' column as integer
            df['TeamID'] = 0
            for index, row in df.iterrows():
                if row['Team'] in teamIDs.values():
                    for id, name in teamIDs.items():
                        if row['Team'] == name:
                            df.at[index,'TeamID'] = int(id)
                else:
                    print("Team not found: " + row['Team'])
            df.to_csv(f'data/days/{dts}/kenpom_cleaned_ids.csv',index=False)
    #move kenpom_cleaned_ids.csv to kenpom_cleaned.csv
    os.rename(f'data/days/{dts}/kenpom_cleaned_ids.csv',f'data/days/{dts}/kenpom_cleaned.csv')

