# -*- coding: utf-8 -*-

import logging
import sublime


logger = logging.getLogger(__name__)


class ConfigSingleton(type):
	_instances = {}
	def __call__(cls, name):
		if name not in cls._instances:
			cls._instances[name] = super(ConfigSingleton, cls).__call__(name)
		return cls._instances[name]


class Config(metaclass=ConfigSingleton):
	def __init__(self, name):
		self.name = name + '.sublime-settings'
		self.init = False
		self.settings = None
		self.on_reload = []

	def load_config(self):
		if self.init:
			return
		logger.info('Load config "{}"'.format(self.name))
		self.settings = sublime.load_settings(self.name)
		self.init = True

	def add_on_change(self, key, func):
		self.load_config()
		self.settings.add_on_change(key, func)

	def get(self, key, default=None):
		self.load_config()
		node = self.settings
		keys = key.split('.')
		for key in keys:
			node = node.get(key)
			if node is None:
				break
		return node if node is not None else default

	def set(self, key, value):
		self.load_config()
		keys = key.split('.')
		root_key = keys[0]

		if len(keys) == 1:
			obj = value
		else:
			obj = self.settings.get(root_key) or {}

			node = obj
			for key in keys[1:-1]:
				if node.get(key) is None:
					node[key] = {}
				node = node[key]
			node[keys[-1]] = value

		self.settings.set(root_key, obj)

		sublime.save_settings(self.name)
