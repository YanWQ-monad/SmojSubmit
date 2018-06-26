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
		log.debug('Init {}'.format(self.__class__.__name__))
		timer.Timer(1, self.delay_init)

	def delay_init(self):
		pass


def oj_call(name, method_name, *args, **kw):
	oj = importlib.import_module('..ojs.' + name, __package__)
	try:
		func = getattr(oj, method_name)
		log.debug('Calling \'{}\' {}()'.format(name, method_name))
		tm.call_func_thread(func, *args, **kw)
	except AttributeError:
		log.debug('\'{}\' doesn\'t have such a method: {}'.format(name, method_name))
