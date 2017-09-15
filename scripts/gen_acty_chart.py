import os
import sqlalchemy
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.style.use('ggplot')

dbuser = os.environ["DBUSER"]
dbname = os.environ["DBNAME"]
dbpass = os.environ["DBPASS"]

engine = sqlalchemy.create_engine('postgresql+psycopg2://{}:{}@localhost/{}'.format(dbuser, dbpass, dbname))

alldf = pd.read_sql("select posts.posted_on, posts.content, threads.game_id from posts inner join threads on posts.thread_id = threads.thread_id;", engine)
alldf.posted_on = pd.to_datetime(alldf.posted_on, unit="ms")
alldf['hour'] = alldf.posted_on.dt.hour
for game_id, df in alldf.groupby('game_id'):
  fig, ax = plt.subplots(figsize = (12,4))
  aggdf = df.groupby('hour').agg({"content":len})
  maxposts = aggdf.content.max()
  maxposts = (maxposts // 100 + 1) * 100
  aggdf.plot(ax = ax)
  ax.set_xlabel("")
  ax.set_ylabel("# Posts")
  plt.xticks([0,6,12,18],["Midnight","6 A.M.","Noon","6 P.M."])
  ax.set_ylim((0,maxposts))
  ax.legend([])
  fig.savefig("../static/{}.png".format(game_id))
