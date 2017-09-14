import pandas as pd
import numpy as np
import boto3
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from Stemmer import Stemmer
import re
import string
import scipy
import pickle
import sqlalchemy
import os
import psycopg2

dbuser = os.environ["DBUSER"]
dbname = os.environ["DBNAME"]
dbpass = os.environ["DBPASS"]

engine = sqlalchemy.create_engine('postgresql+psycopg2://{}:{}@localhost/{}'.format(dbuser, dbpass, dbname))

s3 = boto3.resource('s3')
sfp = s3.Bucket("steamforumposts")
#for i in range(1,7):
#    thread_name = "threads{}.json".format(i)
#    sfp.download_file(thread_name, "../data/"+thread_name)

#sfp.download_file('posts.pkl','../data/posts.pkl')

threads = []

for i in range(1,7):
    thread_name = "../data/threads{}.json".format(i)
    threads.append(pd.DataFrame(json.load(open(thread_name))))

thread_df = pd.concat(threads, axis = 0)
thread_df = thread_df[~thread_df.author_id.isnull()]
print(len(thread_df))
thread_df.drop("content", axis = 1, inplace = True)
thread_df.rename(columns = {'replies':'num_replies'}, inplace = True)


dtypes={'thread_id':  sqlalchemy.types.BigInteger(),
        'posted_on':  sqlalchemy.types.BigInteger(),
        'num_replies': sqlalchemy.types.Integer(),
        'title': sqlalchemy.types.Text(),
        'game_id': sqlalchemy.types.BigInteger(),
        'author_id': sqlalchemy.types.Text()}

thread_df.to_sql("threads", engine, if_exists = 'replace', index = False, dtype = dtypes)

post_df = pd.concat(pickle.load(open('../data/posts.pkl','rb')), axis = 0)
post_df['score'] = (post_df.simscore > .1).astype(int)
post_df['votes'] = 1
post_df.drop(['game_id','bs_ratio','potty_ratio','simscore', 'author'], axis = 1, inplace = True)
post_df.rename(columns = {'response_number':'response_num', 'time':'posted_on', 'author':'author_name'}, inplace = True)

post_df = post_df[post_df.posted_on < "07/01/2017"]

post_df.to_sql("training", engine, if_exists = 'replace', index = False)

#ADD A PRIMARY KEY
connection = psycopg2.connect('dbname={} user={} password={}'.format(dbname, dbuser, dbpass))
cur = connection.cursor()

cur.execute("ALTER TABLE threads ADD PRIMARY KEY (thread_id);")
cur.execute("ALTER TABLE training ADD PRIMARY KEY (thread_id, response_num, score);")
connection.commit()
cur.close()
connection.close()


