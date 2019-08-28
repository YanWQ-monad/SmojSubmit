# -*- coding: utf-8 -*-

import sublime_plugin
import importlib
import threading
import logging
import sublime


logger = logging.getLogger(__name__)


class MonadApplicationLoader(sublime_plugin.ApplicationCommand):
	def __init__(self):
		sublime_plugin.ApplicationCommand.__init__(self)
		logger.debug('Init {}'.format(self.__class__.__name__))
		sublime.set_timeout_async(self.delay_init, 1000)

	def delay_init(self):
		pass
