# -*- encoding: utf-8 -*-
# @Author: RZH

"""
maintain the crawler
this crawler call api to get the data
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from os import path
from random import random
from time import sleep
from typing import List
import logging

import requests
from tqdm import tqdm

from crawler.database import BiliDB

logging.basicConfig(filename=path.join(path.dirname(__file__), '../log/bili_crawler.log'), filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S', level=logging.WARNING)


class BiliCrawler(object):
    """
    Bilibili Crawler. Used to crawl hot videos.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/92.0.4515.159 Safari/537.36'}
    api_cid = 'https://api.bilibili.com/x/player/pagelist'
    api_detail = 'https://api.bilibili.com/x/web-interface/view'
    api_comment = 'https://api.bilibili.com/x/v2/reply'
    api_up = 'https://api.bilibili.com/x/web-interface/card'
    url_popular = 'https://s.search.bilibili.com/cate/search'
    bvid_list: List[str] = []

    def __init__(self, bvid: str = ''):
        self.bvid: str = bvid
        self.cid: List[str] = []
        self.detail: dict = {}
        self.comment: List[str] = []
        self.up: dict = {}

    @classmethod
    def crawl_all(cls, size: int = 50) -> None:
        """
        crawl all data of videos in `bvid_list`
        :param size: number of pages-to-crawl in each category.
        :return: None
        """
        print('Crawling popular video list...')
        cls.__get_popular(size=size)
        print('Crawling video details...')
        with ThreadPoolExecutor(max_workers=10) as executor:
            list(tqdm(executor.map(cls.crawl, map(BiliCrawler, cls.bvid_list)), total=len(cls.bvid_list)))
        print('Crawling done.')
        return

    @classmethod
    def __get_popular(cls, size: int = 50) -> None:
        """
        get popular video list: video url, title, up, play, danmaku, image
        :param size: number of pages-to-crawl in each category.
        :return: None
        """
        time_to: str = datetime.today().strftime('%Y%m%d')
        time_from: str = (datetime.today() + timedelta(days=-7)).strftime('%Y%m%d')
        for cate_id in (28, 29, 30, 31, 59, 193, 194):  # 7 main category in music
            # 28: original, 29: live, 30: vocaloid, 31: cover, 59: perform, 192: mv, 194: electronic
            for page in range(1, size + 1):  # 20 * 50 = 1000 videos per category
                r_popular = requests.get(cls.url_popular, params={
                    'main_ver': 'v3', 'search_type': 'video', 'view_type': 'hot_rank', 'order': 'click',
                    'copy_right': -1, 'cate_id': cate_id, 'page': page, 'pagesize': 20,
                    'time_from': time_from, 'time_to': time_to,
                }, headers=cls.headers)
                if r_popular.status_code == 200:
                    j_popular = r_popular.json()
                    if j_popular['code']:
                        logging.warning('Failed to fetch video list of category %d, page %d, got err msg: %s.'
                                        % (cate_id, page, j_popular['msg']))
                    else:  # code 0 success
                        logging.info('Fetched page %d of category %d.' % (page, cate_id))
                        cls.bvid_list += [video['bvid'] for video in j_popular['result']]
                else:  # error status code
                    logging.warning('Failed to request video list of category %d, page %d, got status code: %d'
                                    % (cate_id, page, r_popular.status_code))
        return

    def crawl(self) -> None:
        """
        crawl all data (of a video) needed
        :return: None
        """
        sleep(random())
        if not self.bvid:
            logging.fatal('Calling to crawl before bvid set.')
            return
        with BiliDB() as db:
            if list(db.execute('SELECT * FROM videos WHERE bvid = ?', (self.bvid,))):
                logging.warning('Skipped video detail of %s: already exist.' % self.bvid)
                return
        self.__get_pagelist().__get_detail().__save_detail()
        self.__get_comment().__save_comment()
        mid = int(self.detail['owner']['mid'])
        with BiliDB() as db:
            if list(db.execute('SELECT * FROM ups WHERE uid = ?', (mid,))):
                logging.info('Skipped up info of %d: already exist.' % mid)
                return
        self.__get_up().__save_up()
        return

    def __get_pagelist(self) -> 'BiliCrawler':
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

    def __get_detail(self) -> 'BiliCrawler':
        """
        get video details: description, like, coin, star, comments(5)
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

    def __get_comment(self) -> 'BiliCrawler':
        """
        get video comments (up to 5)
        :return: self
        """
        if not self.detail:  # no video detail (video avid) yet
            logging.fatal('Calling to get_comment before details crawled.')
            return self
        avid = self.detail['aid']
        r_comment = requests.get(self.api_comment, params={'type': 1, 'oid': avid, 'sort': 1, 'nohot': 1})
        # type = 1: video comment, sort = 1: sort by like number, nohot = 1: do not show hot comments
        if r_comment.status_code == 200:
            j_comment = r_comment.json()
            if j_comment['code']:  # code -400 request error, code -404 not found, code 12002 comment disabled
                logging.warning('Failed to fetch comment of %s, got err msg: %s.' % (self.bvid, j_comment['message']))
            else:  # code 0 success
                self.comment = list(map(lambda x: x['content']['message'], j_comment['data']['replies'][:5]))
                logging.info('Fetched comment of %s.' % self.bvid)
        else:  # error status code
            logging.warning('Failed to request comment of %s, got status code: %d.'
                            % (self.bvid, r_comment.status_code))
        return self

    def __get_up(self) -> 'BiliCrawler':
        """
        get up details: name, uid, intro, avatar, fans
        :return: self
        """
        if not self.detail:  # no video detail (up mid) yet
            logging.fatal('Calling to get_up before details crawled.')
            return self
        mid = int(self.detail['owner']['mid'])
        r_up = requests.get(self.api_up, params={'mid': mid, 'photo': False}, headers=self.headers)
        if r_up.status_code == 200:
            j_up = r_up.json()
            if j_up['code']:  # code -400 request error
                logging.warning('Failed to fetch up info of %d, got err msg: %s.' % (mid, j_up['message']))
            else:  # code 0 success
                logging.info('Fetched up info of %d.' % mid)
                self.up = j_up['data']['card']
        else:  # error status code
            logging.warning('Failed to request up info of %d, got status code: %d.' % (mid, r_up.status_code))
        return self

    def __save_detail(self) -> None:
        """
        save crawled video detail into database
        :return: None
        """
        if not self.detail:  # no detail yet
            logging.fatal('Calling to save_detail before details crawled.')
            return
        with BiliDB() as db:
            cmd = '''INSERT INTO videos 
                     (bvid, title, description, url, pic, play, danmaku, like, coin, collect, up_uid, avid)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
            db.execute(cmd, (self.bvid, self.detail['title'], self.detail['desc'], self.__get_video_url(),
                             self.detail['pic'], self.detail['stat']['view'], self.detail['stat']['danmaku'],
                             self.detail['stat']['like'], self.detail['stat']['coin'], self.detail['stat']['favorite'],
                             self.detail['owner']['mid'], self.detail['aid']))
            logging.info('Saved detail of %s into database.' % self.bvid)
        return

    def __save_comment(self) -> None:
        """
        save crawled comment to database
        :return: None
        """
        if not self.comment:  # no comment yet
            logging.fatal('Calling to save_comment before comment crawled.')
            return
        with BiliDB() as db:
            cmd = '''INSERT INTO comments (bvid, comment_1, comment_2, comment_3, comment_4, comment_5)
                     VALUES (?, ?, ?, ?, ?, ?)'''
            db.execute(cmd, (self.bvid, *self.comment))
            logging.info('Saved comment of %s into database.' % self.bvid)
        return

    def __save_up(self) -> None:
        """
        save crawled up info to database
        :return: None
        """
        if not self.up:  # no up info yet
            logging.fatal('Calling to save_up before up info crawled.')
            return
        with BiliDB() as db:
            cmd = '''INSERT INTO ups (uid, name, introduction, avatar, fans)
                     VALUES (?, ?, ?, ?, ?)'''
            db.execute(cmd, (self.up['mid'], self.up['name'], self.up['sign'], self.up['face'], self.up['fans']))
            logging.info('Saved up info of %s into database.' % self.up['mid'])
        return

    def __get_video_url(self) -> str:
        """
        generate video url based on bvid
        :return: video url
        """
        return 'https://www.bilibili.com/video/%s' % self.bvid


if __name__ == '__main__':
    BiliCrawler.crawl_all(size=1)
    pass
