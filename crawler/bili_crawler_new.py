# -*- encoding: utf-8 -*-
# @Author: RZH

"""
maintain the crawler
this crawler parse the html to get data
"""

from collections import defaultdict
from datetime import datetime, timedelta
from functools import partial
from os import path
from random import random
from time import sleep
from typing import List
import logging

import requests
from requests_html import HTMLSession  # used to render html
from tqdm import tqdm

from data.database import BiliDB

BiliDB = partial(BiliDB, db='data_new.sqlite3')  # specify database

logging.basicConfig(filename=path.join(path.dirname(__file__), '../log/bili_crawler_new.log'), filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S', level=logging.WARNING)
# do not log INFO and DEBUG level logs
logging.disable(logging.INFO)
logging.disable(logging.DEBUG)
pyppeteer_logger = logging.getLogger('pyppeteer')
pyppeteer_logger.setLevel(logging.WARNING)  # disable tons of debug output to speed up


class BiliCrawler(object):
    """
    Bilibili Crawler. Used to crawl hot videos.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/92.0.4515.159 Safari/537.36'}
    url_popular = 'https://www.bilibili.com/v/music/%s/#/all/click/0/%d/%s,%s'
    url_video = 'https://www.bilibili.com/video/'
    url_up = 'https://space.bilibili.com/'
    bvid_list: List[str] = []
    session = HTMLSession()

    def __init__(self, bvid: str = ''):
        self.bvid: str = bvid
        self.detail: 'defaultdict' = defaultdict(dict)
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
        for bvid in tqdm(cls.bvid_list):
            sleep(random())
            try:
                BiliCrawler(bvid=bvid).crawl()
            except IndexError:
                logging.warning('Skipped crawling %s: timeout.' % bvid)
                continue
        print('Crawling done.')
        return

    @classmethod
    def __get_popular(cls, size: int = 50) -> None:
        """
        get popular video list: video url, title, up, play, danmaku, image
        :param size: number of pages-to-crawl in each category.
        :return: None
        """
        time_to: str = datetime.today().strftime('%Y-%m-%d')
        time_from: str = (datetime.today() + timedelta(days=-7)).strftime('%Y-%m-%d')
        for cate in ('original', 'cover', 'live', 'vocaloid', 'perform', 'mv', 'electronic'):
            # 7 main category in music
            for page in range(1, size + 1):  # 20 * 50 = 1000 videos per category
                r_popular = cls.session.get(cls.url_popular % (cate, page, time_from, time_to), headers=cls.headers)
                if r_popular.status_code == 200:
                    r_popular.html.render()
                    t_popular = r_popular.html
                    for item in range(1, 21):
                        cls.bvid_list.append(
                            t_popular.xpath('//*[@id="videolist_box"]/div[2]/ul/li[%d]/div/div[2]/a/@href' % item)[0]
                            .split('/')[-1])
                else:  # error status code
                    logging.warning('Failed to request video list of category %s, page %d, got status code: %d'
                                    % (cate, page, r_popular.status_code))
        return

    def crawl(self) -> None:
        """
        crawl all data (of a video) needed
        :return: None
        """
        if not self.bvid:
            logging.fatal('Calling to crawl before bvid set.')
            return
        with BiliDB() as db:
            if list(db.execute('SELECT * FROM videos WHERE bvid = ?', (self.bvid,))):
                logging.warning('Skipped video detail of %s: already exist.' % self.bvid)
                return
        self.__get_details().__save_detail().__save_comment()
        mid = int(self.detail['owner']['mid'])
        with BiliDB() as db:
            if list(db.execute('SELECT * FROM ups WHERE uid = ?', (mid,))):
                logging.info('Skipped up info of %d: already exist.' % mid)
                return
        self.__get_up().__save_up()
        return

    def __get_details(self) -> 'BiliCrawler':
        """
        get video details: description, like, coin, star, comments(5)
        :return: self
        """
        r_detail = self.session.get(self.url_video + self.bvid, headers=self.headers)
        if r_detail.status_code == 200:
            r_detail.html.render(scrolldown=5, sleep=1)  # sleep and scroll down to load comments
            t_detail = r_detail.html
            self.detail['title'] = t_detail.xpath('//*[@id="viewbox_report"]/h1/span/text()')[0].strip()
            self.detail['desc'] = t_detail.xpath('//*[@id="v_desc"]/div[2]/span/text()')[0].strip()
            self.detail['pub_time'] = int(datetime.strptime(
                t_detail.xpath('//*[@id="viewbox_report"]/div/span[3]/text()')[0].strip(),
                '%Y-%m-%d %H:%M:%S').timestamp())
            self.detail['pic'] = t_detail.xpath('/html/head/meta[12]/@content')[0]
            self.detail['stat']['view'] = \
                self.__standardize_num(t_detail.xpath('//*[@id="viewbox_report"]/div/span[1]/text()')[0])
            self.detail['stat']['danmaku'] = \
                self.__standardize_num(t_detail.xpath('//*[@id="viewbox_report"]/div/span[2]/text()')[0])
            self.detail['stat']['like'] = \
                self.__standardize_num(t_detail.xpath('//*[@id="arc_toolbar_report"]/div[1]/span[1]/text()')[0])
            self.detail['stat']['coin'] = \
                self.__standardize_num(t_detail.xpath('//*[@id="arc_toolbar_report"]/div[1]/span[2]/text()')[0])
            self.detail['stat']['favorite'] = \
                self.__standardize_num(t_detail.xpath('//*[@id="arc_toolbar_report"]/div[1]/span[3]/text()')[0])
            try:  # only one up
                mid = t_detail.xpath('//*[@id="v_upinfo"]/div[1]/a/@href')[0].split('/')[-1]
            except IndexError:  # multiple up, select the leading one
                mid = t_detail.xpath('//*[@id="member-container"]/div[1]/div/a/@href')[0].split('/')[-1]
            self.detail['owner']['mid'] = mid

            for c in range(1, 6):
                try:
                    comm = '\n'.join(
                        t_detail.xpath('//*[@id="comment"]/div/div[2]/div/div[4]/div[%d]/div[2]/p/text()' % c))
                    self.comment.append(comm)
                except IndexError:
                    continue

            # here is three info (avid, category and duration) that is almost
            # impossible to crawl through the video page
            # and since none of them is in the class requirement,
            # i choose to use api to fetch them for convenience
            api = 'https://api.bilibili.com/x/web-interface/view'
            r_api = requests.get(api, params={'bvid': self.bvid}, headers=self.headers)
            if r_api.status_code == 200:
                j_api = r_api.json()
                self.detail['aid'] = j_api['data']['aid']
                self.detail['tname'] = j_api['data']['tname']
                self.detail['duration'] = j_api['data']['duration']
            else:
                logging.warning('Failed to request api of %s, got status code: %d' % (self.bvid, r_api.status_code))
        else:  # error status code
            logging.warning('Failed to request detail of %s, got status code: %d.' % (self.bvid, r_detail.status_code))
        return self

    def __get_up(self) -> 'BiliCrawler':
        """
        get up details: name, uid, intro, avatar, fans
        :return: self
        """
        if not self.detail:
            logging.fatal('Calling to get_up before details crawled.')
            return self
        mid = int(self.detail['owner']['mid'])
        r_up = self.session.get(self.url_up + str(mid), headers=self.headers)
        if r_up.status_code == 200:
            r_up.html.render()  # render javascript
            t_up = r_up.html
            self.up['mid'] = mid
            self.up['name'] = t_up.xpath('//*[@id="h-name"]/text()')[0].strip()
            self.up['sign'] = \
                t_up.xpath('//*[@id="app"]/div[1]/div[1]/div[2]/div[2]/div/div[2]/div[2]/h4/text()')[0].strip()
            self.up['face'] = t_up.xpath('//*[@id="h-avatar"]/@src')[0].strip()
            self.up['fans'] = t_up.xpath('//*[@id="n-fs"]/text()')[0].strip()
        else:  # error status code
            logging.warning('Failed to request up info of %d, got status code: %d.' % (mid, r_up.status_code))
        return self

    def __save_detail(self) -> 'BiliCrawler':
        """
        save crawled video detail into database
        :return: None
        """
        if not self.detail:  # no detail yet
            logging.fatal('Calling to save_detail before details crawled.')
            return self
        with BiliDB() as db:
            cmd = '''INSERT INTO videos (bvid, title, description, url, pic, play, 
                     danmaku, like, coin, collect, up_uid, pub_time, avid, category, duration)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
            db.execute(cmd, (self.bvid, self.detail['title'], self.detail['desc'], self.__get_video_url(),
                             self.detail['pic'], self.detail['stat']['view'], self.detail['stat']['danmaku'],
                             self.detail['stat']['like'], self.detail['stat']['coin'], self.detail['stat']['favorite'],
                             self.detail['owner']['mid'], self.detail['pub_time'], self.detail['aid'],
                             self.detail['tname'], self.detail['duration']))
            logging.info('Saved detail of %s into database' % self.bvid)
        return self

    def __save_comment(self) -> 'BiliCrawler':
        """
        save crawled comment to database
        :return: None
        """
        if not self.comment:  # no comment yet
            logging.fatal('Calling to save_comment before comment crawled.')
            return self
        self.comment += ([''] * (5 - len(self.comment)))
        with BiliDB() as db:
            cmd = '''INSERT INTO comments (bvid, comment_1, comment_2, comment_3, comment_4, comment_5)
                     VALUES (?, ?, ?, ?, ?, ?)'''
            db.execute(cmd, (self.bvid, *self.comment))
            logging.info('Saved comment of %s into database.' % self.bvid)
        return self

    def __save_up(self) -> 'BiliCrawler':
        """
        save crawled up info to database
        :return: None
        """
        if not self.up:  # no up info yet
            logging.fatal('Calling to save_up before up info crawled')
            return self
        mid = self.up['mid']
        with BiliDB() as db:
            if list(db.execute('SELECT * FROM ups WHERE uid = ?', (mid,))):
                logging.info('Skipped up info of %s: already exist.' % mid)
                return self
            cmd = '''INSERT INTO ups (uid, name, introduction, avatar, fans)
                     VALUES (?, ?, ?, ?, ?)'''
            db.execute(cmd, (self.up['mid'], self.up['name'], self.up['sign'], self.up['face'], self.up['fans']))
            logging.info('Saved up info of %s into database' % self.up['mid'])
        return self

    def __get_video_url(self) -> str:
        """
        generate video url based on bvid
        :return: video url
        """
        return 'https://www.bilibili.com/video/%s' % self.bvid

    @staticmethod
    def __standardize_num(text: str) -> int:
        """
        standardize number expression with suffix '万'
        :param text: number expression
        :return: the real number
        """
        text = text.replace('播放', '').replace('弹幕', '').replace(u'\xa0', '').replace('·', '').strip()
        if '万' in text:
            return int(float(text[:text.find('万')]) * 1e4)
        return int(text)


if __name__ == '__main__':
    # BiliCrawler.crawl_all(size=1)
    BiliCrawler('BV1Ub4y1m7Uf').crawl()
    BiliCrawler.session.close()
    pass
