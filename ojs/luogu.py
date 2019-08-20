# -*- coding: utf-8 -*-

import http.cookiejar
import urllib.request
import urllib.parse
import websocket
import tempfile
import sublime
import copy
import time
import json
import ssl
import os
import re

from ..libs import logging as log
from ..main import PLUGIN_NAME
from ..libs import middleware
from ..libs import printer
from ..libs import figlet
from ..libs import config


opener = None
username = None
password = None

root_url = 'https://www.luogu.org'
websocket_url = 'wss://ws.luogu.org/ws'
captcha_url = root_url + '/api/verify/captcha?_t={:.4f}'
login_url = root_url + '/api/auth/userPassLogin'
login_page = root_url + '/auth/login'
empty_url = root_url + '/404'
unlock_url = root_url + '/api/auth/unlock'
unlock_page = root_url + '/auth/unlock'
show_problem_url = root_url + '/problem/{}'
record_api_url = root_url + '/record/{}?_contentOnly=1'
submit_api_url = root_url + '/api/problem/submit/{}'

o2_flag = '// luogu-judger-enable-o2\n'

csrf_re = re.compile(r'<meta name="csrf-token" content="(\d+:[\w=/+]+)">')
feInjection_re = re.compile(r'window\._feInjection = JSON.parse\(decodeURIComponent\("([-a-zA-Z0-9()@:%_\+.~#?&\/=]+)"\)\);')

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


def init(config):
	global cookie, username, password, opener

	cookie = http.cookiejar.CookieJar()
	client_id = cfg.get_settings().get('oj').get('luogu').get('client_id', '')
	uid = cfg.get_settings().get('oj').get('luogu').get('uid', '')
	expires = str(int(time.time()) + 2592000)
	cookie.set_cookie(http.cookiejar.Cookie(0, '__client_id', client_id, None, False, '.luogu.org', True, False, '/', True, True, expires, False, None, None, None))
	cookie.set_cookie(http.cookiejar.Cookie(0, '_uid', uid, None, False, '.luogu.org', True, False, '/', True, True, expires, False, None, None, None))

	handler = urllib.request.HTTPCookieProcessor(cookie)
	opener = urllib.request.build_opener(handler)

	username = config['username']
	password = config['password']
	if config.get('init_login', False):
		login(username, password)


def get_csrf_token(html=None):
	if html is None:
		r = urllib.request.Request(url=empty_url, headers=headers)
		resp = opener.open(r)
		html = resp.read().decode()
	return csrf_re.findall(html)[0]


def getFeInjection():
	r = urllib.request.Request(url=empty_url, headers=headers)
	resp = opener.open(r)
	html = resp.read().decode()
	uri = feInjection_re.findall(html)[0]
	jsn = urllib.parse.unquote(uri)
	injection = json.loads(jsn)
	log.trace('feInjection = {}'.format(injection))

	return injection


def captcha_input():
	timestamp = time.time() * 1000
	r = urllib.request.Request(url=captcha_url.format(timestamp), headers=headers)
	resp = opener.open(r)

	file = tempfile.NamedTemporaryFile('wb', suffix='.png', delete=False)
	file.write(resp.read())
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


def unlock_by_2FA():
	init_msg = ''
	while True:
		headers2 = merge_dict(headers, {
			'Referer': unlock_page,
			'X-CSRF-Token': get_csrf_token(),
			'Content-Type': 'application/json'
		})
		code = None
		def got_input(text=''):
			nonlocal code
			code = text
		sublime.active_window().show_input_panel('[{}] Enter 2FA code'.format(PLUGIN_NAME), init_msg, got_input, None, got_input)
		while code is None:
			time.sleep(0.1)
		if len(code) == 0 or code == 'exit':
			return False
		payload = {'code': code}
		payload = json.dumps(payload).encode()
		r = urllib.request.Request(url=unlock_url, headers=headers2, data=payload)
		try:
			resp = opener.open(r)
			break
		except urllib.error.HTTPError as e:
			log.trace('{}'.format(e.read()))
			init_msg = '2FA code is not correct'

	return True


def login():
	payload = {
		'username': username,
		'password': password,
		'captcha': captcha_input()
	}
	log.trace('{}'.format(payload))
	payload = json.dumps(payload).encode()
	headers2 = merge_dict(headers, {
		'Referer': login_page,
		'X-CSRF-Token': get_csrf_token(),
		'Content-Type': 'application/json'
	})
	log.trace('{}'.format(headers2))

	r = urllib.request.Request(url=login_url, data=payload, headers=headers2)
	try:
		resp = opener.open(r)
		data = json.loads(resp.read().decode())
	except urllib.error.HTTPError as e:
		data = json.loads(e.read().decode())
	log.trace('{}'.format(data))
	if 'status' in data:
		log.error('Login to Luogu failed: {}'.format(data['errorMessage']))
		return False

	if data['locked']:
		return unlock_by_2FA()

	cookie_dict = {item.name: item.value for item in cookie}
	copy = cfg.get_settings().get('oj')
	copy['luogu']['client_id'] = cookie_dict['__client_id']
	copy['luogu']['uid'] = cookie_dict['_uid']
	cfg.get_settings().set('oj', copy)
	cfg.save()

	return True


def submit(pid, code, lang):
	injection = getFeInjection()
	if 'currentUser' not in injection:
		if not login():
			return None

	o2 = code.startswith(o2_flag)
	if o2:
		code = code[len(o2_flag):]

	payload = {
		'lang': lang_map.get(lang, 0),
		'code': code,
		'enableO2': int(o2),
		'verify': ''
	}
	payload = urllib.parse.urlencode(payload).encode()
	headers2 = merge_dict(headers, {
		'Referer': show_problem_url.format(pid),
		'X-CSRF-Token': get_csrf_token()
	})

	r = urllib.request.Request(url=submit_api_url.format(pid), data=payload, headers=headers2)
	resp = opener.open(r)
	data = json.loads(resp.read().decode())
	if data['status'] != 200:
		log.error('Failed to submit: {}'.format(data.get('errorMessage', '-')))
		return None

	fetch_result(str(data['data']['rid']), pid)


def fetch_result(rid, pid):
	r = urllib.request.Request(url=record_api_url.format(rid), headers=merge_dict(headers, dict(Referer=show_problem_url.format(pid))))
	data = json.loads(opener.open(r).read().decode())
	testcases_count = 0
	testcases_group = data['currentData']['testCaseGroup']
	if isinstance(testcases_group, dict):
		testcases_group = testcases_group.values()
	for testcases in testcases_group:
		testcases_count = max(testcases_count, max(testcases))

	cookies = ';'.join(['{}={}'.format(item.name, item.value) for item in cookie])
	ws = websocket.create_connection(websocket_url, sslopt={'cert_reqs': ssl.CERT_NONE}, cookie=cookies)
	join_data = dict(type='join_channel', channel='record.track', channel_param=rid)
	ws.send(json.dumps(join_data, separators=(',', ':')))

	view = LuoguResultView('Result')
	view.create_view()

	view.add_line('Problem ID : {}'.format(pid))
	view.add_line(figlet.get_figlet('Pending'))

	head = ['Result', 'Time', 'Memory', 'Score', 'Description']
	detail = [['Pending', '', '', '', ''] for _ in range(testcases_count)]
	started = False

	view.add_detail(*printer.pretty_format(head, copy.deepcopy(detail)))

	while True:
		msg = json.loads(ws.recv())
		log.trace('{}'.format(msg))
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

			view.update_detail(*printer.pretty_format(head, copy.deepcopy(detail)))
		elif msg['type'] == 'flush':
			break

	leave_data = dict(type='disconnect_channel', channel='record.track', channel_param=rid)
	ws.send(json.dumps(leave_data, separators=(',', ':')))
	ws.close()


cfg = config.Config()
headers = merge_dict(cfg.get_settings().get('headers'), dict(Origin=root_url))
