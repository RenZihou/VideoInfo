# -*- encoding: utf-8 -*-
# @Author: RZH

from math import ceil
from time import time
from datetime import datetime

from django.shortcuts import render, redirect
from django.http import HttpResponse

from data.database import BiliDB


def video_index(request, page: int = 1):
    """
    response to /video/index/
    :return:
    """
    # handle jump-to
    jump_to = request.GET.get('jump_to', -1)
    if jump_to != -1:
        try:
            page = int(jump_to)
        except ValueError:
            page = 1

    # handle search
    search = request.GET.get('search', '')

    # handle normal page
    t1 = time()
    with BiliDB() as db:
        keys = ('avid', 'bvid', 'title', 'description', 'pic', 'play', 'danmaku',
                'like', 'coin', 'collect', 'up_uid', 'duration')
        page_total = ceil(list(db.execute('SELECT MAX(ROWID) FROM videos'))[0][0] / 20)
        if not 1 <= page <= page_total:
            page = 1
        start = (page - 1) * 20 + 1
        end = page * 20 + 1
        if not search:
            video_list = list(map(
                lambda v: dict(zip(keys, v)),
                db.execute('''SELECT avid, bvid, title, description, pic, play, 
                              danmaku, like, coin, collect, up_uid, duration
                              FROM videos WHERE (? <= ROWID) AND (ROWID < ?)''', (start, end,))))
        else:
            video_list = list(map(
                lambda v: dict(zip(keys, v)),
                db.execute('''SELECT avid, bvid, title, description, pic, play,
                              danmaku, like, coin, collect, up_uid, duration
                              FROM videos WHERE (title LIKE ?) OR (description LIKE ?)''', ('%%%s%%' % search,) * 2)))
            page_total = ceil(len(video_list) / 20)
            video_list = video_list[start:end]

        for video in video_list:
            up_uid = video['up_uid']
            try:
                name = list(db.execute('SELECT name FROM ups WHERE uid = ?', (up_uid,)))[0][0]
            except IndexError:
                name = '<unknown>'
            video['up_name'] = name
    t2 = time()
    # TODO: search result is empty
    page_start = max(2, page - 3)
    page_end = min(page_total - 1, page + 3)
    page_list = list(range(page_start, page_end + 1))
    page_list = sum(([1], [-1] if page_list[0] != 2 else [], page_list,
                     [-1] if page_list[-1] != page_total - 1 else [], [page_total]), [])
    page_prev = page - 1 if page != 1 else -1
    page_next = page + 1 if page != page_total else -1
    return render(request=request, template_name='video_index.html',
                  context={'video_list': video_list, 'page_list': page_list, 'total_page': page_total,
                           'current_page': page, 'next_page': page_next, 'prev_page': page_prev,
                           'search_keyword': search, 'time_ms':  '%.1f ms' % ((t2 - t1) * 1000)})


def author_index(request, page: int = 1):
    """

    :param page:
    :param request:
    :return:
    """
    # handle jump-to
    jump_to = request.GET.get('jump_to', -1)
    if jump_to != -1:
        try:
            page = int(jump_to)
        except ValueError:
            page = 1

    # handle search
    search = request.GET.get('search', '')

    # handle normal page
    t1 = time()
    with BiliDB() as db:
        keys = ('uid', 'name', 'introduction', 'fans')
        page_total = ceil(list(db.execute('SELECT MAX(ROWID) FROM ups'))[0][0] / 10)
        if not 1 <= page <= page_total:
            page = 1
        start = (page - 1) * 10 + 1
        end = page * 10 + 1
        if not search:
            author_list = list(map(
                lambda a: dict(zip(keys, a)),
                db.execute('''SELECT uid, name, introduction, fans
                              FROM ups WHERE (? <= ROWID) AND (ROWID < ?)''', (start, end,))))
        else:
            author_list = list(map(
                lambda a: dict(zip(keys, a)),
                db.execute('''SELECT uid, name, introduction, fans
                              FROM ups WHERE (name LIKE ?) OR (introduction LIKE ?)''', ('%%%s%%' % search,) * 2)
            ))
            page_total = ceil(len(author_list) / 20)
            author_list = author_list[start:end]
    t2 = time()
    page_start = max(2, page - 3)
    page_end = min(page_total - 1, page + 3)
    page_list = list(range(page_start, page_end + 1))
    page_list = sum(([1], [-1] if page_list[0] != 2 else [], page_list,
                     [-1] if page_list[-1] != page_total - 1 else [], [page_total]), [])
    page_prev = page - 1 if page != 1 else -1
    page_next = page + 1 if page != page_total else -1
    return render(request=request, template_name='author_index.html',
                  context={'author_list': author_list, 'page_list': page_list, 'total_page': page_total,
                           'current_page': page, 'next_page': page_next, 'prev_page': page_prev,
                           'search_keyword': search, 'time_ms': '%.1f ms' % ((t2 - t1) * 1000)})


def video_detail(request, bvid: str = ''):
    """

    :param request:
    :param bvid:
    :return:
    """
    keys_v = ('avid', 'bvid', 'title', 'description', 'url', 'play', 'danmaku',
              'like', 'coin', 'collect', 'up_uid', 'pub_time')
    keys_a = ('uid', 'name', 'introduction', 'fans')
    with BiliDB() as db:
        video = list(db.execute('''SELECT avid, bvid, title, description, url, 
                                   play, danmaku, like, coin, collect, up_uid, pub_time
                                   FROM videos WHERE bvid = ?''', (bvid,)))
        if not video:  # empty list: video info doesn't exist
            return HttpResponse('No video found.')
        video = dict(zip(keys_v, video[0]))
        video['pub_time'] = datetime.fromtimestamp(video['pub_time']).strftime('%Y-%m-%d %H:%M:%S')
        author = list(db.execute('''SELECT uid, name, introduction, fans 
                                    FROM ups WHERE uid = ?''', (video['up_uid'],)))
        if not author:
            return HttpResponse('No author found.')
        author = dict(zip(keys_a, author[0]))
        comment = list(db.execute('''SELECT comment_1, comment_2, comment_3, comment_4, comment_5 
                                     FROM comments WHERE bvid = ?''', (bvid,)))
        try:
            comment = list(filter(lambda x: x, comment[0]))
        except IndexError:
            comment = []
    return render(request=request, template_name='video_detail.html',
                  context={'video': video, 'author': author, 'comment_list': comment})


def author_detail(request, uid: str = ''):
    """

    :param request:
    :param uid:
    :return:
    """
    keys_a = ('uid', 'name', 'introduction', 'fans')
    keys_v = ('avid', 'bvid', 'title')
    with BiliDB() as db:
        author = list(db.execute('''SELECT uid, name, introduction, fans 
                      FROM ups WHERE uid = ?''', (uid,)))
        if not author:
            return HttpResponse('No author found.')
        author = dict(zip(keys_a, author[0]))
        video_list = list(map(
            lambda x: dict(zip(keys_v, x)),
            db.execute('''SELECT avid, bvid, title 
                                        FROM videos WHERE up_uid = ?''', (uid,))))
    return render(request=request, template_name='author_detail.html',
                  context={'author': author, 'video_list': video_list})


def video_search(request, search: str = ''):
    """

    :param request:
    :param search:
    :return:
    """
    page = request.GET.get('jump_to', 1)
    return redirect('/video/index/%s?search=%s' % (page, search))


def author_search(request, search: str = ''):
    """

    :param request:
    :param search:
    :return:
    """
    page = request.GET.get('jump_to', 1)
    return redirect('/author/index/%s?search=%s' % (page, search))


if __name__ == '__main__':
    pass
