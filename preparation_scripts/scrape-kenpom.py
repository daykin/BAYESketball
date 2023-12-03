import os
from openpyxl import LXML
from waybackpy import WaybackMachineCDXServerAPI, WaybackMachineSaveAPI
import glob
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import pandas as pd

url = "https://kenpom.com"

user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
availability_api = WaybackMachineCDXServerAPI(url, user_agent)


days = glob.glob('data/days/*')

session = requests.Session()
retry = Retry(total=1000, backoff_factor=0.5)
session.mount('http://', HTTPAdapter(max_retries=retry))
session.mount('https://', HTTPAdapter(max_retries=retry))

for day in days:
    dts = day[day.rfind('/')+1:]
    dt = datetime.strptime(dts, '%Y%m%d')

    while not os.path.exists('data/days/' + dts + '/kenpom.html'):
        try:
            result = availability_api.near(dt.year, dt.month, dt.day-1)
            url = result.archive_url
            time.sleep(4.5)
            #Get the webpage without wayback machine stuff
            url = url[:url.find('/http')] + 'id_' + url[url.find('/http'):]
            r = session.get(url, headers={'User-Agent': user_agent},allow_redirects=True)
            with open('data/days/' + dts + '/kenpom.html', 'w') as f:
                f.write(r.text)
                print('Saved ' + dts + '/kenpom.html')
                #rate limit to <15 requests per minute
                time.sleep(4.5)
        except:
            print("Connection refused, back off for 1 minute 10 seconds")
            time.sleep(70)
    with open('data/days/' + dts + '/kenpom.html','r') as f:
        try:
            tables = pd.read_html(f.read())
            #write the df to a csv
            tables[0].to_csv('data/days/' + dts + '/kenpom.csv',index=False)
        except:
            pass
    if not os.path.exists('data/days/' + dts + '/kenpom.csv'):
        with open('data/days/' + dts + '/kenpom.csv','r') as f:
            try:
                df = pd.read_csv(f)
                df = df.dropna(axis=0,how='all')
                df = df.dropna(axis=1,how='all')
                df.to_csv('data/days/' + dts + '/kenpom.csv',index=False)
            except:
                pass
    if os.path.exists('data/days/' + dts + '/kenpom.csv'):
        with open('data/days/' + dts + '/kenpom.csv','r') as f:
            try:
                lines = f.readlines()
                lines = lines[17:]
                for line in lines[1:]:
                    if line.find('Rk')!=-1:
                        lines.remove(line)
                lines = [line for line in lines if not line.startswith(',,')]
                with open('data/days/' + dts + '/kenpom_cleaned.csv','w') as f:
                    f.writelines(lines)
            except KeyboardInterrupt:
                raise
            except:
                pass
    if os.path.exists('data/days/' + dts + '/kenpom_cleaned.csv'):
        with open('data/days/' + dts + '/kenpom_cleaned.csv','r') as f:
            df = pd.read_csv(f)
            df = df.dropna(axis=0,how='all')
            df = df.dropna(axis=1,how='all')
            #for any team names that have a comma in them, remove the comma
            df['Team'] = df['Team'].str.replace(',','')
            #for any team names that have a seed in them, remove the seed
            df['Team'] = df['Team'].str.replace('\d','', regex=True)
            #for any team names that have a space at the end, remove the space
            df['Team'] = df['Team'].str.rstrip()
            #write the df to a csv
            df.to_csv('data/days/' + dts + '/kenpom_cleaned.csv',index=False)