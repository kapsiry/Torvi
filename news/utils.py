#  -*- coding: utf-8 -*-

from math import floor
from xml.parsers.expat import ExpatError
from django.core.exceptions import ValidationError
from libxml2 import parseDoc, parserError
import re
from urlparse import urljoin
from subprocess import Popen, PIPE, STDOUT
from time import sleep

from news.settings import MESSAGE_FORMAT

"""function tochar($int) {
        $ret = (string) '';
        if ( $int < 10 ) return $int;
        if ( $int < 36 ) return chr($int + 55);
        if ( $int < 62 ) return chr($int + 61);
        return $ret;
}
 
function from4id($int) {
        $ret = (string) '';
        $ret = tochar(floor($int / 238328))
             . tochar(floor(($int % 238328) / 3844))
             . tochar(floor(($int % 3844) / 62))
             . tochar($int % 62);
        for ($i=0;$i<=3;$i++) if ($ret{0} == '0') $ret = substr($ret, 1);
        return $ret;
}"""

def tochar(num):
    num = int(num)
    if num is 0:
        return ''
    elif num < 10:
        return str(num)
    elif num < 36:
        return chr(num + 55)
    elif num < 62:
        return chr(num + 61)
    return ''

def from4id(num):
    nums = [int(floor(num / 238328)), int(floor((num % 238328) / 3844)), int(floor((num % 3844) / 62)), int(num % 62)]
    return ''.join([tochar(num) for num in nums if tochar(num) != ''])

http_re = re.compile('^https?:')

def get_absolute_uri(request):
    location = request.get_full_path()
    if not http_re.match(location): 
        current_uri = '%s://%s%s' % (request.is_secure() and 'https' or 'http', request.get_host(), request.path)
        location = urljoin(current_uri, location)
    return location

def testXML(message):
    message = "<div>\n%s\n</div>" % message
    try:
        parseDoc(message.encode('utf-8'))
    except parserError:
        raise ValidationError(u'message contains invalid XML')

def html2text(html):
    w3m = Popen(['w3m', '-dump', '-T', 'text/html', '-O','utf-8','-no-graph'],stdin=PIPE, stdout=PIPE)
    retval = w3m.communicate(html.encode("utf-8"))[0].decode("utf-8")
    retval = retval.replace(u"”", u"\"").replace(u"—", u" - ")
    return retval
    
def format_email(args):
    if 'message' not in args:
        return False
    #if args['message'] is not None:
    #    return False
    args['html_message'] = args['message']
    args['message'] = html2text(args['html_message']).strip()
    message = MESSAGE_FORMAT % args
    return message