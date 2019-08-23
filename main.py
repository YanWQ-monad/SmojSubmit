# -*- coding: utf-8 -*-

from .libs import logging as _logging
_logging.init_logging()


import sublime_plugin
import logging
import sublime

from .libs import thread_manager as tm
from .libs import config
from .libs import loader
from .libs import code
from .libs.exception import InvalidInput
from . import ojs


logger = logging.getLogger(__name__)
PLUGIN_NAME = 'SmojSubmit'


class SmojAddLineReadonly(sublime_plugin.TextCommand):
	def run(self, edit, content, line=None):
		self.view.set_read_only(False)
		if line is None:
			self.view.insert(edit, self.view.size(), content)
		else:
			self.view.insert(edit, self.view.text_point(line - 1, 0), content)
		self.view.set_read_only(True)


class SmojReplaceLineReadonly(sublime_plugin.TextCommand):
	def run(self, edit, line, content):
		self.view.set_read_only(False)
		region = self.view.line(self.view.text_point(line - 1, 0))
		self.view.replace(edit, region, content)
		self.view.set_read_only(True)



class SmojSubmitCommand(loader.MonadApplicationLoader):
	latest_value = None

	def __init__(self):
		loader.MonadApplicationLoader.__init__(self)
		self.cfg = config.Config()
		self.login = False
		self.oj_list = []
		ojs.load_ojs()

	def delay_init(self):
		self.cfg.load_config(PLUGIN_NAME)
		setting = self.cfg.get_settings()

		tm.set_config(setting.get('thread_config'))
		ojs.activate()

		SmojSubmitCommand.latest_value = setting.get('default_oj')
		if SmojSubmitCommand.latest_value:
			logger.info('Set default oj => {}'.format(SmojSubmitCommand.latest_value))

		logger.warning('Plugin loaded')

	# def reload_settings(self):
	# 	new_setting = sublime.load_settings(PLUGIN_NAME + '.sublime-settings')
	# 	for (new, old) in zip(self.setting.get('oj'), new_setting.get('oj')):
	# 		if dict(new) != dict(old) and new.get(name) == old.get('name'):
	# 			thread = loader.oj_call(new.get('name'), new, 'reload_config')
	# 			tm.add_thread(thread)
	# 	new_setting.add_on_change(PLUGIN_NAME, self.reload_settings)
	# 	self.setting = new_setting

	def run(self, **kw):
		oj_name = kw['oj']

		if kw['type'] == 'submit':
			try:
				lang = code.get_lang()
				pid = code.get_pid()
				text = code.get_text()
			except InvalidInput as e:
				logger.error(e.message)
				sublime.status_message(e.message)
				sublime.error_message(e.message)
				return
			logger.debug('Submit to {} {} with {}'.format(oj_name, pid, lang))
			tm.call_func_thread(ojs.submit, oj_name, pid, text, lang)

		SmojSubmitCommand.latest_value = oj_name


class SmojSubmitLatestCommand(sublime_plugin.ApplicationCommand):
	def is_enabled(self):
		return (SmojSubmitCommand.latest_value is not None)

	def run(self, **kw):
		kw['oj'] = SmojSubmitCommand.latest_value
		sublime.run_command('smoj_submit', kw)
