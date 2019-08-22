# -*- coding: utf-8 -*-

import sublime_plugin
import importlib
import threading
import sublime

from . import logging as log
from . import timer as timer
from . import thread_manager as tm


class MonadApplicationLoader(sublime_plugin.ApplicationCommand):
	def __init__(self):
		sublime_plugin.ApplicationCommand.__init__(self)
		log.trace('Init {}'.format(self.__class__.__name__))
		timer.Timer(1, self.delay_init)

	def delay_init(self):
		pass
