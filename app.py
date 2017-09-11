#app.py
from __future__ import division
from flask import Flask, render_template, request
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

    return render_template('dashboard.html', thread_data = thread_data, post_data = post_data, other_links = other_links)#include kwargs of template data here

@app.route('/vote/thread/up/<int:threadid>', methods=['GET'])
def vote_thread_up(threadid):
    if not threadid:
        return
    else:
        db.increment_thread(threadid)

@app.route('/vote/thread/down/<int:threadid>', methods=['GET'])
def vote_thread_down(threadid):
    if not threadid:
        return
    else:
        db.decrement_thread(threadid)

@app.route('/vote/post/up/<int:threadid>/<int:responsenum>', methods=['GET'])
def vote_post_up(threadid, responsenum):
    if threadid and responsenum:
        db.increment_post(threadid, responsenum)

@app.route('/vote/post/down/<int:threadid>/<int:responsenum>', methods=['GET'])
def vote_post_down(threadid, responsenum):
    if threadid and responsenum:
        db.decrement_post(threadid, responsenum)

if __name__ == '__main__':
    #running=True
    #update_thread = threading.Thread(target = add_new_data)
    #update_thread.start()
    #app.run comes last!
    app.run(host='0.0.0.0', threaded=True)