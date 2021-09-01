# -*- encoding: utf-8 -*-
# @Author: RZH

from math import ceil

from django.shortcuts import render
from django.http import HttpResponse

from data.database import BiliDB


def video_index(request, page: int = 1):
    """
    response to video/index/
    :return:
    """
    # handle jump-to
    jump_to = request.GET.get('jump_to', -1)
    if jump_to != -1:
        try:
            page = int(jump_to)
        except ValueError:
            page = 1

    # handle normal page
    keys = ('avid', 'bvid', 'title', 'description', 'url', 'pic', 'play', 'danmaku',
            'like', 'coin', 'collect', 'up_uid')
    with BiliDB() as db:
        page_total = ceil(list(db.execute('SELECT MAX(ROWID) FROM videos'))[0][0] / 20)
        if not 1 <= page <= page_total:
            page = 1
        start = (page - 1) * 20 + 1
        end = page * 20 + 1
        video_list = list(map(
            lambda v: dict(zip(keys, v)),
            db.execute('''SELECT avid, bvid, title, description, url, pic, play, danmaku, like, coin, collect, up_uid
                       FROM videos WHERE (? <= ROWID) AND (ROWID < ?)''', (start, end))))
        for video in video_list:
            up_uid = video['up_uid']
            try:
                name = list(db.execute('SELECT name FROM ups WHERE uid = ?', (up_uid,)))[0][0]
            except IndexError:
                name = '<unknown>'
            video['up_space'] = 'https://space.bilibili.com/%d' % up_uid
            video['up_name'] = name
    page_start = max(2, page - 3)
    page_end = min(page_total - 1, page + 3)
    page_list = list(range(page_start, page_end + 1))
    page_list = sum(([1], [-1] if page_list[0] != 2 else [], page_list,
                     [-1] if page_list[-1] != page_total - 1 else [], [page_total]), [])
    page_prev = page - 1 if page != 1 else -1
    page_next = page + 1 if page != page_total else -1
    return render(request=request, template_name='video_index.html',
                  context={'video_list': video_list, 'page_list': page_list, 'total_page': page_total,
                           'current_page': page, 'next_page': page_next, 'prev_page': page_prev})


if __name__ == '__main__':
    pass
