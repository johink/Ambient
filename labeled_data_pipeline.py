#Initial Data Pipeline for Generated Target Labels
#Inputs -
#json-formatted list of threads
#Pickled dataframes of post data

#Outputs -
#Pickled model
#Predictions for test data
#Data written to disk
#%%
import pandas as pd
import numpy as np
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from Stemmer import Stemmer
import re
import string
import scipy
import pickle


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


threads = []

for i in range(1,7):
    thread_name = "data/threads{}.json".format(i)
    threads.extend(json.load(open(thread_name)))

#Some threads had no content
threads_clean = [thread for thread in threads if thread['content']]

thread_df = pd.DataFrame(threads_clean)
thread_df.posted_on = pd.to_datetime(thread_df.posted_on, unit="s")
#thread_df['title_caps_ratio'] = thread_df.apply(lambda x: get_title_caps_ratio(x.title), axis = 1)
thread_df['title_length'] = thread_df.title.str.len()

thread_train = thread_df[thread_df.posted_on <= "07/01/17"]
thread_test = thread_df[thread_df.posted_on > "07/01/17"]

tfidf_title = StemmedTfidfVectorizer(max_features = 1000, min_df = 5, max_df=.5)
title_tokens_train = tfidf_title.fit_transform(thread_train.title.values)
title_tokens_test = tfidf_title.transform(thread_test.title.values)
title_train_df = pd.DataFrame(title_tokens_train.todense(), columns = map(lambda x: "title_"+x, tfidf_title.get_feature_names()))
title_test_df = pd.DataFrame(title_tokens_test.todense(), columns = map(lambda x: "title_"+x, tfidf_title.get_feature_names()))
title_combined = pd.concat([pd.concat([thread_train, title_train_df], axis = 1), pd.concat([thread_test, title_test_df], axis = 1)], axis = 0)


del threads
del threads_clean
del thread_df


post_df = pd.concat(pickle.load(open('data/posts.pkl','rb')), axis = 0)
post_df['useful'] = (post_df.simscore > .1).astype(int)

#post_df['dow'] = post_df.time.dt.dayofweek
#post_df['mon'] = post_df.time.dt.month
post_df['OP'] = (post_df.response_number == 0).astype(int)
post_df['content_length'] = post_df.content.str.len()
post_df['content_length_std'] = (post_df.content_length - post_df.content_length.mean()) / post_df.content_length.std()
post_df['content_length_std_sq'] = post_df.content_length_std ** 2
#post_df['year'] = post_df.time.dt.year
#post_df['hour'] = post_df.time.dt.hour
post_df['day'] = post_df.time.dt.day
#post_df['off_peak'] = None
post_df['caps_ratio'] = post_df.apply(lambda x: count_caps(x.content), axis = 1) / post_df.content_length
post_df['punct_ratio'] = post_df.apply(lambda x: count_punct(x.content), axis = 1) / post_df.content_length
post_df['csgo'] = (post_df.game_id == 730).astype(int)
post_df['pubg'] = (post_df.game_id == 578080).astype(int)

#post_df.loc[(post_df.hour >= 14) | (post_df.hour < 5), 'off_peak'] = 0
#post_df.loc[(post_df.hour >= 5) & (post_df.hour < 14), 'off_peak'] = 1

combined_df = pd.merge(post_df[['time','useful','content','thread_id','csgo','pubg', 
                                'OP','content_length_std','content_length_std_sq','day',
                                'caps_ratio','punct_ratio']], title_combined, on = "thread_id")
    
train_df = combined_df[combined_df.time <= "07/01/17"]
test_df = combined_df[combined_df.time > "07/01/17"]

ytrain = train_df.useful.values
ytest = test_df.useful.values




df_trimmed = df[]

tfidf_content = StemmedTfidfVectorizer(max_features = 2000)
content_tokens = tfidf_content.fit_transform(df_trimmed.content.values)
content_df = pd.DataFrame(content_tokens.todense(), columns = map(lambda x: "content_"+x, tfidf_content.get_feature_names()))
print("2")

