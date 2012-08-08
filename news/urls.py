#  -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from news.views import NewsList

urlpatterns = patterns('',
    url(r'^torvi/?$', 'news.views.index', name='index'),
    url(r'^torvi/list/$', NewsList.as_view(), name='list'),
    url(r'^torvi/new/', 'news.views.new', name='new'),
    url(r'^torvi/edit/(?P<mid>[0-9]+/?)?$', 'news.views.edit', name='edit'),
    url(r'^torvi/edit/message/', 'news.views.message_json', name='message_json'),
    url(r'^torvi/facebook/$', 'news.views.FBRenewToken', name='FBRenew'),
    url(r'^torvi/facebook/token/$', 'news.views.FBGetToken', name='FBGet'),
    url(r'^torvi/twitter/token/', 'news.views.add_twitter_token', name='add_twitter_token'),
    url(r'^torvi/twitter/$', 'news.views.getTwitterToken', name='getTwitterToken'),
)
