#Web Scraping Steam Community Posts
import requests
from bs4 import BeautifulSoup
import boto3
import pandas as pd
import numpy as np
import json
import time
from pyvirtualdisplay import Display
from selenium import webdriver
#Constants
PUBG_APP_ID = 578080
DOTA2_APP_ID = 570
CSGO_APP_ID = 730

INSTANCE_NO = 1

user_agents = ['Mozilla/5.0 (Windows NT 10.0; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0',
               'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.6) Gecko/20070725 Firefox/2.0.0.6',
               'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3',
               'Mozilla/5.0 (Linux; U; Android 0.5; en-us) AppleWebKit/522+ (KHTML, like Gecko) Safari/419.3',
               'Mozilla/5.0 (iPhone; U; CPU like Mac OS X; en) AppleWebKit/420+ (KHTML, like Gecko) Version/3.0 Mobile/1A543a Safari/419.3',
               'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:31.0) Gecko/20130401 Firefox/31.0'
               'Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0',
               'Mozilla/5.0 (Windows NT 6.1; rv:27.3) Gecko/20130101 Firefox/27.3',
               'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36',
               'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2226.0 Safari/537.36']

#Build a virtual display for selenium
display = Display(visible = 0, size = (800,600))
display.start()

#Create selenium session to retrieve session ID
browser = webdriver.Firefox()
time.sleep(1)
browser.get('http://www.steamcommunity.com/app/578080/discussions/1/')
session_id = browser.execute_script('return g_sessionID')

#Configure cookies to display 50 posts per page
time.sleep(1)
browser.execute_script('Forum_SetTopicRepliesPerPage(50)')
time.sleep(1)
browser.execute_script('Forum_SetTopicsPerPage(50)')

#Create a requests session and populate its cookies with the discussion preferences
s = requests.Session()
time.sleep(1)
s.get('http://steamcommunity.com/app/578080/discussions/1/')
s.cookies['rgDiscussionPrefs'] = browser.get_cookie('rgDiscussionPrefs')['value']
default_cookies = s.cookies
default_headers = s.headers
#Close the browser
browser.close()

def remove_blockquotes(soup):
    while soup.find('blockquote'):
        soup.find('blockquote').extract()
    return soup

try:
    with open('threads{}.json'.format(INSTANCE_NO)) as f:
        threads = json.load(f)
except:
    print("Thread JSON file not found")
    input("Press any button to continue...")
    threads = []

try:
    with open('posts{}.json'.format(INSTANCE_NO)) as f:
        posts = json.load(f)
except:
    print("Post JSON file not found")
    input("Press any button to continue...")
    posts = []

n_completed = len(threads)
s3 = boto3.resource('s3')
sfp = s3.Bucket('steamforumposts')
sfp.download_file('threads_to_scrape{}.csv'.format(INSTANCE_NO), 'local.csv')
df = pd.read_csv('local.csv')
mapper = {'PUBG':PUBG_APP_ID, 'CS:GO':CSGO_APP_ID, 'DOTA2':DOTA2_APP_ID}
df['appid'] = df.game.map(mapper)
n_remaining = len(df) - n_completed
items = zip(df.appid.tail(n_remaining), df.thread_id.tail(n_remaining))
n_errors = 0
pages_before_break = np.random.randint(20,50)

print("Starting to scrape at position {} of assigned array".format(n_completed))

for i, ids in enumerate(items):
    s.cookies = default_cookies
    s.headers = default_headers
    pages_before_break -= 1
    sleepy_time = np.random.uniform(3,7) + np.random.exponential(6)
    if pages_before_break == 0:
        sleepy_time += np.random.rand() * 100
        pages_before_break = np.random.randint(20,50)
    default_headers['User-Agent'] = user_agents[np.random.randint(0,len(user_agents))]
    time.sleep(sleepy_time)
    response = requests.get('http://steamcommunity.com/app/{}/discussions/{}/{}/'.format(ids[0], 1 if ids[0] == PUBG_APP_ID else 0, ids[1]), headers = default_headers, cookies = default_cookies)

    while response.status_code != 200:
        n_errors += 1
        if n_errors > 2:
            raise Exception("After multiple retries, issue still persists. Exiting...")
        print("Status code {} received on thread number {}".format(response.status_code, i))
        time.sleep(60)
        headers = {'User-Agent': user_agents[np.random.randint(0,len(user_agents))]}
        response = requests.get('http://steamcommunity.com/app/{}/discussions/{}/{}/'.format(ids[0], 1 if ids[0] == PUBG_APP_ID else 0, ids[1]), headers = default_headers, cookies = default_cookies)
    

    
    n_errors = 0
    soup = BeautifulSoup(response.text, 'lxml')
    if not soup.find('span', 'topicstats_value'):
        threads.append({'thread_id':ids[1], 'content':None})
        continue
    
    n_posts = int(soup.find_all('span', 'topicstats_value')[-1].text.strip().replace(',', ''))
    n_pages = n_posts // 50
    author_name = soup.find('a', 'forum_op_author').text.strip()
    author_id = soup.find('a', 'forum_op_author')['href'].split('/')[-1]
    #Seconds since 01/01/1970
    post_time = int(soup.find('span', 'date')['data-timestamp'])
    post_title = soup.find('div', 'topic').text.strip()
    post_content = soup.find('div', 'forum_op').find('div', 'content').text.strip()
    replies = soup.find_all('div', 'commentthread_comment')
    
    threads.append({'thread_id':ids[1], 'author_id':author_id,'posted_on':post_time,
                    'title':post_title, 'content':post_content, 'replies':n_posts, 'game_id':ids[0]})
    posts.append({'author':author_name, 'author_id':author_id, 
                  'time':post_time, 'content':post_content,
                  'response_number':'#0', 'thread_id':ids[1]})
    for reply in replies:
        reply_author_name = reply.find('a', 'commentthread_author_link').text.strip()
        reply_author_id = reply.find('a', 'commentthread_author_link')['href'].split('/')[-1]
        reply_time = int(reply.find('span', 'commentthread_comment_timestamp')['data-timestamp'])
        reply_content = remove_blockquotes(reply).find('div', 'commentthread_comment_text').text.strip()
        reply_no = reply.find('div', 'forum_comment_permlink').text.strip()
        posts.append({'author':reply_author_name, 'author_id':reply_author_id, 
                          'time':reply_time, 'content':reply_content,
                          'response_number':reply_no, 'thread_id':ids[1]})
    
    for page in range(n_pages):
        headers = {'User-Agent': user_agents[np.random.randint(0,len(user_agents))]}
        pages_before_break -= 1
        sleepy_time = np.random.uniform(5,7) + np.random.exponential(4)
        if pages_before_break == 0:
            sleepy_time += np.random.rand() * 100
            pages_before_break = np.random.randint(25,50)
        time.sleep(sleepy_time)
        response = requests.get('http://steamcommunity.com/app/{}/discussions/{}/{}/?ctp={}'.format(ids[0], 1 if ids[0] == PUBG_APP_ID else 0, ids[1], page+2), headers = default_headers, cookies = default_cookies)
        while response.status_code != 200:
            n_errors += 1
            if n_errors > 2:
                raise Exception("After multiple retries, issue still persists. Exiting...")
            print("Status code {} received on thread number {}".format(response.status_code, i))
            time.sleep(60)
            headers = {'User-Agent': user_agents[np.random.randint(0,len(user_agents))]}
            response = requests.get('http://steamcommunity.com/app/{}/discussions/{}/{}/?ctp={}'.format(ids[0], 1 if ids[0] == PUBG_APP_ID else 0, ids[1], page+2), headers = default_headers, cookies = default_cookies)
             
        n_errors = 0
        soup = BeautifulSoup(response.text, 'lxml')
        replies = soup.find_all('div', 'commentthread_comment')
        
        for reply in replies:
            reply_author_name = reply.find('a', 'commentthread_author_link').text.strip()
            reply_author_id = reply.find('a', 'commentthread_author_link')['href'].split('/')[-1]
            reply_time = int(reply.find('span', 'commentthread_comment_timestamp')['data-timestamp'])
            reply_content = remove_blockquotes(reply).find('div', 'commentthread_comment_text').text.strip()
            reply_no = reply.find('div', 'forum_comment_permlink').text.strip()
            posts.append({'author':reply_author_name, 'author_id':reply_author_id, 
                              'time':reply_time, 'content':reply_content,
                              'response_number':reply_no, 'thread_id':ids[1]})
    if i % 10 == 0:
        print("After {} iterations, writing {} threads and {} posts".format(i+1, len(threads), len(posts)))
        with open('threads{}.json'.format(INSTANCE_NO), 'w') as f:
            f.write(json.dumps(threads))
        with open('posts{}.json'.format(INSTANCE_NO), 'w') as f:
            f.write(json.dumps(posts))
        print(response.headers)
        print('\n\n')
        print(response.request.headers)    
        print('\n\n')

print("SCRAPING COMPLETED! {} threads and {} posts gathered".format(len(threads), len(posts)))

