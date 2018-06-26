# -*- coding: utf-8 -*-

import sublime_plugin
import sublime
import re

from . import logging as log


pid_regex    = re.compile(r'// ?(\d+)\.cpp')
syntax_regex = re.compile(r'/([^/]*)\.sublime-syntax')


def get_text():
	view = sublime.active_window().active_view()
	text = view.substr(sublime.Region(0, view.size()))
	return text


def get_pid():
	view = sublime.active_window().active_view()
	chunk = view.find_all(r'// ?(\d+)\.cpp', 0)
	if len(chunk) != 1:
		log.warning           ('Not found pid or found multiple pids')
		sublime.status_message('Not found pid or found multiple pids')
		sublime. error_message('Not found pid or found multiple pids')
		return None
	match_str = view.substr(sublime.Region(chunk[0].a, chunk[0].b))
	pid = pid_regex.search(match_str).group(1)
	return int(pid)


def get_lang():
	view = sublime.active_window().active_view()
	syntax = view.settings().get('syntax')
	lang = syntax_regex.search(syntax).group(1)
	return lang
