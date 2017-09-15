#app.py
from __future__ import division
from flask import Flask, render_template, jsonify
import pandas as pd
import time
import random
import threading
from ambient import AmbientDataModel

app = Flask(__name__)
app.jinja_env.tests['equalto'] = lambda value, other : value == other
app.jinja_env.tests['ge'] = lambda value, other : value >= other

#db needs increment/decrement post/thread, get all posts, mapper from gameid to gamename
db = AmbientDataModel()

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/dashboard', methods=['GET'])
def dashboard_default():
    return dashboard(570)

@app.route('/dashboard/<int:gameid>', methods=['GET'])
def dashboard(gameid):
    if not gameid or not db.check_validity(gameid):
        gameid = 570
    thread_data = db.get_thread_data(gameid)
    post_data = db.get_post_data(gameid)
    other_links = db.get_other_links(gameid)
    user_data = db.get_user_stats(gameid)
    topic_data = db.get_topic_stats(gameid)
    summary_data = db.get_summary_stats(gameid)

    return render_template('dashboard.html', 
thread_data = thread_data, 
post_data = post_data, 
other_links = other_links,
game_info = {'gameid':gameid, 'name':db.mapper[gameid][0],'acronym':db.mapper[gameid][1]},
user_data = user_data,
topic_data = topic_data,
summary_data = summary_data
)

@app.route('/vote/thread/up/<int:threadid>', methods=['POST'])
def vote_thread_up(threadid):
    try:
        db.vote_thread(threadid, 1)
        return "Successful"
    except Exception as e:
        print(e)
        return "DBError"

@app.route('/vote/thread/down/<int:threadid>', methods=['POST'])
def vote_thread_down(threadid):
    try:
        db.vote_thread(threadid, 0)
        return "Successful"
    except:
        return "DBError"

@app.route('/vote/post/up/<int:threadid>/<int:responsenum>', methods=['POST'])
def vote_post_up(threadid, responsenum):
    try:
        db.vote_post(threadid, responsenum, 1)
        return "Successful"
    except:
        return "DBError"

@app.route('/vote/post/down/<int:threadid>/<int:responsenum>', methods=['POST'])
def vote_post_down(threadid, responsenum):
    try:
        db.vote_post(threadid, responsenum, 0)
        return "Successful"
    except:
        return "DBError"

@app.route('/thread/<int:threadid>', methods=["POST"])
@app.route('/thread/<int:threadid>/<int:pagenum>', methods=["POST"])
def display_thread(threadid, pagenum=1):
    data = db.get_thread_contents(threadid, pagenum)
    
    return render_template('popup.html', data = data)

if __name__ == '__main__':
    #running=True
    #update_thread = threading.Thread(target = add_new_data)
    #update_thread.start()
    #app.run comes last!
    app.run(host='0.0.0.0', threaded=True)
