#  -*- coding: utf-8 -*-
from django.conf.urls import url
import news.views

urlpatterns = [
    url(r'^torvi/?$', news.views.index, name='index'),
    url(r'^torvi/list/$', news.views.NewsList.as_view(), name='list'),
    url(r'^torvi/new/', news.views.new, name='new'),
    url(r'^torvi/edit/(?P<mid>[0-9]+/?)?$', news.views.edit, name='edit'),
    url(r'^torvi/edit/message/', news.views.message_json, name='message_json'),
]
