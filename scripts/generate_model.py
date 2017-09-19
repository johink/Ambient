import pandas as pd
import numpy as np
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from Stemmer import Stemmer
import re
import string
import scipy
import pickle
import sqlalchemy
import os
from sklearn.ensemble import RandomForestClassifier
import boto3
import psycopg2

dbuser = os.environ["DBUSER"]
dbname = os.environ["DBNAME"]
dbpass = os.environ["DBPASS"]

engine = sqlalchemy.create_engine('postgresql+psycopg2://{}:{}@localhost/{}'.format(dbuser, dbpass, dbname))

def main():
    print("Downloading new posts from s3...")
    
    s3 = boto3.resource('s3')
    sfp = s3.Bucket("steamforumposts")
    sfp.download_file('test_posts.json', '../data/test_posts.json')
    sfp.download_file('test_threads.json', '../data/test_threads.json')
    
    print("Reading in old data from Postgres...")
    
    combined_df = pd.read_sql(
    """
    SELECT training.thread_id, training.response_num, training.content, training.posted_on, training.votes, training.score, threads.title, threads.game_id
    FROM training
    INNER JOIN threads ON training.thread_id = threads.thread_id
    """,
    engine)
    
    punct_set = set(string.punctuation)
    
    def count_caps(posting):
        #Count the number of capital letters
        return sum([letter.isupper() for letter in posting])
    
    def count_punct(posting):
        #Count the number of punctuation characters
        return len([letter for letter in posting if letter in punct_set])
    
    def get_title_caps_ratio(title):
        #Returns ratio of capital letters to number of words
        words = title.split()
        if words:
            return count_caps(title) / len(words)
        else:
            return 0
    
    def remove_hyperlinks(text):
        return re.sub("https?:\S+", "", text)
    
    stemmer = Stemmer("en")
    
    class StemmedTfidfVectorizer(TfidfVectorizer):
        def build_analyzer(self):
            analyzer = super(TfidfVectorizer, self).build_analyzer()
            return lambda doc: stemmer.stemWords(analyzer(doc))
    
    def add_features(post_df):
        post_df.content = post_df.content.apply(remove_hyperlinks)
        post_df['OP'] = (post_df.response_num == 0).astype(int)
        post_df['length_content'] = post_df.content.str.len()
        post_df['length_content_std'] = (post_df.length_content - post_df.length_content.mean()) / post_df.length_content.std()
        post_df['length_content_std_sq'] = post_df.length_content_std ** 2
        post_df['day'] = post_df.posted_on.dt.day
        post_df['caps_ratio'] = post_df.apply(lambda x: count_caps(x.content), axis = 1) / post_df.length_content
        post_df['punct_ratio'] = post_df.apply(lambda x: count_punct(x.content), axis = 1) / post_df.length_content
        
        
    
        return post_df.drop(['length_content', 'game_id'], axis = 1)
    
    def generate_title_tokens():
        threads = pd.read_sql("SELECT thread_id, title FROM threads", engine)
        tfidf_title = StemmedTfidfVectorizer(max_features = 1000, min_df = 5, max_df=.5)
        title_tokens = tfidf_title.fit_transform(threads.title.values)
        title_df = pd.DataFrame(title_tokens.todense(), columns = map(lambda x: "title_"+x, tfidf_title.get_feature_names()))
        return tfidf_title, pd.concat([threads.drop('title', axis = 1), title_df], axis = 1)
    
    def generate_content_tokens(df):
        tfidf_content = StemmedTfidfVectorizer(max_features = 2000, min_df = 5, max_df = .5)
        content_tokens = tfidf_content.fit_transform(df.content.values)
        return tfidf_content, content_tokens
    
    print("Generating features for training data...")
    combined_df = pd.concat([combined_df, pd.get_dummies(combined_df.game_id, prefix="gameid", drop_first=True)], axis = 1)
    combined_df = add_features(combined_df)
    dummy_names = [name for name in combined_df.columns if name.startswith("gameid_")]
    
    print("Generating title tokens...")
    tfidf_title, title_token_df = generate_title_tokens()
    
    print("Generating content tokens...")
    combined_df = pd.merge(combined_df, title_token_df, on = 'thread_id')
    del title_token_df
    
    tfidf_content, sparse_content_tokens = generate_content_tokens(combined_df)
    
    ytrain = combined_df.score
    sample_weights = combined_df.votes
    combined_df.drop(['content','posted_on', 'thread_id', 'score', 'votes', 'title'], axis = 1, inplace = True)
    
    print("Stacking sparse matrices...")
    combined_df = scipy.sparse.hstack([combined_df.values, sparse_content_tokens])
    combined_df.data = np.nan_to_num(combined_df.data)
    
    print("Building random forest...")
    rf = RandomForestClassifier(max_depth = 8, n_estimators = 201, class_weight="balanced", n_jobs=-1)
    rf.fit(combined_df, ytrain, sample_weight = sample_weights)
    
    del combined_df
    
    pickle.dump(rf, open("../model.pkl", "wb"))
    
    print("Writing new threads to Postgres...")
    connection = psycopg2.connect('dbname={} user={} password={}'.format(dbname, dbuser, dbpass))
    cur = connection.cursor()
    
    test_threads = pd.read_json('../data/test_threads.json') 
    dupes = set(test_threads.thread_id[test_threads.duplicated('thread_id', keep = False)].values)
    test_threads = test_threads[~test_threads.thread_id.isin(dupes)]
    data = [(int(a), int(b), int(c), str(d), int(e), str(f)) for a,b,c,d,e,f in zip(test_threads.thread_id, test_threads.posted_on, test_threads.num_replies, test_threads.title, test_threads.game_id, test_threads.author_id)]
    insert_query = 'INSERT INTO threads (thread_id, posted_on, num_replies, title, game_id, author_id) VALUES %s ON CONFLICT (thread_id) DO UPDATE SET num_replies = EXCLUDED.num_replies;'
    psycopg2.extras.execute_values(cur, insert_query, data, template=None, page_size=1000)
    
    connection.commit()
    cur.close()
    connection.close()
    
    
    def transform_test_df(df, tfidf_title, tfidf_content):
        for name in dummy_names:
            df[name] = (df.game_id == int(name.split("_")[-1])).astype(int)
        df = add_features(df)
        title_token_test = tfidf_title.transform(df.title)
        title_token_test_df = pd.DataFrame(title_token_test.todense(), columns = map(lambda x: "title_"+x, tfidf_title.get_feature_names()))
        df = pd.concat([df.drop('title', axis = 1), title_token_test_df], axis = 1)
        content_token_test = tfidf_content.transform(df.content)
    
        print(df.info())
        xtest = df.drop(['content','posted_on', 'thread_id', 'author_id', 'author_name'], axis = 1).values
        xtest = scipy.sparse.hstack([xtest, content_token_test])
        xtest.data = np.nan_to_num(xtest.data)
        return xtest
    
    test_posts = pd.read_json("../data/test_posts.json")
    test_posts.rename(columns = {"time":"posted_on", 'response_number':'response_num', 'author':'author_name'}, inplace = True)
    test_posts.response_num = test_posts.response_num.str[1:].astype(int)
    test_posts = test_posts[~test_posts.thread_id.isin(dupes)]
    test_threads = pd.read_sql("SELECT thread_id, title, game_id FROM threads", engine)
    combined_test = pd.merge(test_posts, test_threads, on = 'thread_id')
    combined_test.posted_on = pd.to_datetime(combined_test.posted_on)
    
    print("Transforming test data...")
    xtest = transform_test_df(combined_test, tfidf_title, tfidf_content)
    print("Generating predictions...")
    preds = rf.predict_proba(xtest)
    
    print("Test posts: {}".format(test_posts.shape))
    print("Combined test: {}".format(combined_test.shape))
    print("preds: {}".format(preds.shape))

    test_posts['usefulness'] = preds[:,1]
    
    print("Writing new posts to posts table...")
    test_posts.to_sql('posts', engine, if_exists = 'replace', index = False)
    
    connection = psycopg2.connect('dbname={} user={} password={}'.format(dbname, dbuser, dbpass))
    cur = connection.cursor()
    
    cur.execute("ALTER TABLE posts ADD PRIMARY KEY (thread_id, response_num);")
    connection.commit()
    cur.close()
    connection.close()
    
if __name__ == "__main__":
    main()
