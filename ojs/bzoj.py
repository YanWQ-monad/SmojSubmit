# -*- coding: utf-8 -*-

import http.cookiejar
import urllib.request
import urllib.parse
import html.parser
import sublime
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

root_url = 'https://www.lydsy.com/JudgeOnline'
sign_url = root_url + '/login.php'
post_url = root_url + '/submit.php'
rest_url = root_url + '/status.php'
cmpl_url = root_url + '/ceinfo.php?sid={}'

_res_re = r"<tr align=center class='(even|odd)row'><td>(\d+)<td><a href='userinfo\.php\?user={name}'>{name}</a><td><a href='problem\.php\?id={pid}'>{pid}</a><td>(<a href='ceinfo\.php\?sid=\d+'>)?<font color=#?[0-9a-zA-Z]+>([a-zA-Z_&]+)</font>(</a>)?<td>((\d+) <font color=red>kb</font>|------)<td>((\d+) <font color=red>ms</font>|------)<td><a target=_blank href=showsource\.php\?id=\d+>[a-zA-Z+]+</a>/<a target=_self href=.submitpage\.php\?id={pid}&sid=\d+.>Edit</a><td>\d+ B<td>[0-9\- :]+</tr>"
_dtl_re = r"<tr align=center class='(even|odd)row'><td>(\d+)<td><a href='userinfo\.php\?user={name}'>{name}</a><td><a href='problem\.php\?id={pid}'>{pid}</a><td>(<a href='ceinfo\.php\?sid=\d+'>)?<font color=#?[0-9a-zA-Z]+>([a-zA-Z_&]+)</font>(</a>)?<td>(\d+) <font color=red>kb</font><td>(\d+) <font color=red>ms</font><td><a target=_blank href=showsource\.php\?id=\d+>[a-zA-Z+]+</a>/<a target=_self href=.submitpage\.php\?id={pid}&sid=\d+.>Edit</a><td>\d+ B<td>[0-9\- :]+</tr>"
_cpl_re = re.compile(r'<pre>(.*)</pre>', flags=re.DOTALL)

lang_map = {
	'C': 0,
	'C++': 1,
	'Pascal': 2,
	'Java': 3,
	'Python': 6
}


def init(config):
	global username
	global password
	username = config['username']
	password = config['password']
	if config.get('init_login', False):
		login(username, password)


def check_login():
	if opener is None:
		return True
	r = urllib.request.Request(url=root_url, headers=headers)
	resp = opener.open(r)
	text = resp.read().decode()
	if text.find('<font color=red>{}</font>'.format(username)) == -1:
		return True


def login(username, password):
	global opener
	cookie  = http.cookiejar.CookieJar()
	handler = urllib.request.HTTPCookieProcessor(cookie)
	opener  = urllib.request.build_opener(handler)

	values  = {
		'user_id': username,
		'password': password,
		'submit': 'Submit'
	}

	r = urllib.request.Request(url=sign_url, data=urllib.parse.urlencode(values).encode(), headers=headers)
	resp = opener.open(r)
	if check_login():
		sublime.status_message('Login to BZOJ fail')
		log.error('Login to BZOJ fail')
		return False
	else:
		sublime.status_message('Login to BZOJ OK')
		log.info('Login to BZOJ: OK')
		return True


def submit(pid, code, lang):
	if check_login():
		sublime.status_message('Logging in to BZOJ...')
		if not login(username, password):
			log.error('Submit fail: Cannot log in')
			return None
	lang = lang_map[lang]
	code = middleware.freopen_filter(code)

	sublime.status_message('Submitting code to BZOJ...')
	log.debug             ('Submitting code to BZOJ...')

	values  = {
		'id': str(pid),
		'language': lang,
		'source': code
	}
	r = urllib.request.Request(url=post_url, data=urllib.parse.urlencode(values).encode(), headers=headers)
	resp = opener.open(r)
	if resp.url.find('status.php') == -1:
		if check_login():
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


def load_result(username, pid):
	values = {
		'problem_id': str(pid),
		'user_id': username,
		'language': '-1',
		'jresult': '-1'
	}
	url = rest_url + '?' + urllib.parse.urlencode(values)

	c_res_re = re.compile(_res_re.format(pid=pid, name=username))

	while True:
		sublime.status_message('Waiting for judging...')
		time.sleep(1)

		r = urllib.request.Request(url=url, headers=headers)
		resp = opener.open(r)
		text = resp.read().decode()
		match = c_res_re.search(text)

		main = match.group(4)
		if main not in  ['Pending', 'Pending_Rejudging', 'Compiling', 'Running_&_Judging']:
			break

	match = re.search(_dtl_re.format(pid=pid, name=username), text)

	sublime.status_message('Loading result...')
	log.debug             ('Loading result...')

	jid = match.group(2)
	memory = match.group(6) + ' KB'
	_time = match.group(7) + ' ms'
	cpl_info = None

	main = main.replace('_', ' ')
	if main == 'Compile Error':
		r = urllib.request.Request(url=cmpl_url.format(jid), headers=headers)
		resp = opener.open(r)
		text = resp.read().decode()
		cpl_info = html.parser.HTMLParser().unescape(_cpl_re.findall(text)[0]).replace('\r', '')
		
	if main.endswith('Exceed'):
		main = main + 'ed'

	detail = [ main, _time, memory ]

	return main, cpl_info, detail


def fetch_result(username, pid):
	head = ['Result', 'Time', 'Memory']
	main, cpl_info, detail = load_result(username, pid)
	printer.print_result(head, [ detail ], main, main, cpl_info, pid)


cfg = config.Config()
headers = cfg.get_settings().get('headers')
