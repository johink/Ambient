import psycopg2
import os

def create_db():
    dbname = os.environ["DBNAME"]
    dbuser = os.environ["DBUSER"]
    dbpass = os.environ["DBPASS"]
    conn = psycopg2.connect("dbname={} user={} password={}".format(dbname, dbuser, dbpass))
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS posts;")
    cur.execute("DROP TABLE IF EXISTS threads;")
    cur.execute("DROP TABLE IF EXISTS training;")
    cur.execute(
"""
CREATE TABLE IF NOT EXISTS posts (
thread_id bigint,
content varchar(10000),
posted_on timestamp,
response_num int,
author_id varchar(50),
author_name varchar(50),
usefulness float8,
PRIMARY KEY (thread_id, response_num)
);
"""
)
    cur.execute(
"""
CREATE TABLE IF NOT EXISTS threads (
thread_id bigint PRIMARY KEY,
posted_on timestamp,
num_replies int,
title varchar(100),
game_id int,
author_id varchar(50)
);
"""
)
    cur.execute(
"""
CREATE TABLE IF NOT EXISTS training (
thread_id bigint,
response_num int,
content varchar(10000),
posted_on timestamp,
votes int,
score int,
PRIMARY KEY (thread_id, response_num)
);
"""
)
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    create_db()
