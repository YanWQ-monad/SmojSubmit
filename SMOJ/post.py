# -*- coding: utf-8 -*-

import urllib.request
import urllib.parse
import threading
import sublime
import re

from .. import common
from .  import config

pst_url = config.root_url + '/submit_problem?pid=%d'

class PostThreading(threading.Thread):
    def __init__(self, opener, cpp, problem, callback):
        self.opener   = opener
        self.cpp      = cpp
        self.problem  = problem
        self.callback = callback
        self.result   = None
        threading.Thread.__init__(self)

    def test_post(self, response):
        if response.url.find('allmysubmits') != -1:
            return True
        else:
            return False

    def run(self):
        try:
            values  = {'pid':str(self.problem), 'language':'.cpp', 'code':self.cpp}
            r = urllib.request.Request(url=(pst_url % self.problem), data=urllib.parse.urlencode(values).encode(), headers=common.headers)
            response = self.opener.open(r)
            if self.test_post(response):
                sublime.status_message('Submit OK')
                self.result  = True
                self.callback()
            else:
                sublime.status_message('Submit Fail')
                self.result  = False
        except urllib.request.HTTPError as e:
            sublime.status_message('Submit Fail')
            sublime. error_message('%s: HTTP error %s contacting API' % (__name__, str(e.code)))
            self.result  = False
        except urllib.request.URLError as e:
            sublime.status_message('Submit Fail')
            sublime. error_message('%s: URL error %s contacting API' % (__name__, str(e.reason)))
            self.result  = False
