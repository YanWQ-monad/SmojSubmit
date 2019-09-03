# -*- coding: utf-8 -*-

from functools import reduce
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

    def add_line(self, content, line=None):
        if content[-1:] != '\n':
            content = content + '\n'
        if self.is_open():
            self.view.run_command('smoj_add_line_readonly', {'content': content, 'line': line})

    def is_open(self):
        return not self.closed


def pretty_format(head, detail):
    cols = len(head)
    lens = [[len(head[i]) for i in range(0, cols)]] \
        + [[len(item[i]) for i in range(0, cols)] for item in detail]
    max_len = reduce(lambda x, y: [max(x[i], y[i]) for i in range(0, cols)], lens)

    head = [head[i].center(max_len[i]) for i in range(0, cols)]
    for item in detail:
        for i in range(0, len(item)):
            if head[i].strip(' ') in ['Time', 'Memory', 'Score']:
                item[i] = item[i].rjust(max_len[i])
            else:
                item[i] = item[i].center(max_len[i])

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
        view.add_line(cpl_info.replace('\r', '\n'))
    view.add_line('Result        -> {} <-'.format(score))
    view.add_line('-' * (tot_len + len(head) + 1))
    view.add_line('| ' + ' | '.join(head) + ' |')
    view.add_line('|' + '-' * (tot_len + len(head) - 1) + '|')
    for row in detail:
        view.add_line('| ' + ' | '.join(row) + ' |')
    view.add_line('-' * (tot_len + len(head) + 1))
