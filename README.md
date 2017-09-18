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

Once an individual EC2 instance had finished its task, it wrote its results to an S3 bucket using boto3, and the data generating process was complete!

### Data cleaning and feature generation:
Communications on forums are inherently messy.  People type things incorrectly (whether purposefully or not), and make frequent use of jargon, acronyms, and sarcasm.  Given the timeframe of this project, I ended up utilizing TFIDF with a custom stopwords list and stemming.  Given more time, I would have tried semantic analysis techniques like LDA or HMMs.

The first big hurdle I faced was the fact that I did not have a response (useful / not useful) variable, which made supervised learning impossible.  I had nearly a million posts, so any kind of hand-labeling solution was obviously off the table.  In the end, my solution was to find patch notes in a specific window after the post was made, and use cosine similarity to see if the post discussed topics related to the changes developers were making to the game.

Exploring the data, I found some interesting facts.  For one, the games had very different lifespans:  DOTA2 had several years of historical posts available, but PUBG had only about half a year.  People who were the OP (original poster) of a thread were generally more helpful than repliers.  Even though Steam allows users to change their forum names, the overwhelming majority (over 99%) of users had posted under just a single name.

To clean the data, I removed <blockquote> elements and hyperlinks, before applying a stemmed version of sklearn's TfidfVectorizer.  Additionally, I created features representing the poster's capitalization and foul language usage, as well as the lengths of the post content and title.

### Model building
I built a random forest model out of my engineered features + vectorized features from the post title and content.  This model had the best performance out of the box.  Given more time, I would have tried a variety of modeling methodologies (logistic regression, SVM, neural network), but this took a backseat as I wanted to spend more time on the dashboard application and automation in AWS.

### Dashboard
Using HTML, CSS, and jQuery, I hand-crafted a dashboard app which presents top-rated posts and threads along with summary statistics.  This was a great experience, and I feel like I learned a good deal about HTTP requests and Flask.  It's amazing to me how quickly one can spin up a machine learning backed web service!

### Amazon Web Services
I made extensive use of AWS throughout the entire lifecycle of this project.  Whether writing or reading results from S3, or spinning up multiple instances to scrape the Steam forums in parallel, to having my webserver spin off a new virtual machine to scrape new posts, persist them, then shut itself down.  The power of AWS is incredible, and I plan to continue familiarizing myself with them.




