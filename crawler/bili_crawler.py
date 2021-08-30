# -*- encoding: utf-8 -*-
# @Author: RZH

"""
maintain the crawler
"""

import logging
import requests
from typing import List
from lxml import etree

from crawler.database import BiliDB

logging.basicConfig(filename='../log/bili_crawler.log', filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S', level=logging.DEBUG)


class BiliCrawler(object):
    """
    Bilibili Crawler. Used to crawl hot videos.
    """
    # url = 'https://www.bilibili.com/v/popular/all'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/92.0.4515.159 Safari/537.36'}
    api_cid = 'https://api.bilibili.com/x/player/pagelist'
    api_detail = 'https://api.bilibili.com/x/web-interface/view'

    def __init__(self):
        self.bvid: str = ''
        self.cid: List[str] = []
        self.detail: dict = {}
        pass

    @classmethod
    def get_popular(cls):
        """
        get popular video list: video url, title, up, play, danmaku, image
        :return:
        """
        pass

    def get_pagelist(self) -> 'BiliCrawler':
        """
        get video pagelist
        :return: self
        """
        if not self.bvid:  # no bvid yet
            logging.fatal('Calling to get_pagelist before bvid set.')
            return self
        r_cid = requests.get(self.api_cid, params={'bvid': self.bvid}, headers=self.headers)
        if r_cid.status_code == 200:
            j_cid = r_cid.json()
            if j_cid['code']:  # code -400 request error, code -404 video not found
                logging.warning('Failed to fetch pagelist of %s, got err msg: %s.' % (self.bvid, j_cid['message']))
            else:  # code 0 success
                logging.info('Fetched pagelist of %s.' % self.bvid)
                self.cid = [page['cid'] for page in j_cid['data']]
        else:  # error status code
            logging.warning('Failed to request pagelist of %s, got status code: %d.' % (self.bvid, r_cid.status_code))
        return self

    def get_details(self) -> 'BiliCrawler':
        """
        get video details: description, like, coin, star, comments(5)
        get up details: name, uid, intro, avatar, fans
        :return: self
        """
        if not self.cid:  # no cid yet
            logging.fatal('Calling to get_details before cid set.')
            return self
        r_detail = requests.get(self.api_detail, params={'bvid': self.bvid, 'cid': self.cid}, headers=self.headers)
        if r_detail.status_code == 200:
            j_detail = r_detail.json()
            if j_detail['code']:
                # code -400 request error, code -403 no permission
                # code -404 video not found, code 62002 video not available
                logging.warning('Failed to fetch detail of %s, got err msg: %s.' % (self.bvid, j_detail['message']))
            else:  # code 0 success
                logging.info('Fetched detail of %s' % self.bvid)
                self.detail = j_detail['data']
        else:  # error status code
            logging.warning('Failed to request detail of %s, got status code: %d.' % (self.bvid, r_detail.status_code))
        return self

    def save_to_db(self) -> None:
        """
        save crawled data to database
        :return: None
        """
        if not self.detail:  # no detail yet
            logging.fatal('Calling to save_to_db before details crawled.')
            return
        with BiliDB() as db:
            cmd = '''INSERT INTO videos (bvid, title, description, url, pic, play, danmaku, like, coin, collect, up_uid)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
            db.execute(cmd, (self.bvid, self.detail['title'], self.detail['desc'], self.get_video_url(),
                             self.detail['pic'], self.detail['stat']['view'], self.detail['stat']['danmaku'],
                             self.detail['stat']['like'], self.detail['stat']['coin'], self.detail['stat']['favorite'],
                             self.detail['owner']['mid']))
            logging.info('Saved detail of %s into database' % self.bvid)

    def get_video_url(self) -> str:
        """
        generate video url based on bvid
        :return: video url
        """
        return 'https://www.bilibili.com/video/%s' % self.bvid


if __name__ == '__main__':
    v = BiliCrawler()
    v.bvid = 'BV1Kh411W7Yp'
    v.get_pagelist().get_details().save_to_db()
    pass
