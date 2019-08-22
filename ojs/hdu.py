# -*- coding: utf-8 -*-

import urllib.parse
import html.parser as parser
import time
import re

from ..libs import logging as log
from ..libs import middleware
from . import OjModule, abort_when_false


lang_map = {
	'C++': 0, # G++
	'C': 1, # GCC
	'Pascal': 4, # Pascal
	'Java': 5, # Java
	'C#': 6 # C#
}


class HduModule(OjModule):
	name = 'hdu'
	display_name = 'HDU'
	result_header = ['Result', 'Time', 'Memory']
	support_languages = [ 'C++', 'C', 'Java', 'Pascal', 'C#' ]

	root_url = 'http://acm.hdu.edu.cn'
	login_url = root_url + '/userloginex.php?action=login'
	submit_url = root_url + '/submit.php?action=submit'
	result_url = root_url + '/status.php?{}'
	compile_message_url = root_url + '/viewerror.php?rid={}'

	result_regex_r = r'<tr (bgcolor=#D7EBFF )?align=center ><td height=22px>(\d+)</td><td>([0-9\-: ]+)</td><td>(<a (.*) target=_blank>)?<font color=(#?[0-9a-zA-Z]+)>([0-9a-zA-Z<>()_ ]+)</font>(</a>)?</td><td><a href="/showproblem\.php\?pid={pid}">{pid}</a></td><td>(\d+)MS</td><td>(\d+)K</td><td><a href="/viewcode\.php\?rid=(\d+)"  ?target=_blank>(\d+) B</td><td>([A-Za-z\+#]+)</td><td class=fixedsize><a href="/userstatus\.php\?user={username}">{username}</a></td></tr>'
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
		return html.find('<img alt="Author" src="/images/user.png" border=0 height=18 width=18> {}'.format(self.username)) != -1

	def login(self):
		self.opener, _ = self.create_opener()

		values = {
			'username': self.username,
			'userpass': self.password,
			'login': 'Sign In'
		}

		html, resp = self.post(self.login_url, values, self.headers)
		login_status = self.check_login()
		if login_status:
			message = 'Login to HDU OK'
		else:
			message = 'Login to HDU fail'
		self.set_status(message)
		log.info(message)
		return login_status

	@abort_when_false
	def submit(self, runtime):
		language = lang_map[runtime.language]
		code = middleware.freopen_filter(runtime.code)

		values  = {
			'action': 'submit',
			'check': '0',
			'problemid': str(runtime.pid),
			'language': language,
			'usercode': code
		}
		html, resp = self.post(self.submit_url, values, self.headers)
		if resp.url.find('status.php') == -1:
			if resp.url.find('userloginex.php') != -1:
				message = 'Submit Fail: Invalid login'
			else:
				message = 'Submit Fail'
			self.set_status(message)
			log.warning(message)
			return False
		else:
			self.set_status('Submit OK, fetching result...')
			log.info('Submit OK')

	def load_result(self, runtime):
		values = {
			'first': '',
			'pid': str(runtime.pid),
			'user': self.username,
			'lang': '0',
			'status': '0'
		}
		url = self.result_url.format(urllib.parse.urlencode(values))
		result_regex = re.compile(self.result_regex_r.format(pid=runtime.pid, username=self.username), flags=re.DOTALL)

		while True:
			self.set_status('Waiting for judging...')
			time.sleep(1)

			html, resp = self.get(url, self.headers)
			match = result_regex.search(html)

			result = match.group(7)
			if result not in ['Compiling', 'Running', 'Queuing']:
				break

		message = 'Loading result...'
		self.set_status(message)
		log.debug(message)

		result = result.replace('<br>', ' ')
		judge_id = match.group(2)
		time_ = match.group(9) + ' ms'
		memory = match.group(10) + ' KB'
		detail = [ result, time_, memory ]

		if result == 'Compilation Error':
			result = 'Compile Error'
			html, resp = self.get(self.compile_message_url.format(judge_id), self.headers)
			runtime.judge_compile_message = parser.HTMLParser().unescape(self.compile_message_regex.findall(html)[0]).replace('\r', '')

		runtime.judge_detail = [ detail ]
		runtime.judge_result = result
		runtime.judge_score = 100 if result == 'Accepted' else 0
