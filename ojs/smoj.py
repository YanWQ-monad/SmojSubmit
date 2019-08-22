# -*- coding: utf-8 -*-

import json
import time
import re

from ..libs import logging as log
from ..libs import middleware
from . import OjModule, abort_when_false


result_link = {
	'Accept': 'Accepted',
	'Wrong_Answer': 'Wrong Answer',
	'compile_error': 'Compile Error',
	'monitor_time_limit_exceeded9(超时)': 'Time Limit Exceeded',
	'monitor_segment_error(段错误,爆内存或爆栈?)': 'Runtime Error',
	'monitor_file_name_error(你的文件名出错了?)': 'File Name Error',
	'monitor_memory_limit_exceeded': 'Memory Limit Exceeded',
	'monitor_SIGFPE_error(算术运算错误,除数是0?浮点运算出错？溢出？)': 'SIGFPE Error',
	'monitor_time_limit_exceeded14(超时,没用文件操作或者你的程序崩溃)': 'Output Limit Exceeded'
	# monitor_invalid_syscall_id: Restrict Function
	# 测评机出错--无法清空沙箱或者无法复制文件.in到沙箱: No Data
}


class SmojModule(OjModule):
	name = 'smoj'
	display_name = 'SMOJ'
	result_header = ['Result', 'Score', 'Time', 'Memory']
	support_languages = [ 'C++' ]

	root_url = 'http://smoj.nhedu.net'
	login_url = root_url + '/login'
	post_url = root_url + '/submit_problem?pid={}'
	result_url = root_url + '/allmysubmits'
	detail_url = root_url + '/showresult'

	status_regex = re.compile(r'<td><a href="showproblem\?id=\d{4,}">\d{4,}</a></td>\s*<td>([a-zA-Z ]*)</td>')
	meta_regex = re.compile(r'<td><a href="#" id="result"><input type="hidden" value="(.*)"><input type="hidden" value="\d{4,}"><input type="hidden" id="submitTime" value="(\d+)">((\d+)/(\d+)|点击查看)</a></td>')

	def init(self, config):
		self.username = config['username']
		self.password = config['password']
		self.headers = config['headers']
		if config.get('init_login', False):
			self.login()

	def login(self):
		self.set_status('Logging in to SMOJ...')
		self.opener, _ = self.create_opener()

		values = {
			'redirect_to': '',
			'username': self.username,
			'password': self.password
		}

		html, resp = self.post(self.login_url, values, self.headers)
		if len(html) < 100:
			message = 'Login to SMOJ fail: {}'.format(info)
		else:
			message = 'Login to SMOJ OK'
		self.set_status(message)
		log.error(message)
		return len(html) >= 100  # same as the if condition

	def check_login(self):
		if self.opener is None:
			return False
		html, resp = self.get(self.root_url, self.headers)
		return resp.url.find('/login') == -1

	@abort_when_false
	def submit(self, runtime):
		assert runtime.language in ['C++', 'C']
		code = middleware.freopen_filter(runtime.code, runtime.pid)

		values = {
			'pid': str(runtime.pid),
			'language': '.cpp',
			'code': code
		}

		html, resp = self.post(self.post_url.format(runtime.pid), values, self.headers)
		if resp.url.find('allmysubmits') == -1:
			if html.startswith('<html>'):
				message = 'Submit failed. Redirected to {}'.format(resp.url)
			else:
				message = 'Submit failed: {}'.format(html)
			self.set_status(message)
			log.error(message)
			return False
		else:
			self.set_status('Submit OK, fetching result...')
			log.info('Submit OK')

	@abort_when_false
	def load_result(self, runtime):
		timestamp = None
		while True:
			time.sleep(1)
			self.set_status('Waiting for judging...')
			html, resp = self.get(self.result_url, self.headers)
			if timestamp is None:
				match = self.meta_regex.search(html)
				timestamp = match.group(2)
			if self.status_regex.search(html).group(1) == 'done':
				match = self.meta_regex.search(html)
				runtime.judge_score = match.group(3)
				break

		self.set_status('Loading result...')
		values = {
			'submitTime': timestamp,
			'pid': runtime.pid,
			'user': self.username
		}
		html, resp = self.post(self.detail_url, values, self.headers)
		result = json.loads(html)

		if result['result'] == 'OI_MODE':
			self.set_status('This is an OI-MODE problem')
			return False

		runtime.judge_compile_message = \
			result['compileInfo'][0] if len(result['compileInfo']) else None

		data = result['result'].replace('\n', '')
		detail = []
		for testcase in data.split(';')[:-1]:
			groups = testcase.split(':')
			detail.append([
				self._get_status_name(groups[0]),
				groups[1],
				groups[2].replace('不可用', 'NaN') + ' ms',
				groups[3].replace('不可用', 'NaN') + ' KB'
			])

		runtime.judge_result = \
			([item[0] for item in detail if item[0] != 'Accepted'] + ['Accepted'])[0]
		runtime.judge_detail = detail

	def _get_status_name(self, status: str):
		if status[:3] == 'goc':
			status = status[3:]
		try:
			if status[:26] == 'monitor_invalid_syscall_id':
				return 'Restrict Function'
			if status[:21] == '测评机出错--无法清空沙箱或者无法复制文件':
				return 'No Data'
			return result_link[status]
		except KeyError:
			return status
