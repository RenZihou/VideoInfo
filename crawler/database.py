# -*- encoding: utf-8 -*-
# @Author: RZH

import sqlite3


class BiliDB(object):
    def __init__(self):
        self.conn = sqlite3.connect('../data/data.sqlite')
        self.cur = self.conn.cursor()

    def __enter__(self):
        return self.cur

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.cur.close()
        self.conn.close()


def create_database():
    with BiliDB() as db:
        db.execute('''create table if not exists videos
                   (bvid         TEXT     NOT NULL,
                   title        TEXT     NOT NULL,
                   description  TEXT     NOT NULL,
                   url          TEXT     NOT NULL,
                   pic          TEXT     NOT NULL,
                   play         INTEGER  NOT NULL,
                   danmaku      INTEGER  NOT NULL,
                   like         INTEGER  NOT NULL,
                   coin         INTEGER  NOT NULL, 
                   collect      INTEGER  NOT NULL,
                   up_uid       INTEGER  NOT NULL)''')
        db.execute('''create table if not exists ups
        (uid          INTEGER  NOT NULL,
        name          TEXT     NOT NULL,
        introduction  TEXT     NOT NULL,
        avatar        TEXT     NOT NULL,
        fans          INTEGER  NOT NULL)''')


if __name__ == '__main__':
    create_database()
    pass
