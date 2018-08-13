# -*- coding: utf-8 -*-

import threading


title = ''
g_lock = threading.Lock()
level_map = [ 'trace', 'debug', 'info', 'warning', 'error' ]
global_level = level_map.index('info')


def set_logging_config(name, cfg):
	global title
	global global_level
	title = name
	try:
		global_level = level_map.index(cfg.get('debug'))
	except ValueError:
		error('No such logging level: {}'.format(cfg.get('debug')))


def write_log(level, message):
	if level_map.index(level) >= global_level:
		s = title + ': [' + level.upper() + '] ' + message
		with g_lock:
			print(s)


def trace(message):
	write_log('trace', message)


def debug(message):
	write_log('debug', message)


def info(message):
	write_log('info', message)


def warning(message):
	write_log('warning', message)


def error(message):
	write_log('error', message)
