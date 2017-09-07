# Ambient
### Cut out the noise and find actionable forum posts

User feedback can be extremely valuable, but often it is hard to find amidst the sea of complaining and trolling on web forums.  My goal was to attempt to make this feedback easier to find.  As an avid gamer, I chose to focus my efforts on Steam's gaming forums, and to reduce the scope I pulled posts for the three most popular games.

The three games are:
* DOTA 2
* Counter-Strike: Global Offensive
* Player Unknown's Battlegrounds

### Gathering the data:
The forums for the three selected games are extremely active.  This was very helpful from a data quantity standpoint, but it introduced another issue:  Without using the search functionality, one isn't able to find any posts more than a couple days old.

Therefore, the gathering process had to be split into two parts.  The first task was to harvest the ID numbers of individual threads.  This was quite time-consuming, as only ten threads could be displayed per page, and many had too few replies to be useful (I filtered out any posts that didn't have at least 2 replies).  To help ensure a robust sample of posts, I ran both generic searchterms like "who", "what", "where", as well as game-specific language like "OP", "fps", and "champ".  Once the script was executing properly, I spun up six separate EC2 instances on Amazon Web Services to conduct the scraping in parallel.

After sampling, I had the IDs of roughly 60,000 threads, which I would later discover had anywhere from 2 to over 40,000 replies.  After some experimentation with Selenium, I was able to obtain 50 replies per request instead of the default 15.  I then used the requests library along with BeautifulSoup to parse the responses and pull out date, content, etc., which I again parallelized over my six EC2 instances.

(Technical note here, for any search engine indexer... maybe this can help someone:  
When using the requests library's Session object, after a couple hundred GET requests all six of my instances mysteriously got the same error:  HTTP Code 413.  I'd never heard of this one, but it occurs when the server rejects your request for being too large.  This error didn't make any sense in my case, because GET requests don't have a message body.  Turns out, Steam was augmenting a cookie which indicated "recently viewed threads" with every request, which eventually got so large that the server rejected it!)

Once an individual EC2 instance had finished its task, it wrote its results to an S3 bucket using 

