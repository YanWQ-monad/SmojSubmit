# -*- coding: utf-8 -*-

from functools import reduce
import sublime_plugin
import sublime

from . import figlet


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
			self.view.run_command('smoj_add_line_readonly', {'line': line})

	def is_open(self):
		return not self.closed


def pretty_format(head, detail):
	cols = len(head)
	lens = [[ len(head[i]) for i in range(0, cols) ]] \
			+ [ [ len(item[i]) for i in range(0, cols) ] for item in detail ]
	max_len = reduce(lambda x, y: [ max(x[i], y[i]) for i in range(0, cols) ], lens)

	head = [ head[i].center(max_len[i]) for i in range(0, cols) ]
	for item in detail:
		item[0] = item[0].center(max_len[0])
		item[1] = item[1].rjust (max_len[1])
		item[2] = item[2].rjust (max_len[2])
		item[3] = item[3].rjust (max_len[3])

	return head, detail


def print_result(head, detail, main, score, cpl_info, pid):
	head, detail = pretty_format(head, detail)
	tot_len = len('  '.join(head)) + 2

	view = SmojResultView('Result')
	view.create_view()
	view.add_line('Problem ID : {}'.format(str(pid)))
	view.add_line(figlet.get_figlet(main))
	if cpl_info:
		view.add_line('Compile INFO:')
		view.add_line(compile.replace('\r', '\n'))
	view.add_line('Result        -> {} <-'.format(score))
	view.add_line('-' * (tot_len + len(head) + 1))
	view.add_line('| ' + ' | '.join(head) + ' |')
	view.add_line('|' + '-' * (tot_len + len(head) - 1) + '|')
	for row in detail:
		view.add_line('| ' + ' | '.join(row) + ' |')
	view.add_line('-' * (tot_len + len(head) + 1))
