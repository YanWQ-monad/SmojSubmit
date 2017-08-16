# -*- coding: utf-8 -*-

import urllib.request
import urllib.parse
import http.cookiejar
import threading
import sublime

from .. import common, log
from .  import config

class LoginThreading(threading.Thread):
    def __init__(self, username, password, callback_opener, callback_loginf, relogin, opener=None):
        self.username        = username
        self.password        = password
        self.callback_opener = callback_opener
        self.callback_loginf = callback_loginf
        self.relogin         = relogin
        self.opener          = opener
        self.result          = None
        threading.Thread.__init__(self)

    def test_login(self, opener):
        r = urllib.request.Request(url=config.root_url+'/', headers=common.headers)
        response = opener.open(r)
        if response.url.find('/login') != -1:
            return False
        else:
            return True

    def logout(self, opener):
        if self.opener is None:
            self.result = False
            return None
        opener = self.opener
        r = urllib.request.Request(url=config.root_url+'/logout', headers=common.headers)
        self.callback_loginf(False)
        response = opener.open(r)

    def run(self):
        if self.relogin:
            sublime.status_message('Logging out...')
            self.logout(self.opener)
            opener = self.opener
            log.debug('Log out from SMOJ')
        else:
            cookie  = http.cookiejar.CookieJar()
            handler = urllib.request.HTTPCookieProcessor(cookie)
            opener  = urllib.request.build_opener(handler)
        log.info('Log in to SMOJ with user \'%s\'' % self.username)
        sublime.status_message('Logging in...')
        values  = {'redirect_to':'', 'username':self.username, 'password':self.password}
        r = urllib.request.Request(url=config.root_url+'/login', data=urllib.parse.urlencode(values).encode(), headers=common.headers)
        response = opener.open(r)
        if self.test_login(opener):
            self.callback_opener(opener)
            self.callback_loginf(True)
            self.result = True
            sublime.status_message('Login OK')
            log.debug('Log in to SMOJ OK')
        else:
            self.callback_loginf(False)
            self.result = False
            sublime.status_message('Login fail')
            log.warning('Login fail')
