from django import template

register = template.Library()

from news.models import Twitter_available, Facebook_available

def Fb_available(context):
    return Facebook_available()

def Tw_available(context):
        return Twitter_available()

register.filter('fbavail', Fb_available)
register.filter('twavail', Tw_available)