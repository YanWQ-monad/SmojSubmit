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
from ..main import headers


username = None
password = None
opener = None

root_url = 'http://acm.hdu.edu.cn'
sign_url = root_url + '/userloginex.php?action=login'
post_url = root_url + '/submit.php?action=submit'
rest_url = root_url + '/status.php'
cmpl_url = root_url + '/viewerror.php?rid={}'

_cpl_re = re.compile(r'<pre>(.*)</pre>', flags=re.DOTALL)
_res_re = r'<tr (bgcolor=#D7EBFF )?align=center ><td height=22px>(\d+)</td><td>([0-9\-: ]+)</td><td>(<a (.*) target=_blank>)?<font color=(#?[0-9a-zA-Z]+)>([0-9a-zA-Z<>()_ ]+)</font>(</a>)?</td><td><a href="/showproblem\.php\?pid={}">{}</a></td><td>(\d+)MS</td><td>(\d+)K</td><td><a href="/viewcode\.php\?rid=(\d+)"  ?target=_blank>(\d+) B</td><td>([A-Za-z\+#]+)</td><td class=fixedsize><a href="/userstatus\.php\?user={}">{}</a></td></tr>'

lang_map = {
	'C++': 0, # G++
	'C': 1, # GCC
	'Pascal': 4, # Pascal
	'Java': 5, # Java
	'C#': 6 # C#
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
	if text.find('<img alt="Author" src="/images/user.png" border=0 height=18 width=18> {}'.format(username)) == -1:
		return True


def login(username, password):
	global opener
	cookie  = http.cookiejar.CookieJar()
	handler = urllib.request.HTTPCookieProcessor(cookie)
	opener  = urllib.request.build_opener(handler)

	values  = {
		'username': username,
		'userpass': password,
		'login': 'Sign In'
	}

	r = urllib.request.Request(url=sign_url, data=urllib.parse.urlencode(values).encode(), headers=headers)
	resp = opener.open(r)
	if check_login(resp):
		sublime.status_message('Login to HDU fail')
		log.error('Login to HDU fail')
		return False
	else:
		sublime.status_message('Login to HDU OK')
		log.info('Login to HDU: OK')
		return True


def submit(pid, code, lang):
	if check_login():
		sublime.status_message('Logging in to HDU...')
		if not login(username, password):
			log.error('Submit fail: Cannot log in')
			return None
	lang = lang_map[lang]
	code = middleware.freopen_filter(code)

	sublime.status_message('Submitting code to HDU...')
	log.debug             ('Submitting code to HDU...')

	values  = {
		'action': 'submit',
		'check': '0',
		'problemid': str(pid),
		'language': lang,
		'usercode': code
	}
	r = urllib.request.Request(url=post_url, data=urllib.parse.urlencode(values).encode(), headers=headers)
	resp = opener.open(r)
	if resp.url.find('status.php') == -1:
		if resp.url.find('userloginex.php') != -1:
			sublime.status_message('Submit Fail: Invalid login')
			log.warning('Submit Fail: Invalid login')
		else:
			sublime.status_message('Submit Fail')
			log.warning('Submit Fail')
	else:
		sublime.status_message('Submit OK, fetching result...')
		log.info('Submit OK')

	fetch_result(username, pid)


def load_result(username, pid):
	values = {
		'first': '',
		'pid': str(pid),
		'user': username,
		'lang': '0',
		'status': '0'
	}
	url = rest_url + '?' + urllib.parse.urlencode(values)

	while True:
		sublime.status_message('Waiting for judging...')
		time.sleep(1)

		r = urllib.request.Request(url=url, headers=headers)
		resp = opener.open(r)
		text = resp.read().decode()
		match = re.search(_res_re.format(pid, pid, username, username), text, flags=re.DOTALL)

		main = match.group(7)
		if main not in  ['Compiling', 'Running', 'Queuing']:
			break

	sublime.status_message('Loading result...')
	log.debug             ('Loading result...')

	jid = match.group(2)
	_time = match.group(9) + ' ms'
	memory = match.group(10) + ' KB'
	cpl_info = None

	if main == 'Compilation Error':
		main = 'Compile Error'
		r = urllib.request.Request(url=cmpl_url.format(jid), headers=headers)
		resp = opener.open(r)
		text = resp.read().decode()
		cpl_info = html.parser.HTMLParser().unescape(_cpl_re.findall(text)[0]).replace('\r', '')
		
	main = main.replace('<br>', ' ')
	detail = [ main, _time, memory ]

	return main, cpl_info, detail


def fetch_result(username, pid):
	head = ['Result', 'Time', 'Memory']
	main, cpl_info, detail = load_result(username, pid)
	figlet = 'Runtime Error' if main.startswith('Runtime Error') else main
	printer.print_result(head, [ detail ], figlet, main, cpl_info, pid)
