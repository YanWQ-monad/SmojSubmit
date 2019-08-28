# -*- coding: utf-8 -*-

import http.cookiejar
import urllib.parse
import websocket
import tempfile
import logging
import sublime
import copy
import time
import json
import ssl
import os
import re

from ..main import PLUGIN_NAME
from ..libs import printer
from ..libs import figlet
from ..libs import config as gconfig
from ..libs.exception import LoginFail, SubmitFail, ExitScript
from . import OjModule


logger = logging.getLogger(__name__)
lang_map = {
	'Auto': 0,
	'Pascal': 1,
	'C': 2,
	'C++': 3,
	'C++11': 4,
	'C++14': 11,
	'C++17': 12,
	'Python2': 6,
	'Python3': 7,
	'PyPy2': 24,
	'PyPy3': 25,
	'Java8': 8,
	'Node.js': 9,
	'Ruby': 13,
	'Go': 14,
	'Rust': 15,
	'PHP7': 16,
	'C#Mono': 17,
	'VisualBasicMono': 18,
	'Haskell': 19,
	'KotlinNative': 20,
	'KotlinJVM': 21,
	'Scala': 22,
	'Perl': 23,
	# Redirect:
	'Python': 7,
	'Java': 8,
	'JavaScript': 9,
	'PHP': 16,
	'C#': 17
}

result_map = {
	0: 'Waiting',
	1: 'Judging',
	2: 'Compile Error',
	3: 'Output Limit Exceeded',
	4: 'Memory Limit Exceeded',
	5: 'Time Limit Exceeded',
	6: 'Wrong Answer',
	7: 'Runtime Error',
	12: 'Accepted',
	14: 'Unaccepted'
}


class LuoguResultView(printer.SmojResultView):
	def __init__(self, name):
		printer.SmojResultView.__init__(self, name)
		self.compile_msg_height = 0

	def update_line(self, content, line):
		if self.view.substr(self.view.line(self.view.text_point(line - 1, 0))) != content:
			self.view.run_command('smoj_replace_line_readonly', {'line': line, 'content': content})

	def set_compile_msg(self, content):
		self.compile_msg_height = len(content.split('\n'))
		self.add_line('Compile information:', 8)
		self.add_line(content, 9)

	def replace_figlet(self, main):
		lines = figlet.get_figlet(main).rstrip('\n').split('\n')
		for i, line in enumerate(lines):
			self.update_line(line, i + 2)

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


def merge_dict(x, y):
	z = x.copy()
	z.update(y)
	return z


class LuoguModule(OjModule):
	name = 'luogu'
	display_name = 'Luogu'
	post_type = 'json'
	support_languages = [ 'C++', 'C', 'Java', 'Pascal', 'Python', 'JavaScript', 'Ruby', 'Go', 'Rust', 'PHP', 'C#', 'Haskell', 'Kotlin', 'Scala', 'Perl' ]

	root_url = 'https://www.luogu.org'
	websocket_url = 'wss://ws.luogu.org/ws'
	captcha_url = root_url + '/api/verify/captcha?_t={:.4f}'
	empty_url = root_url + '/404'
	login_page = root_url + '/auth/login'
	login_url = root_url + '/api/auth/userPassLogin'
	record_api_url = root_url + '/record/{}?_contentOnly=1'
	show_problem_url = root_url + '/problem/{}'
	submit_api_url = root_url + '/api/problem/submit/{}'
	unlock_page = root_url + '/auth/unlock'
	unlock_url = root_url + '/api/auth/unlock'

	o2_flag = '// luogu-judger-enable-o2\n'

	csrf_regex = re.compile(r'<meta name="csrf-token" content="(\d+:[a-zA-Z0-9/+]+=)">')
	feinjection_regex = re.compile(r'window\._feInjection = JSON.parse\(decodeURIComponent\("([-a-zA-Z0-9()@:%_\+.~#?&\/=]+)"\)\);')

	class RuntimeVariable(OjModule.RuntimeVariable):
		# pid: str
		# code: str
		# language: str
		# judge_id: str

		def __init__(self, pid: str, code: str, language: str):
			self.pid = pid
			self.code = code
			self.language = language
			self.judge_id = None

	def init(self, config):
		self.config = gconfig.Config('SmojSubmit')

		self.opener, self.cookie = self.create_opener()
		client_id = self.config.get('oj.luogu.client_id', '')
		uid = self.config.get('oj.luogu.uid', '')
		expires = str(int(time.time()) + 2592000)
		self.cookie.set_cookie(http.cookiejar.Cookie(0, '__client_id', client_id, None, False, '.luogu.org', True, False, '/', True, True, expires, False, None, None, None))
		self.cookie.set_cookie(http.cookiejar.Cookie(0, '_uid', uid, None, False, '.luogu.org', True, False, '/', True, True, expires, False, None, None, None))

		self.headers = merge_dict(config['headers'], dict(Origin=self.root_url))
		self.username = config['username']
		self.password = config['password']
		if config.get('init_login', False):
			self.login()

	def check_login(self):
		if self.opener is None:
			return False
		injection = self._get_feinjection()
		return 'currentUser' in injection and injection['currentUser'] is not None

	def login(self):
		payload = {
			'username': self.username,
			'password': self.password,
			'captcha': self._get_captcha()
		}
		data, resp = self.post(self.login_url, payload, self.login_page)
		data = json.loads(data)
		logger.debug('Login response: {}'.format(data))

		if 'status' in data:
			raise LoginFail(data['errorMessage'])

		if data['locked']:
			logger.info('Two-Factor Auth required')
			self._unlock_with_2FA()

		cookie_dict = {item.name: item.value for item in self.cookie}
		self.config.set('oj.luogu.client_id', cookie_dict['__client_id'])
		self.config.set('oj.luogu.uid', cookie_dict['_uid'])
		logger.debug('save cookie: uid={} client_id={}'.format(cookie_dict['_uid'], cookie_dict['__client_id']))

	def submit(self, runtime):
		code = runtime.code
		o2 = code.startswith(self.o2_flag)
		if o2:
			code = code[len(self.o2_flag):]

		payload = {
			'lang': lang_map.get(runtime.language, 0),
			'code': code,
			'enableO2': int(o2),
			'verify': ''
		}
		data, resp = self.post(
			self.submit_api_url.format(runtime.pid),
			payload,
			self.show_problem_url.format(runtime.pid),
			post_type='urlencoded')
		data = json.loads(data)

		if data['status'] != 200:
			raise SubmitFail(data.get('errorMessage', '-'))

		runtime.judge_id = str(data['data']['rid'])

	def load_result(self, runtime):
		data, resp = self.get(self.record_api_url.format(runtime.judge_id), merge_dict(self.headers, dict(Referer=self.show_problem_url.format(runtime.pid))))
		data = json.loads(data)
		testcases_group = data['currentData']['testCaseGroup']
		if isinstance(testcases_group, dict):
			testcases_group = testcases_group.values()
		testcases_count = max([max(testcases) for testcases in testcases_group])

		cookies = ';'.join(['{}={}'.format(item.name, item.value) for item in self.cookie])
		ws = websocket.create_connection(
			self.websocket_url, sslopt={'cert_reqs': ssl.CERT_NONE}, cookie=cookies)
		join_data = dict(type='join_channel', channel='record.track', channel_param=runtime.judge_id)
		ws.send(json.dumps(join_data, separators=(',', ':')))

		view = LuoguResultView('Result')
		view.create_view()

		view.add_line('Problem ID : {}'.format(runtime.pid))
		view.add_line(figlet.get_figlet('Pending'))

		header = ['Result', 'Time', 'Memory', 'Score', 'Description']
		detail = [['Pending', '', '', '', ''] for _ in range(testcases_count)]
		started = False

		view.add_detail(*printer.pretty_format(header, copy.deepcopy(detail)))

		while True:
			msg = json.loads(ws.recv())
			logger.debug('websocket receive {}'.format(msg))
			if msg['type'] == 'status_push':
				record = msg['record']
				if 'testcases' in record['detail']:
					for index, testcase in record['detail']['testcases'].items():
						index = int(index) - 1
						if detail[index][1] != '':
							continue
						detail[index] = [
							result_map.get(testcase['status'], str(testcase['status'])),
							str(testcase['time']) + 'ms',
							str(testcase['memory']) + 'KB',
							str(testcase['score']),
							testcase['message'].replace('\n', ' ') if testcase['message'] else ''
						]

				if view.compile_msg_height == 0 and len(record.get('detail', {}).get('compile', {}).get('content', '')):
					view.set_compile_msg(record['detail']['compile']['content'])

				if not started:
					view.replace_figlet('Waiting')
					for row in detail:
						row[0] = 'Waiting'
				started = True

				if record['status'] != 1:
					if record['status'] == 2:
						for row in detail:
							row[0] = 'Compile Error'
							row[3] = '0'
					view.replace_figlet(result_map[record['status']])

				view.update_detail(*printer.pretty_format(header, copy.deepcopy(detail)))
			elif msg['type'] == 'flush':
				break

		leave_data = dict(type='disconnect_channel', channel='record.track', channel_param=runtime.judge_id)
		ws.send(json.dumps(leave_data, separators=(',', ':')))
		ws.close()

		raise ExitScript()

	def post(self, url, data, referer, **kwargs):
		headers = self.headers.copy()
		headers['X-CSRF-Token'] = self._get_xsrf_token()
		headers['Referer'] = referer
		return super(LuoguModule, self).post(url, data, headers, **kwargs)

	def _get_captcha(self):
		url = self.captcha_url.format(time.time() * 1000)
		data, resp = self.get(url, self.headers, decode=False)

		file = tempfile.NamedTemporaryFile('wb', suffix='.png', delete=False)
		file.write(data)
		file.close()

		window = sublime.active_window()
		view = window.open_file(file.name)
		view.set_scratch(True)

		cap = None
		def got_input(text=''):
			nonlocal cap
			cap = text
			window.focus_view(view)
			window.run_command('close_file')
			os.remove(file.name)
		window.show_input_panel('[{}] Enter the captcha text'.format(PLUGIN_NAME), '', got_input, None, got_input)

		while cap is None:
			time.sleep(0.1)
		return cap

	def _get_feinjection(self):
		html, resp = self.get(self.empty_url, self.headers)
		uri = self.feinjection_regex.findall(html)[0]
		injection = json.loads(urllib.parse.unquote(uri))
		logger.debug('feInjection = {}'.format(injection))
		return injection

	def _get_xsrf_token(self):
		html, resp = self.get(self.empty_url, self.headers)
		return self.csrf_regex.findall(html)[0]

	def _unlock_with_2FA(self):
		initial_msg = ''
		while True:
			code = None
			cancal = False
			def got_input(text):
				nonlocal code
				code = text
			def on_cancal():
				nonlocal cancal
				cancal = True
			sublime.active_window().show_input_panel('[{}] Enter 2FA code'.format(PLUGIN_NAME), initial_msg, got_input, None, on_cancal)

			while code is None and cancal == False:
				time.sleep(0.1)
			if cancal:
				raise ExitScript()

			payload = {'code': code}
			data, resp = self.post(self.unlock_url, payload, self.unlock_page)
			data = json.loads(data)
			if 'status' not in data:
				break
			initial_msg = '2FA code is not correct'
