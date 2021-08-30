# -*- encoding: utf-8 -*-
# @Author: RZH

"""
maintain the crawler
"""

from datetime import datetime, timedelta
import logging
import requests
from typing import List

from crawler.database import BiliDB

logging.basicConfig(filename='../log/bili_crawler.log', filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S', level=logging.DEBUG)


class BiliCrawler(object):
    """
    Bilibili Crawler. Used to crawl hot videos.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/92.0.4515.159 Safari/537.36'}
    api_cid = 'https://api.bilibili.com/x/player/pagelist'
    api_detail = 'https://api.bilibili.com/x/web-interface/view'
    url_popular = 'https://s.search.bilibili.com/cate/search'
    bvid_list: List[str] = []

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
        time_to: str = datetime.today().strftime('%Y%m%d')
        time_from: str = (datetime.today() + timedelta(days=-7)).strftime('%Y%m%d')
        for cate_id in [28, 29, 30, 31, 59, 193, 194]:  # 7 main category in music
            # 28: original, 29: live, 30: vocaloid, 31: cover, 59: perform, 192: mv, 194: electronic
            for page in range(1, 51):  # 20 * 50 = 1000 videos per category
                r_popular = requests.get(cls.url_popular, params={
                    'main_ver': 'v3', 'search_type': 'video', 'view_type': 'hot_rank', 'order': 'click',
                    'copy_right': -1, 'cate_id': cate_id, 'page': page, 'pagesize': 20,
                    'time_from': time_from, 'time_to': time_to,
                })
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

    def get_up(self):
        pass

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
    BiliCrawler.get_popular()
    pass
