"""VideoInfo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from VideoInfo import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.video_index, name='video_index'),
    path('video/index/', views.video_index, name='video_index'),
    path('video/index/<int:page>', views.video_index, name='video_index'),
    path('video/index/search/<str:search>', views.video_search, name='video_search'),
    path('author/index/', views.author_index, name='author_index'),
    path('author/index/<int:page>', views.author_index, name='author_index'),
    path('author/index/search/<str:search>', views.author_search, name='author_search'),
    path('video/detail/<str:bvid>', views.video_detail, name='video_detail'),
    path('author/detail/<str:uid>', views.author_detail, name='author_detail'),
]
