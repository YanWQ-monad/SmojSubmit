# -*- coding: utf-8 -*-

import sublime_plugin
import sublime

class SmojAddLine(sublime_plugin.TextCommand):
	def run(self, edit, line):
		self.view.set_read_only(False)
		self.view.insert(edit, self.view.size(), line)
		self.view.set_read_only(True)

class SmojResultView:
	def __init__(self, name):
		self.name = name
		self.closed = True
		self.view = None

	def create_view(self):
		self.view = sublime.active_window().new_file()
		self.view.set_name(self.name)
		self.view.set_scratch(True)
		self.view.set_read_only(True)
		self.closed = False

	def add_line(self, line):
		if line[-1:] != '\n':
			line = line + '\n'
		if self.is_open():
			self.view.run_command('smoj_add_line', {'line': line})

	def is_open(self):
		return not self.closed
