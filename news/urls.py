#  -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from news.views import NewsList

urlpatterns = patterns('',
    url(r'^$', 'news.views.index', name='index'),
    url(r'^list/$', NewsList.as_view(), name='list'),
    url(r'^new/', 'news.views.new', name='new'),
    url(r'^edit/(?P<mid>[0-9]+/?)?$', 'news.views.edit', name='edit'),
    url(r'^edit/message/', 'news.views.message_json', name='message_json'),
    url(r'^facebook/$', 'news.views.FBRenewToken', name='FBRenew'),
    url(r'^facebook/token/$', 'news.views.FBGetToken', name='FBGet'),
    url(r'^twitter/token/', 'news.views.add_twitter_token', name='add_twitter_token'),
    url(r'^twitter/$', 'news.views.getTwitterToken', name='getTwitterToken'),
)
