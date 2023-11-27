import sqlite3
import requests
import os
import time
import numpy as np
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

overall = sqlite3.connect('data/ncaa.db')
pbp = sqlite3.connect('data/pbp.db')

c = overall.cursor()

ids = [id[0] for id in c.execute('SELECT id FROM games').fetchall()]


user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"

# Configure Chrome options for headless browsing
chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = './Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing'
chrome_options.add_argument("--headless")  # Run Chrome in headless mode
# Set path to chromedriver executable
chromedriver_path = "./chromedriver"
# Initialize ChromeDriver instance
service = Service(executable_path='./chromedriver')
driver = webdriver.Chrome(service=service, options=chrome_options)

#normal random offset with mean 1 and std 0.25
def random_offset():
    return np.random.normal(1, 0.25)

for id in ids:
    url = f"https://www.espn.com/mens-college-basketball/playbyplay/_/gameId/{id}?_xhr=1"
    # Retrieve play-by-play data from URL in a headless browser
    if not os.path.exists(f"data/pbp/{id}_raw"):
        driver.get(url)
        # save to data/pbp/{id}.json
        if "Access Denied" in driver.page_source:
            print("Access Denied for " + url)
            break
        with open(f"data/pbp/{id}_raw", "w") as f:
            f.write(driver.page_source)
            print(f"Saved {id}")
        time.sleep(min(0.5,1+random_offset()))

driver.quit()  # Close the headless browser
    
