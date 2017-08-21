#Patch Notes Web Scraper
import pandas as pd
import numpy as np
import json
import requests
import bs4
import time
import os

#%%
#Scrape CS:GO patch notes
base_url = "http://blog.counter-strike.net/index.php/category/updates/page/"
i = 1
results = []
while True:
    page = requests.get(base_url + str(i))
    if page.status_code != 200:
        print("Received status code {} on page {}".format(page.status_code, i))
        break
    
    text = page.text
    soup = bs4.BeautifulSoup(text, "lxml")
    posts = soup.find_all("div", "inner_post")
    
    
    filtered_posts = [post for post in posts if "Pre-Release" not in post.find('a').text]
    for post in filtered_posts:
        d = {}
        d["post_date"] = post.find("p", "post_date").text[:10]
        d["topics"] = set()
        d["content"] = []
        category = None
        subcategory = None
        for paragraph in post.find_all("p")[1:]:
            for line in paragraph.text.split('\n'):
                if line == line.upper() or ('[' in line and ']' in line):
                    category = line.strip("[] ")
                    d["topics"].add(category)
                elif category:
                    cleaned_change = line.replace("-", " ").replace("_", " ")
                    cleaned_change = "".join([letter.lower() for letter in cleaned_change if letter.isalnum() or letter.isspace()]).strip()
                    if line.strip().startswith("--") or line.strip().startswith("– –") or line.strip().startswith("—"):
                        d["content"].append({"topic":subcategory, "change":cleaned_change})
                        d["topics"].add(subcategory)
                    else:
                        subcategory = line.strip("-–—[]: ").split()[0].strip("-[]: ").upper()                  
                        d["content"].append({"topic":category, "change":cleaned_change})
        results.append(d)
        print(d["post_date"])
        print(d["topics"])
        print()

    i += 1
    if i % 5 == 0:
        print("On page {}".format(i))
    time.sleep(5)

results = results[:-1]
for item in results:
    item['topics'] = list(item['topics'])
result_string = json.dumps(results)
with open("csgo_notes.json", "w") as f:
    f.write(result_string)


#%%
#Scrape PUBG patch notes
results = []
base_url = "c:/users/john/desktop/new folder/"
links = [link for link in os.listdir(base_url)]
for link in links:
    with open(base_url + link, encoding = "utf-8") as f:
        text = f.read()
    soup = bs4.BeautifulSoup(text, "lxml").find_all('div', 'md')[1]
    d = {}
    d["post_date"] = soup.find_all('p')[1].text.split()[-1]
    d["content"] = []
    d["topics"] = set()
    for line in soup:
        if line.name in ['h2','h1']:
            category = line.text[:-1]
            d["topics"].add(category)
            if category.startswith("Links"):
                break
        if line.name == 'ul':
            for child in line.find_all('li'):
                d["content"].append({"topic":category, "change": "".join([letter for letter in child.text if letter.isalnum() or letter.isspace()])})
    
    print(d["topics"])
    results.append(d)

for item in results:
    item['topics'] = list(item['topics'])
result_string = json.dumps(results)
with open("c:/users/john/desktop/ambient/pubg_notes.json", "w") as f:
    f.write(result_string)
    
#%%
#Scrape DOTA 2 patch notes
#results = []
base_url = "https://dota2.gamepedia.com"
page_to_get = "/August_19,_2017_Patch"
while True:
    response = requests.get(base_url + page_to_get)
    if response.status_code != 200:
        print("Received status code {} on page {}".format(page.status_code, page_to_get))
        break
    
    d = {}
    d["content"] = []
    d["topics"] = set()

    soup = bs4.BeautifulSoup(response.text, "lxml")
    
    d["post_date"] = " ".join(soup.find('h1', 'firstHeading').text.split()[:-1])
    
    soup = soup.find('div', 'mw-content-ltr')
    try:
        page_to_get = soup.find('td').find('a')['href']
    except:
        print("Couldn't find previous patch on page {}".format(page_to_get))
        break

    
    soup = soup.find('div')
    category = None
    
    for line in soup.children:
        if isinstance(line, bs4.NavigableString):
            continue
        elif line.name in ['h1','h2','h3','h4']:
            category = line.text
        elif line.name == 'ul':
            for change in line.find_all('li'):
                d['content'].append({'topic':category, 'change':change.text}) 
                d["topics"].add(category)
    
    results.append(d)
    print("Patch on {}\nTopics {}".format(d['post_date'], d['topics']))
    time.sleep(5)

for item in results:
    item['topics'] = list(item['topics'])
result_string = json.dumps(results)
with open("c:/users/john/desktop/ambient/dota2_notes.json", "w") as f:
    f.write(result_string)