# -*- coding: utf-8 -*-

import urllib.parse
import html.parser as parser
import logging
import time
import re

from ..libs import middleware
from ..libs.exception import LoginFail, SubmitFail
from . import OjModule


logger = logging.getLogger(__name__)
lang_map = {
    'C': 0,
    'C++': 1,
    'Pascal': 2,
    'Java': 3,
    'Python': 6
}


class BzojModule(OjModule):
    name = 'bzoj'
    display_name = 'BZOJ'
    result_header = ['Result', 'Time', 'Memory']
    support_languages = ['C++', 'C', 'Java', 'Pascal', 'Python']

    root_url = 'http://www.lydsy.com/JudgeOnline'
    login_url = root_url + '/login.php'
    submit_url = root_url + '/submit.php'
    result_url = root_url + '/status.php?{}'
    compile_message_url = root_url + '/ceinfo.php?sid={}'

    result_regex_r = (
        r"<tr align=center class='(even|odd)row'>"
        r"<td>(\d+)"
        r"<td><a href='userinfo\.php\?user={name}'>{name}</a>"
        r"<td><a href='problem\.php\?id={pid}'>{pid}</a>"
        r"<td>(<a href='ceinfo\.php\?sid=\d+'>)?<font color=#?[0-9a-zA-Z]+>([a-zA-Z_&]+)</font>(</a>)?"
        r"<td>((\d+) <font color=red>kb</font>|------)"
        r"<td>((\d+) <font color=red>ms</font>|------)"
        r"<td><a target=_blank href=showsource\.php\?id=\d+>[a-zA-Z+]+</a>/<a target=_self href=.submitpage\.php\?id={pid}&sid=\d+.>Edit</a>"  # noqa: E501
        r"<td>\d+ B"
        r"<td>[0-9\- :]+</tr>")

    detail_regex_r = (
        r"<tr align=center class='(even|odd)row'>"
        r"<td>(\d+)"
        r"<td><a href='userinfo\.php\?user={name}'>{name}</a>"
        r"<td><a href='problem\.php\?id={pid}'>{pid}</a>"
        r"<td>(<a href='ceinfo\.php\?sid=\d+'>)?<font color=#?[0-9a-zA-Z]+>([a-zA-Z_&]+)</font>(</a>)?"
        r"<td>(\d+) <font color=red>kb</font>"
        r"<td>(\d+) <font color=red>ms</font>"
        r"<td><a target=_blank href=showsource\.php\?id=\d+>[a-zA-Z+]+</a>/<a target=_self href=.submitpage\.php\?id={pid}&sid=\d+.>Edit</a>"  # noqa: E501
        r"<td>\d+ B"
        r"<td>[0-9\- :]+</tr>")

    compile_message_regex = re.compile(r'<pre>(.*)</pre>', flags=re.DOTALL)

    def init(self, config):
        self.username = config['username']
        self.password = config['password']
        self.headers = config['headers']
        if config.get('init_login', False):
            self.login()

    def check_login(self):
        if self.opener is None:
            return False
        html, resp = self.get(self.root_url, self.headers)
        return html.find('<font color=red>{}</font>'.format(self.username)) != -1

    def login(self):
        self.opener, _ = self.create_opener()

        values = {
            'user_id': self.username,
            'password': self.password,
            'submit': 'Submit'
        }

        html, resp = self.post(self.login_url, values, self.headers)
        login_status = self.check_login()
        if login_status:
            message = 'Login to BZOJ OK'
            logger.info(message)
            self.set_status(message)
        else:
            raise LoginFail()

    def submit(self, runtime):
        language = lang_map[runtime.language]
        code = middleware.freopen_filter(runtime.code)

        values = {
            'id': str(runtime.pid),
            'language': language,
            'source': code
        }
        html, resp = self.post(self.submit_url, values, self.headers)
        if resp.url.find('status.php') == -1:
            if self.check_login():
                raise SubmitFail()
            else:
                raise SubmitFail('Invalid login')
        else:
            self.set_status('Submit OK, fetching result...')
            logger.info('Submit OK')

    def load_result(self, runtime):
        values = {
            'problem_id': str(runtime.pid),
            'user_id': self.username,
            'language': '-1',
            'jresult': '-1'
        }
        url = self.result_url.format(urllib.parse.urlencode(values))

        result_regex = re.compile(self.result_regex_r.format(pid=runtime.pid, name=self.username))

        while True:
            self.set_status('Waiting for judging...')
            time.sleep(1)

            html, resp = self.get(url, self.headers)
            match = result_regex.search(html)

            result = match.group(4)
            if result not in ['Pending', 'Pending_Rejudging', 'Compiling', 'Running_&_Judging']:
                break

        match = re.search(self.detail_regex_r.format(pid=runtime.pid, name=self.username), html)

        message = 'Loading result...'
        self.set_status(message)

        result = result.replace('_', ' ')
        if result.endswith('Exceed'):
            result = result + 'ed'

        judge_id = match.group(2)
        memory = match.group(6) + ' KB'
        time_ = match.group(7) + ' ms'
        detail = [result, time_, memory]

        if result == 'Compile Error':
            html, resp = self.get(self.compile_message_url.format(judge_id), self.headers)
            runtime.judge_compile_message = \
                parser.HTMLParser().unescape(self.compile_message_regex.findall(html)[0]).replace('\r', '')

        runtime.judge_detail = [detail]
        runtime.judge_result = result
        runtime.judge_score = 100 if result == 'Accepted' else 0
