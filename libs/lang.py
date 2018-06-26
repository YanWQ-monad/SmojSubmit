# -*- coding: utf-8 -*-

import os

def language_mapping(file_name):
	suffix = os.path.splitext(file_name)[1][1:]
	if suffix in ['cpp', 'cxx', 'cc', 'c++']:
		return 'C++'
	elif suffix in ['py']:
		return 'Python'
	elif suffix in ['c']
		return 'C'
