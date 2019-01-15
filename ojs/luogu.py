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
captcha_url = root_url + '/download/captcha'
login_url = root_url + '/login/loginpage'
show_problem_url = root_url + '/problemnew/show/'
show_record_url = root_url + '/recordnew/show/'
submit_api_url = root_url + '/api/problem/submit/'
submit_page_url = root_url + '/problem/ajax_submit'
twoFA_url = root_url + '/login/send_unlock_email'
unlock_url = root_url + '/login/unlock'

o2_flag = '// luogu-judger-enable-o2\n'

capt_re = re.compile(r'<meta name="csrf-token" content="(\d+:[\w=/+]+)">')
testcase_re = re.compile(r'<small>#(\d+)</small>')

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
	handler = urllib.request.HTTPCookieProcessor(cookie)
	opener = urllib.request.build_opener(handler)
	username = config['username']
	password = config['password']
	if config.get('init_login', False):
		login(username, password)


def get_csrf_token(html=None):
	if html is None:
		r = urllib.request.Request(url=root_url, headers=headers)
		resp = opener.open(r)
		html = resp.read().decode()
	return capt_re.findall(html)[0]


def captcha_input():
	r = urllib.request.Request(url=captcha_url, headers=headers)
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
	code = None
	init_msg = 'send_unlock_email'
	while True:
		def got_input(text=''):
			nonlocal code
			code = text
		sublime.active_window().show_input_panel('[{}] Enter 2FA code'.format(PLUGIN_NAME), init_msg, got_input, None, got_input)
		while code is None:
			time.sleep(0.1)
		if code == 'send_unlock_email':
			headers2 = merge_dict(headers, {'Referer': unlock_url, 'X-CSRF-Token': get_csrf_token()})
			r = urllib.request.Request(url=twoFA_url, headers=headers2, method='POST')
			data = json.loads(opener.open(r).read().decode())
			if data.code != 200:
				log.error('Send unlock email failed: {}'.format(data.message))
			else:
				init_msg = 'Send email successful'
			continue
		payload = {'csrf-token': get_csrf_token(), 'code': code}
		payload = urllib.parse.urlencode(payload).encode()
		r = urllib.request.Request(url=unlock_url, headers=merge_dict(headers, dict(Referer=unlock_url)), data=payload)
		resp = opener.open(r)
		if resp.geturl() == unlock_url:
			init_msg = '2FA code is not correct'
			continue
		break


def login():
	payload = {
		'username': username,
		'password': password,
		'cookie': '3',
		'redirect': '',
		'verify': captcha_input()
	}
	payload = urllib.parse.urlencode(payload).encode()
	headers2 = merge_dict(headers, {
		'Referer': login_url,
		'X-CSRF-Token': get_csrf_token()
	})

	r = urllib.request.Request(url=login_url, data=payload, headers=headers2)
	resp = opener.open(r)
	data = json.loads(resp.read().decode())
	if data['code'] != 200:
		log.error('Login to Luogu failed: {}'.format(data['message']))
		return False

	r = urllib.request.Request(url=root_url, headers=merge_dict(headers, dict(Referer=login_url)))
	resp = opener.open(r)
	if resp.geturl() == unlock_url:
		unlock_by_2FA()

	return True


def submit(pid, code, lang):
	r = urllib.request.Request(url=submit_page_url+'?pid={}'.format(pid), headers=merge_dict(headers, dict(Referer=show_problem_url + pid)))
	resp = opener.open(r)
	data = json.loads(resp.read().decode())
	if data['code'] == 0:
		if not login():
			return None
	elif data['code'] != 201:
		log.error('Failed to submit: {}'.format(data['message']))
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
		'Referer': show_problem_url + pid,
		'X-CSRF-Token': get_csrf_token()
	})

	r = urllib.request.Request(url=submit_api_url + pid, data=payload, headers=headers2)
	resp = opener.open(r)
	data = json.loads(resp.read().decode())
	if data['status'] != 200:
		log.error('Failed to submit: {}'.format(data.get('message', '-')))
		return None

	fetch_result(str(data['data']['rid']), pid)


def fetch_result(rid, pid):
	r = urllib.request.Request(url=show_record_url + rid, headers=merge_dict(headers, dict(Referer=show_problem_url + pid)))
	html = opener.open(r).read().decode()
	testcases = len(testcase_re.findall(html))

	cookies = ';'.join(['{}={}'.format(item.name, item.value) for item in cookie])
	ws = websocket.create_connection(websocket_url, sslopt={'cert_reqs': ssl.CERT_NONE}, cookie=cookies)
	join_data = dict(type='join_channel', channel='record.track', channel_param=rid)
	ws.send(json.dumps(join_data, separators=(',', ':')))

	view = LuoguResultView('Result')
	view.create_view()

	view.add_line('Problem ID : {}'.format(pid))
	view.add_line(figlet.get_figlet('Pending'))

	head = ['Result', 'Time', 'Memory', 'Score', 'Description']
	detail = [['Pending', '', '', '', ''] for _ in range(testcases)]
	started = False

	view.add_detail(*printer.pretty_format(head, copy.deepcopy(detail)))

	while True:
		msg = json.loads(ws.recv())
		log.trace('{}'.format(msg))
		if msg['type'] == 'status_push':
			for (key, value) in msg['detail'].items():
				if not key.startswith('case'):
					continue
				index = int(key[4:]) - 1
				if detail[index][1] != '':
					continue
				detail[index] = [
					result_map.get(value['flag'], str(value['flag'])),
					str(value['time']) + 'ms',
					str(value['memory']) + 'KB',
					str(value['score']),
					value['desc'].replace('\n', ' ') if value['desc'] else ''
				]

			if view.compile_msg_height == 0 and len(msg['detail']['compile']['content']):
				view.set_compile_msg(msg['detail']['compile']['content'])
			if not started:
				view.replace_figlet('Waiting')
				for row in detail:
					row[0] = 'Waiting'
			if msg['status'] != 1:
				if msg['status'] == 2:
					for row in detail:
						row[0] = 'Compile Error'
						row[3] = '0'
				view.replace_figlet(result_map[msg['status']])
			started = True

			view.update_detail(*printer.pretty_format(head, copy.deepcopy(detail)))
		elif msg['type'] == 'flush':
			break
	ws.close()


cfg = config.Config()
headers = merge_dict(cfg.get_settings().get('headers'), dict(Origin=root_url))
