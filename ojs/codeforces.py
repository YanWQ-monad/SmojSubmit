# -*- coding: utf-8 -*-
import threading
import websocket
import logging
import sublime
import copy
import json
import time
import ssl
import re

from ..libs import cookie
from ..libs import printer
from ..libs import figlet
from ..libs.middleware import freopen_filter
from ..libs.exception import LoginFail, SubmitFail, ExitScript
from . import OjModule


logger = logging.getLogger(__name__)


lang_map = {
    'C11': 43,
    'Clang++17': 52,
    'C++11': 42,
    'C++14': 50,
    'C++17': 54,
    'MS C++ 2010': 2,
    'MS C++ 2017': 59,
    'C# Mono': 9,
    'D': 28,
    'Go': 32,
    'Haskell': 12,
    'Java': 36,
    'Kotlin': 48,
    'OCaml': 19,
    'Delphi': 3,
    'Free Pascal': 4,
    'PascalABC': 51,
    'Perl': 13,
    'PHP': 6,
    'Python2': 7,
    'Python3': 31,
    'PyPy2': 40,
    'PyPy3': 41,
    'Ruby': 8,
    'Rust': 49,
    'Scala': 20,
    'JavaScript V8': 34,
    'Node.js': 55,
    # Redirect:
    'C': 43,
    'C++': 42,
    'Python': 31,
    'JavaScript': 34,
    'Pascal': 4,
    'C#': 9
}


result_map = {
    'FAILED': 'Unaccepted',
    'OK': 'Accepted',
    'PARTIAL': 'Unaccepted',
    'COMPILATION_ERROR': 'Compile Error',
    'RUNTIME_ERROR': 'Runtime Error',
    'WRONG_ANSWER': 'Wrong Answer',
    'PRESENTATION_ERROR': 'Presentation Error',
    'TIME_LIMIT_EXCEEDED': 'Time Limit Exceeded',
    'MEMORY_LIMIT_EXCEEDED': 'Memory Limit Exceeded',
    'IDLENESS_LIMIT_EXCEEDED': 'Time Limit Exceeded',
    'SECURITY_VIOLATED': 'Restrict Function',
    'CRASHED': 'Unaccepted',
    'INPUT_PREPARATION_CRASHED': 'Unaccepted',
    'CHALLENGED': 'Unaccepted',
    'SKIPPED': 'Unaccepted',
    'REJECTED': 'Unaccepted'
}


class CodeforcesResultView(printer.SmojResultView):
    header = ['ID', 'Result', 'Time', 'Memory', 'Checker Log']
    judging_detail = [None, 'Running', '', '', '']

    def __init__(self, name, pid):
        printer.SmojResultView.__init__(self, name)
        self.judging = True
        self.compile_msg_height = 0
        self.pid = pid
        self.detail_row = 0
        self.current_line = 0

    def add_line(self, content, line=None):
        count = len(content.split('\n'))
        if content.endswith('\n'):
            self.current_line += count - 1
        else:
            self.current_line += count
        super(CodeforcesResultView, self).add_line(content, line)

    def create_view(self):
        super(CodeforcesResultView, self).create_view()
        self.add_line('Problem ID: {}'.format(self.pid))
        self.add_line(figlet.get_figlet('Pending'))

    def update_figlet(self, result):
        lines = figlet.get_figlet(result)
        if lines[-1] == '\n':
            lines = lines[:-1]
        lines = lines.split('\n')
        for i, line in enumerate(lines):
            self.update_line(line, i + 2)

    def update_line(self, content, line):
        if line > self.current_line:
            self.add_line(content)
        elif self.view.substr(self.view.line(self.view.text_point(line - 1, 0))) != content:
            self.view.run_command('smoj_replace_line_readonly', {'line': line, 'content': content})

    def update_with(self, details):
        if not self.is_open():
            return
        details = copy.deepcopy(details)
        if self.judging:
            self.judging_detail[0] = str(len(details) + 1)
            details = details + [self.judging_detail]
        header, details = printer.pretty_format(self.header, details)
        self.update_detail(header, details)

    def set_compile_msg(self, content):
        self.compile_msg_height = len(content.split('\n'))
        self.add_line('Compile information:', 8)
        self.add_line(content, 9)

    def update_detail(self, head, detail):
        tot_len = len('  '.join(head)) + 2
        self.update_line('-' * (tot_len + len(head) + 1), 8 + self.compile_msg_height)
        self.update_line('| ' + ' | '.join(head) + ' |', 9 + self.compile_msg_height)
        self.update_line('|' + '-' * (tot_len + len(head) - 1) + '|', 10 + self.compile_msg_height)
        for i, row in enumerate(detail):
            self.update_line('| ' + ' | '.join(row) + ' |', 11 + i + self.compile_msg_height)
        self.update_line('-' * (tot_len + len(head) + 1), 11 + len(detail) + self.compile_msg_height)

    def add_detail(self, head, detail):
        tot_len = len('  '.join(head)) + 2
        self.add_line('-' * (tot_len + len(head) + 1))
        self.add_line('| ' + ' | '.join(head) + ' |')
        self.add_line('|' + '-' * (tot_len + len(head) - 1) + '|')
        for i, row in enumerate(detail):
            self.add_line('| ' + ' | '.join(row) + ' |')
        self.add_line('-' * (tot_len + len(head) + 1))


class CodeforcesModule(OjModule):
    name = 'codeforces'
    display_name = 'Codeforces'
    support_languages = [
        'C', 'C++', 'Python', 'JavaScript', 'C#', 'D', 'Go', 'Haskell', 'Java', 'Kotlin',
        'OCaml', 'Perl', 'PHP', 'Ruby', 'Rust', 'Scala', 'Pascal']

    root_url = 'https://codeforces.com'
    websocket_root_url = 'wss://pubsub.codeforces.com'
    websocket_live_url = websocket_root_url + '/ws/s_{cc}/s_{pc}?_={time}&tag=&time=&eventid='
    empty_url = root_url + '/404'
    login_url = root_url + '/enter'
    submit_url = root_url + '/{}/{}/submit?csrf_token={}'
    submit_page = root_url + '/{}/{}/submit'
    result_url = root_url + '/{}/{}/my'
    detail_url = root_url + '/data/submitSource'
    result_api_url = root_url + '/api/contest.status?handle={}&from=1&count=1&contestId={}'

    login_check_substr = '<a href="/profile/{0}">{0}</a>'
    csrf_token_regex = re.compile(r'<meta name="X-Csrf-Token" content="([a-f0-9]+)" ?/>')
    codeforces_pid_regex = re.compile(r'(\d+)([A-Z]\d?)')
    cc_token_regex = re.compile(r'<meta name="cc" content="([a-f0-9]+)" ?/>')
    pc_token_regex = re.compile(r'<meta name="pc" content="([a-f0-9]+)" ?/>')
    reason_regex = re.compile(r'<span class=\"error for__source\">([^<]+)</span>')

    class RuntimeVariable(OjModule.RuntimeVariable):
        def __init__(self, *args, **kwargs):
            super(CodeforcesModule.RuntimeVariable, self).__init__(*args, **kwargs)
            self.sync_id = 0
            self.view = None
            self.details = []
            self.judging = False
            self.submission_id = None
            self.lock = None

    def init(self, config):
        self.username = config['username']
        self.password = config['password']
        self.headers = config['headers']
        self.is_login = False
        self.opener, self.cookie = self.create_opener()

        if cookie.load_cookie('codeforces', 'codeforces.com', self.cookie, ['X-User-Sha1', 'JSESSIONID']):
            self.is_login = True

        if config.get('init_login', False) and not self.check_login():
            self.login()

    def check_login(self):
        if self.is_login is False:
            return False
        html, resp = self.get(self.empty_url, self.headers)
        return html.find(self.login_check_substr.format(self.username)) != -1

    def login(self):
        self.csrf_token = self._get_csrf_token()

        payload = {
            'csrf_token': self.csrf_token,
            'action': 'enter',
            'handleOrEmail': self.username,
            'password': self.password,
            'remember': 'on'
        }

        html, resp = self.post(self.login_url, payload, self.login_url)
        self.is_login = True
        if self.check_login():
            message = 'Login to Codeforces OK'
            logger.info(message)
            self.set_status(message)
        else:
            reasons = self.reason_regex.findall(html)
            if len(reasons) > 0:
                raise LoginFail(reasons[0])
            raise LoginFail()

        cookie.save_cookie('codeforces', self.cookie, ['X-User-Sha1', 'JSESSIONID'])

    def submit(self, runtime):
        code = freopen_filter(runtime.code)
        self.csrf_token = self._get_csrf_token()
        contest, pid = self._parse_problem_id(runtime.pid)
        url = self.submit_url.format('contest', contest, self.csrf_token)
        program_type = lang_map[runtime.language]
        expect_url = self.result_url.format('contest', contest)

        payload = {
            'csrf_token': self.csrf_token,
            'action': 'submitSolutionFormSubmitted',
            'submittedProblemIndex': pid,
            'programTypeId': program_type,
            'source': code,
            'tabSize': '4',
            'sourceFile': ''
        }

        html, resp = self.post(url, payload, self.submit_page.format('contest', contest))
        if resp.url != expect_url:
            with open('XYZZYX.html', 'wb') as f:
                f.write(html.encode())
            reasons = self.reason_regex.findall(html)
            if len(reasons) > 0:
                raise SubmitFail(reasons[0])

    def load_result(self, runtime):
        contest, pid = self._parse_problem_id(runtime.pid)
        url = self.result_url.format('contest', contest)
        html, resp = self.get(url, self.headers)

        cookies = ';'.join(['{}={}'.format(item.name, item.value) for item in self.cookie])
        cc_token, pc_token = self._get_websocket_token(html)
        timestamp = int(time.time() * 1000)
        websocket_url = self.websocket_live_url.format(cc=cc_token, pc=pc_token, time=timestamp)
        logger.debug('Make WebSocket request: {}'.format(websocket_url))
        ws = websocket.create_connection(
            websocket_url, sslopt={'cert_reqs': ssl.CERT_NONE}, cookie=cookies)

        runtime.view = CodeforcesResultView('Result', runtime.pid)
        runtime.view.create_view()
        runtime.view.update_with([])
        runtime.judging = True
        runtime.lock = threading.Lock()

        threading.Thread(target=lambda: self._fetch_detail_process(runtime)).start()
        last_id = 0
        while True:
            logger.debug('Waiting for websocket message')
            msg = json.loads(ws.recv())
            logger.debug('Websocket receive: {}'.format(msg))
            data = json.loads(msg['text'])
            logger.debug('Judge message: {}'.format(data))
            if msg['id'] <= last_id:
                continue
            last_id = msg['id']
            judge_count = data['d'][8]
            if runtime.submission_id is None:
                runtime.submission_id = data['d'][1]

            runtime.view.update_figlet('Waiting')
            logger.debug('Submission runs to {}'.format(judge_count))

            if data['d'][6] != 'TESTING':
                runtime.view.judging = False

            with runtime.lock:
                for i in range(len(runtime.details), judge_count):
                    logger.debug('Add a testcase line #{}'.format(i + 1))
                    runtime.details.append([str(i + 1), 'Fetching', '', '', ''])
                runtime.view.update_with(runtime.details)

            if len(runtime.details) != judge_count:
                runtime.sync_id += 1
            if data['d'][6] != 'TESTING':
                break

            time.sleep(1)

        runtime.sync_id += 1
        runtime.judging = False
        ws.close()
        logger.debug('Main thread listening ended')

        data, resp = self.get(self.result_api_url.format(self.username, contest), self.headers)
        data = json.loads(data)
        result = data['result'][0]['verdict']
        result = result_map.get(result, result)
        runtime.view.update_figlet(result)

        raise ExitScript()

    def post(self, url, payload, referer):
        headers = self.headers.copy()
        headers['Origin'] = self.root_url
        headers['Referer'] = referer
        return super(CodeforcesModule, self).post(url, payload, headers)

    def work(self, pid, code, language):
        self._check_printf_lld(code)
        return super(CodeforcesModule, self).work(pid, code, language)

    def _fetch_detail_process(self, runtime):
        contest, pid = self._parse_problem_id(runtime.pid)
        referer = self.result_url.format('contest', contest)
        logger.debug('Child thread started')
        local_id = 0
        current_testcase = 1

        while runtime.judging or local_id < runtime.sync_id:
            while local_id >= runtime.sync_id and runtime.judging:
                time.sleep(0.1)
            logger.debug('Detected sync id increase to {} ({}'.format(runtime.sync_id, runtime.judging))
            local_id = runtime.sync_id

            payload = {
                'submissionId': runtime.submission_id,
                'csrf_token': self.csrf_token
            }

            data, resp = self.post(self.detail_url, payload, referer)
            data = json.loads(data)
            logger.debug('Detail data: {}'.format(data))

            prev_testcase = current_testcase
            while 'answer#{}'.format(current_testcase) in data:
                logger.debug('New testcase received: {}'.format(current_testcase))
                current_testcase += 1
            current_testcase = min(current_testcase, len(runtime.details) + 1)

            with runtime.lock:
                for i in range(prev_testcase, current_testcase):
                    result = result_map.get(data['verdict#{}'.format(i)], data['verdict#{}'.format(i)])
                    time_ = data['timeConsumed#{}'.format(i)] + 'ms'
                    memory = str(int(data['memoryConsumed#{}'.format(i)]) // 1024) + 'KB'
                    checker_log = data['checkerStdoutAndStderr#{}'.format(i)].rstrip('\r\n')
                    logger.debug('Update detail {} => {}'.format(i, [result, time_, memory, checker_log]))

                    runtime.details[i - 1] = [str(i), result, time_, memory, checker_log]

                runtime.view.update_with(runtime.details)

        logger.debug('Child thread exited')

    def _check_printf_lld(self, code):
        if code.find('%lld') == -1:
            return
        return_value = sublime.ok_cancel_dialog(
            'Found \"%lld\" in your code.\nAre you sure to submit it anyway?', 'Yes')
        if not return_value:
            raise ExitScript()

    def _parse_problem_id(self, pid):
        match = self.codeforces_pid_regex.search(pid)
        logger.debug('Parse problem ID: {} => {}'.format(pid, match.groups()))
        return match.groups()

    def _get_csrf_token(self):
        html, resp = self.get(self.empty_url, self.headers)
        token = self.csrf_token_regex.findall(html)[0]
        logger.debug('CSRF token: {}'.format(token))
        return token

    def _get_websocket_token(self, html):
        cc_token = self.cc_token_regex.findall(html)[0]
        pc_token = self.pc_token_regex.findall(html)[0]
        logger.debug('cc: {}, pc: {}'.format(cc_token, pc_token))
        return cc_token, pc_token
