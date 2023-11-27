import json
import requests

url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates=2022"

response = requests.get(url)
json_data = response.json()

# Save the JSON data as a file
with open("data.json", "w") as file:
    json.dump(json_data, file)

