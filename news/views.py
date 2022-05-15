# encoding: utf-8
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, HttpResponse
from django.views.generic import ListView
from django.utils.datastructures import MultiValueDictKeyError
from django import forms

from news.models import *
from news.utils import format_email

import logging
logger = logging.getLogger(__file__)


class NewsForm(forms.Form):
    class Meta:
        model = News
    emailto = default_email_to


class NewsList(ListView):
    template_name = 'news/index.html'

    def get_queryset(self):
        q1 = News.objects.filter(publishid__isnull=True).order_by('-modifed')
        q2 = News.objects.filter(publishid__isnull=False)
        return q1 | q2


def index(request, **kwargs):
    form = NewsForm()
    unpublished = News.objects.filter(publishid__isnull=True).order_by('-modifed')
    return render(
        request,
        'news/index.html',
        {'form': form, 'news_list': unpublished},
    )


def edit(request, **kwargs):
    notice = None
    if 'mid' in kwargs:
        mid = kwargs['mid']
    else:
        mid = None
    if request.method == 'POST':
        try:
            subject = request.POST['subject']
            message = request.POST['message']
            creator = request.POST['name']
            toemail = request.POST['emailto']
            email_message = request.POST['email']
            id = request.POST['newsid']
        except MultiValueDictKeyError as error:
            return new(request, **kwargs)

        try:
            news = News.objects.get(id__exact=int(id))

        except (News.DoesNotExist, ValueError) as error:
            news = News(subject=subject, message=message, creator=creator,
                        toemail=toemail)
            try:
                news.full_clean()
            except ValidationError:
                kwargs['error'] = 'Unvalid xml detected!!!!'
                kwargs['form'] = form
                return new(request, **kwargs)
            news.save()
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
    return render(request, 'news/new.html', kwargs)


def message_json(request, **kwargs):
    if request.method != 'POST':
        raise Http404
    if 'message' not in request.POST or 'subject' not in request.POST:
        raise Http404
    creator = ""
    if 'creator' in request.POST:
        creator = request.POST['creator']
    message = format_email({
        'message': request.POST['message'],
        'subject': request.POST['subject'],
        'creator': creator
    })
    return HttpResponse(message, mimetype="text/plain")
