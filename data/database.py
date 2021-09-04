# -*- encoding: utf-8 -*-
# @Author: RZH

"""
provide access to database and several functions
"""

import sqlite3
from os import path


class BiliDB(object):
    """
    connect to the database
    """
    def __init__(self):
        self.conn = sqlite3.connect(path.join(path.dirname(__file__), 'data.sqlite'))
        self.cur = self.conn.cursor()

    def __enter__(self):
        return self.cur

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.cur.close()
        self.conn.close()


def create_database() -> None:
    """
    create empty database
    :return: None
    """
    with BiliDB() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS videos
                   (bvid        TEXT     PRIMARY KEY,
                   title        TEXT     NOT NULL,
                   description  TEXT     NOT NULL,
                   url          TEXT     NOT NULL,
                   pic          TEXT     NOT NULL,
                   play         INTEGER  NOT NULL,
                   danmaku      INTEGER  NOT NULL,
                   like         INTEGER  NOT NULL,
                   coin         INTEGER  NOT NULL, 
                   collect      INTEGER  NOT NULL,
                   up_uid       TEXT     NOT NULL,
                   avid         INTEGER  NOT NULL,
                   pub_time     INTEGER  NOT NULL,
                   category     TEXT     NOT NULL,
                   duration     INTEGER  NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS ups
                      (uid          TEXT  PRIMARY KEY,
                      name          TEXT     NOT NULL,
                      introduction  TEXT     NOT NULL,
                      avatar        TEXT     NOT NULL,
                      fans          INTEGER  NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS comments
                      (bvid      TEXT  PRIMARY KEY,
                      comment_1  TEXT  NOT NULL,
                      comment_2  TEXT  NOT NULL,
                      comment_3  TEXT  NOT NULL,
                      comment_4  TEXT  NOT NULL,
                      comment_5  TEXT  NOT NULL)''')
    return


if __name__ == '__main__':
    create_database()
    pass
