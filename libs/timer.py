# -*- coding: utf-8 -*-

from threading import Thread
import time

class TimerThread(Thread):
	def __init__(self, delay, callback):
		self.delay = delay
		self.callback = callback
		Thread.__init__(self)

	def run(self):
		time.sleep(self.delay)
		self.callback()


class Timer:
	def __init__(self, delay, callback):
		timer = TimerThread(delay, callback)
		timer.start()
