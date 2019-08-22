# -*- coding: utf-8 -*-

import threading
import logging
import queue
import time


logger = logging.getLogger(__name__)
pool = queue.Queue()
active = []
max_active_thread_count = 3 # It can be overridden in 'sublime-setting'
lock = threading.Lock()
event = threading.Event()


class ThreadLoop(threading.Thread):
	def run(self):
		while True:
			event.wait()
			with lock:
				event.clear()
			for thread in active:
				if not thread.is_alive():
					active.remove(thread)
			while len(active) < max_active_thread_count and not pool.empty():
				top = pool.get()
				top.start()
				active.append(top)


class ManagedThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)

	def run(self):
		self.exec()
		on_thread_done()


class FunctionNewThread(ManagedThread):
	def __init__(self, func, *args, **kw):
		ManagedThread.__init__(self)
		self.func = func
		self.args = args
		self.kw = kw

	def exec(self):
		func = self.func
		try:
			func(*self.args, **self.kw)
		except Exception as e:
			logger.exception('Exception in child thread: {}'.format(str(e)))


def set_config(config):
	if config is None:
		return
	global max_active_thread_count
	max_active_thread_count = config.get('max_active_thread_count', 3)


def add_thread(thread):
	logger.debug('Push a thread')
	pool.put(thread)
	with lock:
		event.set()


def on_thread_done():
	with lock:
		event.set()


def call_func_thread(func, *args, **kw):
	thread = FunctionNewThread(func, *args, **kw)
	add_thread(thread)


loop = ThreadLoop()
loop.start()
