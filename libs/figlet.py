# -*- coding: utf-8 -*-

import importlib


figlet_link = {
	'Accepted':              'AC',
	'Wrong Answer':          'WA',
	'Compile Error':         'CE',
	'Time Limit Exceeded':   'TLE',
	'Runtime Error':         'RE',
	'File Name Error':       'FNE',
	'Memory Limit Exceeded': 'MLE',
	'SIGFPE Error':          'SE',
	'Output Limit Exceeded': 'OLE',
	'Restrict Function':     'RF',
	'Presentation Error':    'PE'
}


def get_figlet(key):
	try:
		figlet = importlib.import_module('..figlets.' + figlet_link[key], __package__)
		return figlet.figlet
	except KeyError:
		return ''
