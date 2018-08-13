# -*- coding: utf-8 -*-

import sublime

from . import logging as log


class Singleton(type):
	_instances = {}
	def __call__(cls, *args, **kwargs):
		if cls not in cls._instances:
			cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
		return cls._instances[cls]


class Config(metaclass=Singleton):
	def __init__(self):
		self.init = False

	def load_config(self, name, on_reload=None):
		self.name = name + '.sublime-settings'
		self.on_reload = on_reload
		self.settings = sublime.load_settings(self.name)
		self.add_reload()
		self.init = True

	def add_reload(self):
		keys = [ 'oj', 'thread_config' ]
		for key in keys:
			self.settings.add_on_change(key, self.on_change)

	def on_change(self):
		log.debug('Settings changed')
		self.settings = sublime.load_settings(self.name)
		if self.on_reload:
			self.on_reload(self.settings)

	def get_settings(self):
		assert self.init
		return self.settings
