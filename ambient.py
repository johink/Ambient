import psycopg2
import os
import pandas as pd
import numpy as np
import sqlalchemy

get_first = lambda x: x.iloc[0]

def date_helper(post_time):
    datediff = pd.datetime.now() - post_time
    if datediff.days == 0:
        hours = datediff.total_seconds() / 3600
        if hours == 0:
            return "Now"
        elif hours == 1:
            return "An hour ago"
        else:
            return "{} hours ago".format(hours)
    elif datediff.days <= 31:
        if datediff.days == 1:
            return "Yesterday"
        else:
            return "{} days ago".format(datediff.days)
    else:
        return post_time.strftime("%b %d, %Y")

class AmbientDataModel(object):
    def __init__(self):
        self.conn = None
        self.cur = None
        self.engine = sqlalchemy.create_engine("postgresql+psycopg2://{}:{}@localhost/{}".format(os.environ["DBUSER"], os.environ["DBPASS"], os.environ["DBNAME"]))
        self.setup()

    def setup(self):
        self.raw_data = pd.read_sql(
"""
SELECT posts.author_name, posts.content, posts.posted_on, posts.response_num, posts.thread_id, posts.usefulness, threads.title, threads.game_id, threads.num_replies, threads.posted_on AS creation_date
FROM posts
INNER JOIN threads ON posts.thread_id = threads.thread_id;
""", 
self.engine)
        self.raw_data.posted_on = pd.to_datetime(self.raw_data.posted_on, unit='ms')
        self.game_set = set(self.raw_data.game_id.unique())

        self.thread_weights = self.raw_data.groupby('thread_id').agg({'usefulness':np.mean, 'response_num': len, 'title':get_first, 'game_id':get_first, 'author_name':get_first, 'num_replies':get_first, 'creation_date':get_first})
        self.thread_weights.usefulness *= 1 + np.log(self.thread_weights.response_num)
        self.thread_weights.drop('response_num', axis = 1, inplace = True)
        self.thread_weights.rename(columns = {"creation_date":"posted_on"}, inplace = True)
        self.thread_weights.sort_values('usefulness', ascending = False, inplace = True)
        self.thread_weights = self.thread_weights.reset_index().rename(columns = {"index":"thread_id"})
        self.thread_weights.posted_on = pd.to_datetime(self.thread_weights.posted_on, unit='s')

        self.raw_data.posted_on = self.raw_data.posted_on.apply(date_helper)
        self.thread_weights.posted_on = self.thread_weights.posted_on.apply(date_helper)

        self.mapper = {
               570 : "DOTA 2",
               730 : "Counter-Strike: Global Offensive",
   578080 : "Player Unknown's Battlegrounds"
  }


    def _grab_db_conn(self):
        self.conn = psycopg2.connect("dbname={} user={} password={}".format(os.environ["DBNAME"], os.environ["DBUSER"], os.environ["DBPASS"]))
        self.cur = self.conn.cursor()

    def _close_db_conn(self):
        self.conn.commit()
        self.cur.close()
        self.conn.close()

    def check_validity(self, game_id):
        return game_id in self.game_set

    def get_thread_data(self, game_id):
        return self.thread_weights[self.thread_weights.game_id == game_id].head(100).to_dict('records')

    def get_post_data(self, game_id):
        return self.raw_data[self.raw_data.game_id == game_id].sort_values('usefulness', ascending = False).head(100).to_dict('records')

    def get_other_links(self, game_id):
        return [{"game_id" : gid, "game_name" : self.mapper[gid] } for gid in self.game_set if gid != game_id]
 
    def vote_post(self, thread_id, response_num, score):
        self._grab_db_conn()
        print("Voting post #{} in thread {} as {}".format(response_num, thread_id, score))
        query = """
INSERT INTO training (content, response_num, thread_id, posted_on, score, votes)
SELECT content, response_num, thread_id, to_timestamp(posted_on/1000), {}, 1 
FROM posts 
WHERE thread_id = {} AND response_num = {} 
ON CONFLICT (thread_id, response_num, score) 
DO UPDATE SET votes = training.votes + 1;
""".format(score, thread_id, response_num)
        print(query)
        self.cur.execute(query)
        self._close_db_conn()
