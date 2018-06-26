# -*- coding: utf-8 -*-

import sublime_plugin

PLUGIN_NAME = 'SmojSubmit'
headers ={
	'User-Agent': r'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.75 Safari/537.36',
	'Accept': r'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
}

class SmojAddLineReadonly(sublime_plugin.TextCommand):
	def run(self, edit, line):
		self.view.set_read_only(False)
		self.view.insert(edit, self.view.size(), line)
		self.view.set_read_only(True)
