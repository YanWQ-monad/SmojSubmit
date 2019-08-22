# -*- coding: utf-8 -*-

import urllib.parse
import html.parser as parser
import logging
import base64
import time
import re

from ..libs import middleware
from . import OjModule, abort_when_false


logger = logging.getLogger(__name__)
lang_map = {
	'C++': 0, # G++
	'C': 1, # GCC
	'Java': 2, # Java
	'Pascal': 3 # Pascal
}


class PojModule(OjModule):
	name = 'poj'
	display_name = 'POJ'
	result_header = ['Result', 'Time', 'Memory']
	support_languages = [ 'C++', 'C', 'Java', 'Pascal' ]

	root_url = 'http://poj.org'
	login_url = root_url + '/login'
	submit_url = root_url + '/submit'
	result_url = root_url + '/status?{}'
	compile_message_url = root_url + '/showcompileinfo?solution_id={}'

	result_regex = re.compile(r'<tr align=center><td>(.*)</td></tr>')
	compile_message_regex = re.compile(r'<pre>(.*)</pre>', flags=re.DOTALL)
	reduce_html_1_regex = re.compile(r'<a href=showsource\?solution_id=(\d+) target=_blank>')
	reduce_html_2_regex = re.compile(r'<font color=([a-zA-Z]+)>')
	reduce_html_3_regex = re.compile(r'<a href=(.*) target=_blank>')

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
		return html.find('<b>{}</b>'.format(self.username)) != -1

	def login(self):
		self.opener, _ = self.create_opener()

		values = {
			'user_id1': self.username,
			'password1': self.password,
			'B1': 'login',
			'url': '/'
		}
		html, resp = self.post(self.login_url, values, self.headers)

		login_status = self.check_login()
		if login_status:
			message = 'Login to POJ OK'
			logger.info(message)
		else:
			message = 'Login to POJ fail'
			logger.error(message)
		self.set_status(message)
		return login_status

	@abort_when_false
	def submit(self, runtime):
		language = lang_map[runtime.language]
		code = middleware.freopen_filter(runtime.code)
		code = base64.b64encode(code.encode()).decode()

		values = {
			'problem_id': str(runtime.pid),
			'language': language,
			'source': code,
			'submit': 'submit',
			'encoded': '1'
		}
		html, resp = self.post(self.submit_url.format(runtime.pid), values, self.headers)
		if resp.url.find('status') == -1:
			if html.find('Please login first.') != -1:
				message = 'Submit Fail: Invalid login'
			else:
				message = 'Submit Fail'
			self.set_status(message)
			logger.error(message)
			return False
		else:
			self.set_status('Submit OK, fetching result...')
			logger.info('Submit OK')

	def load_result(self, runtime):
		running_statuses = \
			['Compiling', 'Judging', 'Waiting', 'Queuing', 'Running & Judging']
		values = {
			'problem_id': str(runtime.pid),
			'user_id': self.username,
			'result': '',
			'language': ''
		}
		url = self.result_url.format(urllib.parse.urlencode(values))

		while True:
			self.set_status('Waiting for judging...')
			time.sleep(1)

			html, resp = self.get(url, self.headers)
			html = self._reduce_html(html, runtime.pid)

			row = self.result_regex.findall(html)[0].split('</td><td>')
			result = row[3]
			if result not in running_statuses:
				break

		message = 'Loading result...'
		self.set_status(message)

		judge_id = row[0]
		memory = row[4]
		time_ = row[5]
		detail = [ result, time_, memory ]

		if result == 'Compile Error':
			html, resp = self.get(self.compile_message_url.format(judge_id), self.headers)
			runtime.judge_compile_message = \
				parser.HTMLParser().unescape(self.compile_message_regex.findall(html)[0])

		runtime.judge_detail = [ detail ]
		runtime.judge_result = result
		runtime.judge_score = 100 if result == 'Accepted' else 0

	def _reduce_html(self, html: str, pid: str):
		html = html.replace('<a href=userstatus?user_id={}>'.format(self.username), '')
		html = html.replace('<a href=problem?id={}>'.format(pid), '')
		html = html.replace('</font>', '').replace('</a>', '')
		html = re.sub(self.reduce_html_1_regex, '', html)
		html = re.sub(self.reduce_html_2_regex, '', html)
		html = re.sub(self.reduce_html_3_regex, '', html)
		return html
