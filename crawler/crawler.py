# -*- encoding: utf-8 -*-
# @Author: RZH

import requests
from lxml import etree


class BiliCrawler(object):
    # url = 'https://www.bilibili.com/v/popular/all'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; '
                             'Trident/7.0; rv:11.0) like Gecko'}

    def __init__(self):
        pass

    def get_popular(self):
        """
        get popular video list: video url, title, up, play, danmaku, image
        :return:
        """
        pass

    def get_details(self):
        """
        get video details: description, like, coin, star, comments(5)
        get up details: name, uid, intro, avatar, fans
        :return:
        """
        api = 'https://api.bilibili.com/x/web-interface/view'
        
        pass

    def save_to_db(self):
        """
        save crawled data to database
        :return:
        """
        pass


if __name__ == '__main__':
    pass
