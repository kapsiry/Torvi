#  -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as __
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.db.models import Max

from .settings import *

from subprocess import Popen, PIPE
from datetime import datetime, timedelta
import requests
from email.utils import formataddr
import logging
from pytz import timezone

from news.utils import from4id, testXML, html2text, format_email
import difflib

logger = logging.getLogger(__name__)


LOG_TYPES = (
    ('F', 'Facebook'),
    ('T', 'Twitter'),
    ('E', 'Email'),
    ('P', 'Publish'),
    ('U', 'Unpublish'),
    ('M', 'Modifed'),
    ('O', 'Other')
)


class News(models.Model):
    creator    = models.CharField(max_length=256, 
                                verbose_name = _('Creator'), blank=True)
    sender     = models.EmailField(max_length=256,
                                verbose_name = _('Sender'),
                                default=default_email_sender)
    subject    = models.CharField(max_length=512,
                                verbose_name=_('Subject'), blank=True)
    message    = models.CharField(max_length=50000,
                                verbose_name=_('Message'), blank=True,
                                validators=[testXML])
    email_message = models.CharField(max_length=50000,
                                     verbose_name=_('Email message'),
                                     blank=True)
    modifed    = models.DateTimeField(auto_now=True)
    published  = models.DateTimeField(null=True, blank=True, default=None)
    publishid  = models.IntegerField(null=True, blank=True, unique=True)
    totwitter  = models.BooleanField(blank=False, default=False,
                                    verbose_name = _("Tweet?"))
    toemail    = models.CharField(max_length=8096, blank=True)
    tofacebook = models.BooleanField(blank=False, default=False,
                                    verbose_name = _("Facebook?"))

    class Meta:
        ordering = ['modifed']

    def clean(self):
        testXML(self.message)

    def send_mail(self, addr=None, message=None):
        retval = ''
        if not addr:
            addr = self.toemail
        if not addr:
            return False
        addr = addr.strip()
        if addr == 'all':
            # TODO: implement this
            raise NotImplementedError
        subject = self.subject.strip()
        if type(subject) == type(""):
            subject = str(subject)
        if message is None or message == "":
            message = format_email({'message' : self.message,
                        'subject' : subject, 'creator' : self.creator})
            if not message:
                return False
        logentries = Logs.objects.filter(news_id=self.id, source="E", error=False)
        for recipiement in addr.split(','):
            if logentries.filter(action__icontains=recipiement):
                # don't resend message
                #continue
                subject = "%s: %s" % (__("Correction"), subject)
            try:
                send_mail(subject, message,
                      formataddr((self.creator,self.sender)),
                      [recipiement],fail_silently=False)
                # For legacy charset ... Don't use!
                #email = EmailMessage(subject, message,
                #                formataddr((self.creator,self.sender)),
                #                [recipiement])
                #email.encoding = 'iso-8859-1'
                #email.send()
                addLogEntry(self,
                    _('Email sent successfully to %(recipiement)s' % {
                            'recipiement' : recipiement}),
                            error=False, source='E')
            except Exception as error:
                retval += "Failed emailing to %s: %s\n" % (recipiement, error)
        if retval == '':
            return True
        else:
            return retval

    def unpublish(self):
        self.published = None
        self.save()
        addLogEntry(self, _('Unpublished!'), source='P')

    def publish(self, email_message=""):
        # test validity
        try:
            self.full_clean()
        except ValidationError as error:
            return "%s" % error
        self.published = datetime.now(tz=timezone(TIME_ZONE))
        if not self.publishid:
            publishid = News.objects.filter(publishid__isnull=False).aggregate(
                                            Max('publishid'))['publishid__max']
            if publishid:
                publishid += 1
            else:
                publishid = 1
            self.publishid = publishid
        addLogEntry(self, _('Published!'), source='P')
        self.save()

        try:
            comm = Popen([COMMIT_SCRIPT], stdout=PIPE, stderr=PIPE, encoding="utf-8")
            comm.wait()
            retval = str(comm.stdout.read())
            errors = str(comm.stderr.read())
            returncode = comm.returncode
            if errors:
                addLogEntry(self, "Command error: %s" % (errors,), error=True,
                        source='P')
            addLogEntry(self, "Command output: %s" % (retval,), error=False,
                        source='P')
            addLogEntry(self, "Command exits with code %s" % (returncode,),
                        error=False, source='P')
        except Exception as error:
            notice = "Unexcpected error occured while publishing!\n%s" % error
            addLogEntry(self, notice, error=True, source='P')
            return
        if self.toemail:
            emailretval = self.send_mail(message=email_message)
            if emailretval is True:
                addLogEntry(self, _("Email(s) sent successfully!"),
                            error=False, source='E')
            else:
                addLogEntry(self, "%s" % emailretval, error=True, source='E')

    def save(self, *args, **kwargs):
        try:
            old = News.objects.get(pk=self.pk)
            self._log_diffs()
        except News.DoesNotExist:
            pass
        super(News, self).save(*args, **kwargs)

    def _log_diffs(self):
        try:
            old = News.objects.get(pk=self.pk)
        except News.DoesNotExist:
            return True
        diff = {}
        old = old.__dict__
        new = self.__dict__
        sd1 = set(old)
        sd2 = set(new)
        #Keys missing in the second dict
        for key in sd1.difference(sd2):
            diff[key] = (old[key], None)
        #Keys missing in the first dict
        for key in sd2.difference(sd1):
            diff[key] = (None, new[key])
        #Check for differences
        for key in sd1.intersection(sd2):
            if old[key] != new[key]:
                diff[key] = (old[key], new[key])
        for key in diff:
            txt = ""
            if key not in ['message', 'email_message', 'creator', 'subject']:
                continue
            change = list(diff[key])
            try:
                change[0] = change[0].strftime("%Y-%m-%d %H:%M")
            except:
                pass
            try:
                change[1] = change[1].strftime("%Y-%m-%d %H:%M")
            except:
                pass
            if key in ['message', 'email_message']:
                a = change[0]
                b = change[1]
                if a == None:
                    a = ''
                if b == None:
                    b = ''
                diffa = list(difflib.ndiff(a.splitlines(1),b.splitlines(1)))
                txt = "%s" % ''.join([i for i in diffa if not i.startswith('?')]).strip()
            elif change[0] == None:
                txt = "%s: () -> '%s'. " % (key, change[1])
            elif change[1] == None:
                txt = "%s: '%s' -> (). " % (key, change[0])
            else:
                txt = "%s: '%s' => '%s'. " % (key, change[0], change[1])
            logentry = Logs(action=txt, error=False, source='M', news=self)
            logentry.save()

    def __unicode__(self):
        return "%s (%s)" % (self.subject, self.modifed.strftime("%d.%m.%Y %H:%M"))

    def __str__(self):
        return "%s (%s)" % (self.subject, self.modifed.strftime("%d.%m.%Y %H:%M"))


class Logs(models.Model):
    date   = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=50000, blank=False)
    error  = models.BooleanField(default=False)
    source = models.CharField(max_length=1, choices=LOG_TYPES, default='O')
    news   = models.ForeignKey(News, on_delete=models.CASCADE)

    def __unicode__(self):
        return '%s: %s' % (self.date.strftime("%d.%m.%Y %H:%M"), self.action)


def addLogEntry(news, action, error=None, source=None):
    if not error and not type:
        log = Logs(action=action, news=news)
    elif not error:
        log = Logs(action=action, news=news, source=source)
    elif not type:
        log = Logs(action=action, news=news, error=error)
    else:
        log = Logs(action=action, news=news, error=error, source=source)
    log.save()
