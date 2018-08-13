# -*- coding: utf-8 -*-

import http.cookiejar
import urllib.request
import urllib.parse
import html.parser
import sublime
import base64
import time
import re

from ..libs import logging as log
from ..libs import middleware
from ..libs import printer
from ..libs import config


username = None
password = None
opener = None
headers = None

root_url = 'http://poj.org'
sign_url = root_url + '/login'
post_url = root_url + '/submit'
rest_url = root_url + '/status'

_res_re = re.compile(r'<tr align=center><td>(.*)</td></tr>')
_cpl_re = re.compile(r'<pre>(.*)</pre>', flags=re.DOTALL)
reduce_1 = re.compile(r'<a href=showsource\?solution_id=(\d+) target=_blank>')
reduce_2 = re.compile(r'<font color=([a-zA-Z]+)>')
reduce_3 = re.compile(r'<a href=(.*) target=_blank>')

lang_map = {
	'C++': 0, # G++
	'C': 1, # GCC
	'Java': 2, # Java
	'Pascal': 3 # Pascal
}


def init(config):
	global username
	global password
	username = config['username']
	password = config['password']
	if config.get('init_login', False):
		login(username, password)


def check_login(resp=None):
	if opener is None:
		return True
	if resp is None:
		r = urllib.request.Request(url=root_url, headers=headers)
		resp = opener.open(r)
	text = resp.read().decode()
	if text.find('<b>{}</b>'.format(username)) == -1:
		return True


def login(username, password):
	global opener
	cookie  = http.cookiejar.CookieJar()
	handler = urllib.request.HTTPCookieProcessor(cookie)
	opener  = urllib.request.build_opener(handler)

	values  = {
		'user_id1': username,
		'password1': password,
		'B1': 'login',
		'url': '/'
	}

	r = urllib.request.Request(url=sign_url, data=urllib.parse.urlencode(values).encode(), headers=headers)
	resp = opener.open(r)
	if check_login(resp):
		sublime.status_message('Login to POJ fail')
		log.error('Login to POJ fail')
		return False
	else:
		sublime.status_message('Login to POJ OK')
		log.info('Login to POJ: OK')
		return True


def submit(pid, code, lang):
	if check_login():
		sublime.status_message('Logging in to POJ...')
		if not login(username, password):
			log.error('Submit fail: Cannot log in')
			return None
	lang = lang_map[lang]
	code = middleware.freopen_filter(code)
	code = base64.b64encode(code.encode()).decode()

	sublime.status_message('Submitting code to POJ...')
	log.debug             ('Submitting code to POJ...')

	values  = {
		'problem_id': str(pid),
		'language': lang,
		'source': code,
		'submit': 'submit',
		'encoded': '1'
	}
	r = urllib.request.Request(url=(post_url.format(pid)), data=urllib.parse.urlencode(values).encode(), headers=headers)
	resp = opener.open(r)
	text = resp.read().decode()
	if resp.url.find('status') == -1:
		if text.find('Please login first.') != -1:
			sublime.status_message('Submit Fail: Invalid login')
			log.warning('Submit Fail: Invalid login')
		else:
			sublime.status_message('Submit Fail')
			log.warning('Submit Fail')
		return False
	else:
		sublime.status_message('Submit OK, fetching result...')
		log.info('Submit OK')

	fetch_result(username, pid)


def reduce_html(text, pid):
	text = text.replace('<a href=userstatus?user_id={}>'.format(username), '')
	text = text.replace('<a href=problem?id={}>'.format(pid), '')
	text = text.replace('</font>', '')
	text = text.replace('</a>', '')
	text = re.sub(reduce_1, '', text)
	text = re.sub(reduce_2, '', text)
	text = re.sub(reduce_3, '', text)

	return text


def load_result(username, pid):
	values = {
		'problem_id': str(pid),
		'user_id': username,
		'result': '',
		'language': ''
	}
	url = rest_url + '?' + urllib.parse.urlencode(values)

	while True:
		sublime.status_message('Waiting for judging...')
		time.sleep(1)

		r = urllib.request.Request(url=url, headers=headers)
		resp = opener.open(r)
		text = resp.read().decode()
		text = reduce_html(text, pid)

		row = _res_re.findall(text)[0].split('</td><td>')

		main = row[3]
		if main not in  ['Compiling', 'Judging', 'Waiting', 'Queuing', 'Running & Judging']:
			break

	sublime.status_message('Loading result...')
	log.debug             ('Loading result...')

	jid = row[0]
	memory = row[4]
	_time = row[5]
	cpl_info = None

	if main == 'Compile Error':
		r = urllib.request.Request(url=root_url + '/showcompileinfo?solution_id={}'.format(jid), headers=headers)
		resp = opener.open(r)
		text = resp.read().decode()
		cpl_info = html.parser.HTMLParser().unescape(_cpl_re.findall(text)[0])
	detail = [ main, _time, memory ]

	return main, cpl_info, detail


def fetch_result(username, pid):
	head = ['Result', 'Time', 'Memory']
	main, cpl_info, detail = load_result(username, pid)
	printer.print_result(head, [ detail ], main, main, cpl_info, pid)


cfg = config.Config()
headers = cfg.get_settings().get('headers')
