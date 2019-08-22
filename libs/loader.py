# -*- coding: utf-8 -*-

import sublime_plugin
import importlib
import threading
import logging
import sublime

from . import timer as timer
from . import thread_manager as tm


logger = logging.getLogger(__name__)


class MonadApplicationLoader(sublime_plugin.ApplicationCommand):
	def __init__(self):
		sublime_plugin.ApplicationCommand.__init__(self)
		logger.debug('Init {}'.format(self.__class__.__name__))
		timer.Timer(1, self.delay_init)

	def delay_init(self):
		pass
