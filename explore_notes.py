import json
import pandas as pd
import numpy as np

with open("pubg_notes.json") as f:
    data = json.load(f)
    
data
#%%

all_topics = list(set([topic for patch in data for topic in patch['topics']]))
sorted(all_topics)

len([notes for patch in data for notes in patch['content']])

#%%
df = pd.DataFrame([{'date':patch['post_date'], 'change':change['change']} for patch in data for change in patch['content']])
df.date.replace('1)', '4/20/17', inplace = True)
df.date.replace('12/13)', '6/21/17', inplace = True)
    
df.date = pd.to_datetime(df.date)
df.head()

#%%
categories = []
for change in df.change:
    print(change)
    categories.append(input("What category? >> "))
    
#%%
df['category'] = categories
df.head()
#%%
df.to_csv("pubg_notes.csv")