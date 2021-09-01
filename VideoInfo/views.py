# -*- encoding: utf-8 -*-
# @Author: RZH

from django.shortcuts import render
from django.http import HttpResponse


def video_index(request):
    """
    response to video/index/
    :return:
    """
    # return HttpResponse('hello world. video list here.')
    return render(request=request, template_name='video_index.html')


if __name__ == '__main__':
    pass
