# -*- coding: utf-8 -*-

import threading
import traceback
import sys

from . import common

DEBUG = False

g_lock = threading.Lock()

def write_log(level, message):
	s = common.PLUGIN_NAME + ': [' + level + '] ' + message
	with g_lock:
		print(s)

def debug(message):
	if DEBUG:
		write_log('DEBUG', message)

def info(message):
	write_log('INFO', message)

def warning(message):
	write_log('WARNING', message)

def error(message):
	write_log('ERROR', message)

def exception(message):
    exc_type, exc_value, exc_traceback = sys.exc_info()
    exception_message = traceback.format_exception(exc_type, exc_value, exc_traceback)
    write_log('EXCEPTION', message)
    for line in exception_message:
    	write_log('EXCEPTION', line)
