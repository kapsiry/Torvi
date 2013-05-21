# encoding: utf-8
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.views.generic import ListView
from django.utils.datastructures import MultiValueDictKeyError
from django import forms
from django.core.urlresolvers import reverse

from twython import Twython, TwythonAuthError, TwythonError

import datetime as date
from oauth_hook import OAuthHook
import requests
from urlparse import parse_qs
import json
from pytz import timezone

from news.models import *
from news.utils import from4id, get_absolute_uri, format_email
from settings import FACEBOOK_APP_SECRET, FACEBOOK_APP_ID, MESSAGE_FORMAT

import logging
logger = logging.getLogger(__file__)

class NewsForm(forms.Form):
    class Meta:
        model = News
    emailto = default_email_to

class NewsList(ListView):
    #context_object_name="news_list"
    template_name = 'news/index.html'

    def get_queryset(self):
        q1 = News.objects.filter(publishid__isnull=True).order_by('-modifed')
        q2 = News.objects.filter(publishid__isnull=False)
        return q1 | q2

def index(request, **kwargs):
    form = NewsForm()
    unpublished = News.objects.filter(publishid__isnull=True).order_by('-modifed')
    return render_to_response('news/index.html',
        {'form': form, 'news_list' : unpublished },
        context_instance=RequestContext(request))

def edit(request, **kwargs):
    notice = None
    if 'mid' in kwargs:
        mid = kwargs['mid']
    else:
        mid = None
    if request.method == 'POST':
        tofacebook = False
        twitter = False
        email = False
        try:
            subject  = request.POST['subject']
            message  = request.POST['message']
            creator  = request.POST['name']
            toemail  = request.POST['emailto']
            email_message = request.POST['email']
            if 'tofacebook' in request.POST:
                tofacebook = True
            if 'totwitter' in request.POST:
                twitter = True
            id       = request.POST['newsid']
        except MultiValueDictKeyError as error:
            return new(request, **kwargs)

        try:
            news = News.objects.get(id__exact=int(id))

        except (News.DoesNotExist, ValueError) as error:
            news = News(subject=subject, message=message, creator=creator,
                        toemail=toemail, totwitter=twitter,
                        tofacebook = tofacebook)
            try:
                news.full_clean()
            except ValidationError:
                kwargs['error'] = 'Unvalid xml detected!!!!'
                kwargs['form'] = form
                return new(request, **kwargs)
            news.save()
            #return HttpResponseRedirect(reverse('new', news.id,
            #                   kwargs={'message' : message}))
            #return render_to_response('news/new.html',{'form': news,
            #                                   'message' : notice},
            #                        context_instance=RequestContext(request))
            kwargs['mid'] = news.id
            return new(request, **kwargs)

        if 'delete' in request.POST:
            news.delete()
            return redirect('list')
        if 'unpublish' in request.POST:
            news.unpublish()
            return new(request, **kwargs)
        news.subject = subject
        news.message = message.strip()
        news.creator = creator
        news.tofacebook = tofacebook
        news.totwitter = twitter
        news.toemail = toemail
        try:
            news.full_clean()
        except ValidationError:
            kwargs['error'] = 'Unvalid xml detected!!!!'
            kwargs['form'] = news
            return new(request, **kwargs)
        news.save()
        notice = 'Saved successfully!\n'
        if 'publish' in request.POST:
            news.publish(email_message=email_message)
        kwargs['message'] = notice
        kwargs['form'] = news
        return new(request, **kwargs)

    if mid:
        news = get_object_or_404(News, id__exact=mid)
        return new(request, **kwargs)
    else:
        return redirect(new)

def new(request, **kwargs):
    if 'mid' in kwargs:
        mid = kwargs['mid']
        if 'log' not in kwargs:
            kwargs['log'] = Logs.objects.filter(news_id__exact=mid).order_by(
                                                                '-date').all()
        if 'form' not in kwargs:
            kwargs['form'] = get_object_or_404(News, id__exact=mid)
    if 'form' not in kwargs:
        kwargs['form'] = NewsForm()
    return render_to_response('news/new.html', kwargs,
                        context_instance=RequestContext(request))

def FBRenewToken(request, **kwargs):
    # https://developers.facebook.com/docs/authentication/applications/
    # https://developers.facebook.com/docs/authentication/
    url = "https://www.facebook.com/dialog/oauth?client_id=%s" % FACEBOOK_APP_ID
    url += "&scope=publish_actions&redirect_uri=%stoken/&response_type=token" % (
        get_absolute_uri(request))
    return redirect(url)

def FBGetToken(request, **kwargs):
    token = ''
    if request.method == 'GET' and 'access_token' in request.GET:
        token  = request.GET['access_token']

    if request.method == 'POST' and 'token' in request.POST and 'expires' in request.POST:
        token = request.POST['token']
        expires = request.POST['expires']
        userid_req = requests.get("https://graph.facebook.com/me?access_token=%s" % token)
        #print("%s" % userid_req.text)
        userid_json = json.loads(userid_req.text)
        if 'id' in userid_json:
            userid = userid_json['id']
        else:
            return render_to_response('news/facebook.html',
                                        {'token' : token, 'expires' : expires,
                                        'message' : _("Failed to add Facebook token!")},
                                    context_instance=RequestContext(request))
        addFBToken(token, expires, userid)
        return render_to_response('news/facebook.html',
                        {'token' : token, 'expires' : expires,
                        'message': 'Added successfully!'},
                        context_instance=RequestContext(request))
    else:
        expires = datetime.now(tz=timezone(TIME_ZONE)) + date.timedelta(days=60)
    if 'expires_in' in request.GET:
        expires = datetime.now(tz=timezone(TIME_ZONE)) + date.timedelta(seconds=request.GET['expires_in'])
    return render_to_response('news/facebook.html', {'token' : token,
                            'expires' : expires},
                            context_instance=RequestContext(request))

def getTwitterToken(request, **kwargs):
    twitter = Twython(
        twitter_token = TWITTER_CONSUMER_KEY,
        twitter_secret = TWITTER_CONSUMER_SECRET,
        callback_url = request.build_absolute_uri(
                                    reverse('news.views.add_twitter_token'))
        )
    try:
        auth_props = twitter.get_authentication_tokens()
    except TwythonAuthError as e:
        kwargs['error'] = e
        return render_to_response('news/twitter_error.html', kwargs,
                                    context_instance=RequestContext(request))
    
    request.session['request_token'] = auth_props
    return HttpResponseRedirect(auth_props['auth_url'])


def add_twitter_token(request, **kwargs):
    
    if request.method == 'GET':
        twitter = Twython(
            twitter_token = TWITTER_CONSUMER_KEY,
            twitter_secret = TWITTER_CONSUMER_SECRET,
            oauth_token = request.session['request_token']['oauth_token'],
            oauth_token_secret = request.session['request_token']['oauth_token_secret'],
        )
        oauth_verifier = request.GET['oauth_verifier']
        try:
            authorized_tokens = twitter.get_authorized_tokens(oauth_verifier)
            if 'oauth_token' not in authorized_tokens:
                raise TwythonError(authorized_tokens)
            oauth_token = authorized_tokens['oauth_token']
            oauth_secret = authorized_tokens['oauth_token_secret']
            tw = addTwitterToken(token=oauth_token, secret=oauth_secret)
        except TwythonError as e:
            kwargs['error'] = e
            return render_to_response('news/twitter_error.html', kwargs,
                                    context_instance=RequestContext(request))
        return render_to_response('news/twitter.html', {},
                                      context_instance=RequestContext(request))
    else:
        raise Http404

def message_json(request, **kwargs):
    if request.method != 'POST':
        raise Http404
    if 'message' not in request.POST or 'subject' not in request.POST:
        raise Http404
    creator = ""
    if 'creator' in request.POST:
        creator = request.POST['creator']
    message = format_email({'message': request.POST['message'],
                    'subject': request.POST['subject'], 'creator' : creator})
    return HttpResponse(message, mimetype="text/plain")
