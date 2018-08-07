# -*- coding: utf-8 -*-

import sublime_plugin
import sublime


PLUGIN_NAME = 'SmojSubmit'
headers ={
	'User-Agent': r'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.75 Safari/537.36',
	'Accept': r'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
}


from .libs import thread_manager as tm
from .libs import logging as log
from .libs import loader
from .libs import code

latest = None

class SmojAddLineReadonly(sublime_plugin.TextCommand):
	def run(self, edit, line):
		self.view.set_read_only(False)
		self.view.insert(edit, self.view.size(), line)
		self.view.set_read_only(True)


class SmojSubmitCommand(loader.MonadApplicationLoader):
	def __init__(self):
		# raise Exception
		loader.MonadApplicationLoader.__init__(self)
		self.login = False
		self.oj_list = []
		self.oj_config = {}

	def delay_init(self):
		log.info('{} Loaded'.format(PLUGIN_NAME))
		setting = sublime.load_settings(PLUGIN_NAME + '.sublime-settings')
		tm.set_config(setting.get('thread_config'))
		for (name, oj) in setting.get('oj').items():
			if oj.get('enable') is None or oj.get('enable'):
				loader.oj_call(name, 'init', oj)
				self.oj_list.append(name)
				self.oj_config[name] = dict(oj)
				self.oj_config[name]['name'] = name
		# setting.add_on_change(PLUGIN_NAME, self.reload_settings)
		self.setting = setting

	# def reload_settings(self):
	# 	new_setting = sublime.load_settings(PLUGIN_NAME + '.sublime-settings')
	# 	for (new, old) in zip(self.setting.get('oj'), new_setting.get('oj')):
	# 		if dict(new) != dict(old) and new.get(name) == old.get('name'):
	# 			thread = loader.oj_call(new.get('name'), new, 'reload_config')
	# 			tm.add_thread(thread)
	# 	new_setting.add_on_change(PLUGIN_NAME, self.reload_settings)
	# 	self.setting = new_setting

	def run(self, **kw):
		global latest
		oj_name = kw['oj']
		
		if oj_name not in self.oj_list:
			log.error('Unknown OJ: {}'.format(oj_name))
			sublime.status_message('Unknown OJ: {}'.format(oj_name))
			return None

		if kw['type'] == 'submit':
			lang = code.get_lang()
			if lang not in self.oj_config[oj_name]['lang']:
				log.error('Unsupported Language: {}'.format(lang))
				sublime.status_message('Unsupported Language: {}'.format(lang))
				sublime. error_message('Unsupported Language: {}'.format(lang))
				return None
			pid  = code.get_pid()
			text = code.get_text()
			loader.oj_call(oj_name, 'submit', pid, text, lang)

		latest = oj_name


class SmojSubmitLatestCommand(sublime_plugin.ApplicationCommand):
	def is_enabled(self):
		return (latest is not None)

	def run(self, **kw):
		kw['oj'] = latest
		sublime.run_command('smoj_submit', kw)
