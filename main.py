# -*- coding: utf-8 -*-

import sublime_plugin
import sublime

from .libs import thread_manager as tm
from .libs import logging as log
from .libs import loader
from .libs import code
from . import common


latest = None


class SmojSubmitCommand(loader.MonadApplicationLoader):
	def __init__(self):
		# raise Exception
		loader.MonadApplicationLoader.__init__(self)
		self.login = False
		self.oj_list = []
		self.oj_config = {}

	def delay_init(self):
		log.info('{} Loaded'.format(common.PLUGIN_NAME))
		setting = sublime.load_settings(common.PLUGIN_NAME + '.sublime-settings')
		tm.set_config(setting.get('thread_config'))
		for oj in setting.get('oj'):
			if oj.get('enable') is None or oj.get('enable'):
				loader.oj_call(oj.get('name'), 'init', oj)
				self.oj_list.append(oj.get('name'))
				self.oj_config[oj.get('name')] = oj
		# setting.add_on_change(common.PLUGIN_NAME, self.reload_settings)
		self.setting = setting

	# def reload_settings(self):
	# 	new_setting = sublime.load_settings(common.PLUGIN_NAME + '.sublime-settings')
	# 	for (new, old) in zip(self.setting.get('oj'), new_setting.get('oj')):
	# 		if dict(new) != dict(old) and new.get(name) == old.get('name'):
	# 			thread = loader.oj_call(new.get('name'), new, 'reload_config')
	# 			tm.add_thread(thread)
	# 	new_setting.add_on_change(common.PLUGIN_NAME, self.reload_settings)
	# 	self.setting = new_setting

	def run(self, **kw):
		global latest
		oj_name = kw['oj']
		if oj_name not in self.oj_list:
			log.error('Unknown OJ: {}'.format(oj_name))
			sublime.status_message('Unknown OJ: {}'.format(oj_name))
			return None
		latest = oj_name

		if kw['type'] == 'submit':
			pid  = code.get_pid()
			text = code.get_text()
			lang = code.get_lang()
			if lang not in self.oj_config[oj_name]['lang']:
				log.error('Unsupported Language: {}'.format(lang))
				sublime.status_message('Unsupported Language: {}'.format(lang))
				return None
			loader.oj_call(oj_name, 'submit', pid, text, lang)


class SmojSubmitLatestCommand(sublime_plugin.ApplicationCommand):
	def is_enabled(self):
		return (latest is not None)

	def run(self, **kw):
		kw['oj'] = latest
		sublime.run_command('smoj_submit', kw)
