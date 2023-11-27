import json
from datetime import datetime
import os
import time
import requests

# Load data.json into a Python object
with open('data.json') as file:
    data = json.load(file)
    calendar = data['leagues'][0]['calendar']

# Convert list of dates to datetime objects
formatted_dates = []
for date_str in calendar:
    date_obj = datetime.strptime(date_str, '%Y-%m-%dT%H:%MZ')
    formatted_date_str = date_obj.strftime('%Y%m%d')
    formatted_dates.append(formatted_date_str)


for date_string in formatted_dates:
    # Create directory if it doesn't exist
    directory = f"data/days/{date_string}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    if not os.path.exists(f"{directory}/raw_{date_string}.json"):
        time.sleep(2.5) #rate limit
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={date_string}&groups=50"
        response = requests.get(url)
        json_data = response.json()
        with open(f"{directory}/raw_{date_string}.json", "w") as f:
            json.dump(json_data,f)

n_games = 0
dayfiles = []
days = []
for f in os.walk('data/days'):
    if f[0] and f[2]:
        days.append(f[0])
        dayfiles.append(f[2])

for dir, fnames in zip(days,[f for f in dayfiles]):
    for fname in fnames:
        with open(f'{dir}/{fname}') as infile:
            data = json.load(infile)
            if 'events' in data.keys():
                n_games += len(data['events'])

print(n_games)