#Web Scraping Steam Community Posts
import requests

#Constants
PUBG_APP_ID = 578080
DOTA2_APP_ID = 570
CSGO_APP_ID = 730


#Build a virtual display for selenium
from pyvirtualdisplay import Display
display = Display(visible = 0, size = (800,600))
display.start()

#Create selenium session to retrieve session ID
from selenium import webdriver
browser = webdriver.Firefox()
browser.get('http://www.steamcommunity.com/app/578080/discussions/1/')
session_id = browser.execute_script('return g_sessionID')

#Configure cookies to display 50 posts per page
browser.execute_script('Forum_SetTopicRepliesPerPage(50)')
browser.execute_script('Forum_SetTopicsPerPage(50)')

#Create a requests session and populate its cookies with the discussion preferences
s = requests.Session()
s.get('http://steamcommunity.com/app/578080/discussions/1/')
s.cookies['rgDiscussionPrefs'] = browser.get_cookie('rgDiscussionPrefs')['value']

#Close the browser
browser.close()

#Now we're free to start using requests to scrape the forums!
#Topic class == 'forum_topic'
#Comment class == 'commentthread_comment_content 2nd child <div>
#Author class == 'commentthread_comment_author
#Timestamp inside author. span class == commentthread_comment_timestamp inside title or data-timestamp attribute
#Author SteamID inside anchor tag, class == commentthread_author_link at the end of href attribute

#Above is just for replies:  OP is div class == forum_op
#OP Author in anchor tag class == forum_op_author href has steam id, .text has name
#img tag indicates if they own the game
#span class == date shows time of posting
#div class == topic gives topic
#div class == content .text has all content

#<blockquote> elements contain users quoting other users

#query parameter ?ctp=x gives the page number for thread replies
#query parameter ?fp=x gives the page number for posts

#Issues to consider:
    #ignore non-english posts
    #how to find older postings