# -*- coding: utf-8 -*-

import functools
import http.cookiejar
import importlib
import json
import logging
import os
import sublime
import urllib.request

from ..libs import config
from ..libs import printer


logger = logging.getLogger(__name__)
ojs = {}


class ModuleRegister(type):
	def __new__(cls, name, bases, attrs):
		newclass = super(cls, ModuleRegister).__new__(cls, name, bases, attrs)
		if name != 'OjModule':
			logger.info('new class registered: {} (class {})'
				.format(attrs['display_name'], name))
			ojs[attrs['name']] = newclass()
		return newclass


class OjModule(metaclass=ModuleRegister):
	# name: str
	# display_name: str
	# result_header: list
	# support_languages: list
	post_type = 'urlencoded'  # str

	class RuntimeVariable:
		# pid: str
		# code: str
		# language: str
		# judge_detail: list
		# judge_result: str
		# judge_score: int
		# judge_compile_message: str

		def __init__(self, pid: str, code: str, language: str):
			self.pid = pid
			self.code = code
			self.language = language
			self.judge_detail = None
			self.judge_result = None
			self.judge_score = None
			self.judge_compile_message = None

		def __str__(self):
			return json.dumps({
				prop: value for prop, value in vars(self).items()
					if not prop.startswith('__') })

		__repr__ = __str__


	def __init__(self):
		self.opener = None

	def set_status(self, message: str):
		sublime.status_message(message)

	def create_opener(self):
		cookie = http.cookiejar.CookieJar()
		handler = urllib.request.HTTPCookieProcessor(cookie)
		opener = urllib.request.build_opener(handler)
		return opener, cookie

	def get(self, url, headers, decode=True):
		logger.debug('GET {}'.format(url))
		req = urllib.request.Request(url=url, headers=headers)
		resp = self.opener.open(req)
		html = resp.read()

		if decode:
			try:
				html = html.decode('utf-8')
			except UnicodeDecodeError:
				html = html.decode('gbk')

		return html, resp

	def post(self, url, data, headers, post_type=None):
		logger.debug('POST {} with data {}'.format(url, data))
		post_type = post_type or self.post_type

		if isinstance(data, dict):
			if post_type == 'urlencoded':
				data = urllib.parse.urlencode(data).encode()
			elif post_type == 'json':
				headers['Content-Type'] = 'application/json'
				data = json.dumps(data).encode()
		elif isinstance(data, str):
			data = data.encode()

		req = urllib.request.Request(url=url, data=data, headers=headers)
		resp = None
		try:
			resp = self.opener.open(req)
		except urllib.error.HTTPError as e:
			resp = e
		html = resp.read()

		try:
			html = html.decode('utf-8')
		except UnicodeDecodeError:
			html = html.decode('gbk')

		return html, resp

	def init(self, config: dict):
		raise NotImplementedError

	def check_login(self):
		raise NotImplementedError

	def login(self):
		raise NotImplementedError

	def submit(self, runtime: RuntimeVariable):
		raise NotImplementedError

	def load_result(self, runtime: RuntimeVariable):
		raise NotImplementedError

	def work(self, pid, code, language):
		if language not in self.support_languages:
			message = 'Unsupported Language: {}'.format(language)
			logger.error(message)
			self.set_status(message)
			sublime.error_message(message)
			return False

		logger.debug('checking login status')
		login_status = self.check_login()
		logger.debug('checked login status: {}'.format(login_status))

		if not login_status:
			logger.debug('call self.login()')
			if not self.login():
				return False

		runtime = self.RuntimeVariable(pid, code, language)
		logger.debug('Initialized runtime variable: {}'.format(runtime))

		logger.debug('call self.submit(runtime)')
		self.set_status('Submitting code to {}...'.format(self.display_name))
		self.submit(runtime)
		logger.debug('end self.submit(runtime)')

		logger.debug('Runtime variable: {}'.format(runtime))

		logger.debug('call self.load_result(runtime)')
		self.load_result(runtime)
		logger.debug('end self.load_result(runtime)')

		logger.debug('Runtime variable: {}'.format(runtime))
		logger.debug('call print_result()')
		printer.print_result(
			self.result_header,
			runtime.judge_detail,
			runtime.judge_result,
			runtime.judge_score,
			runtime.judge_compile_message,
			runtime.pid)


def abort_when_false(func):
	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		return_value = func(*args, **kwargs)
		if return_value == False:
			raise Exception('Abort when return False')
	return wrapper


def activate():
	cfg = config.Config()
	headers = cfg.get_settings().get('headers')
	ojs_config = cfg.get_settings().get('oj')
	for name, oj in ojs.items():
		if name not in ojs_config:
			logger.warning('no config for {}, skip'.format(oj.display_name))
		oj_config = ojs_config[name]
		oj_config['headers'] = headers
		logger.debug('activate {} with config {}'.format(oj.display_name, oj_config))
		oj.init(oj_config)


def load_ojs():
	ojs_path = os.path.dirname(os.path.abspath(__file__))
	for file in os.listdir(ojs_path)[::-1]:
		if not file.startswith('__') and file.endswith('.py'):
			logger.debug('import {}'.format(file))
			importlib.import_module('.' + file[:-3], __package__)


def submit(oj_name, pid, code, language):
	if oj_name not in ojs:
		sublime.status_message('No such oj: {}'.format(oj_name))
		return
	oj = ojs[oj_name]
	oj.work(pid, code, language)
