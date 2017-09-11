import psycopg2
import os
import pandas as pd
import numpy as np
import sqlalchemy

get_first = lambda x: x.iloc[0]

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
        self.game_set = set(self.raw_data.game_id.unique())

        self.thread_weights = self.raw_data.groupby('thread_id').agg({'usefulness':np.mean, 'response_num': len, 'title':get_first, 'game_id':get_first, 'author_name':get_first, 'num_replies':get_first, 'creation_date':get_first})
        self.thread_weights.usefulness *= 1 + np.log(self.thread_weights.response_num)
        self.thread_weights.drop('response_num', axis = 1, inplace = True)
        self.thread_weights.rename(columns = {"creation_date":"posted_on"}, inplace = True)
        self.thread_weights.sort_values('usefulness', ascending = False, inplace = True)




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
  
