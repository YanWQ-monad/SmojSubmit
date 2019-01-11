# -*- coding: utf-8 -*-

import sublime_plugin
import sublime
import re

from . import logging as log


syntax_regex = re.compile(r'/([^/]*)\.sublime-syntax')


suffix_map = {
	'Pascal': '.pas',
	'C': '.c',
	'C++': '.cpp',
	'Python': '.py',
	'Java': '.java',
	'JavaScript': '.js',
	'Ruby': '.rb',
	'Go': '.go',
	'Rust': '.rs',
	'PHP': '.php',
	'C#': '.cs',
	'Haskell': '.hs',
	'Kotlin': '.kt',
	'Scala': '.sc',
	'Perl': '.pl',
}


def get_text():
	view = sublime.active_window().active_view()
	text = view.substr(sublime.Region(0, view.size()))
	return text


def get_pid():
	suffix = suffix_map.get(get_lang(), '.cpp')
	regex = '// ?([\\w\\d]+)\\{}'.format(suffix)
	view = sublime.active_window().active_view()
	chunk = view.find_all(regex, 0)
	if len(chunk) != 1:
		log.warning           ('Not found pid or found multiple pids')
		sublime.status_message('Not found pid or found multiple pids')
		sublime. error_message('Not found pid or found multiple pids')
		return None
	match_str = view.substr(sublime.Region(chunk[0].a, chunk[0].b))
	pid = re.search(regex, match_str).group(1)
	return pid


def get_lang():
	view = sublime.active_window().active_view()
	syntax = view.settings().get('syntax')
	lang = syntax_regex.search(syntax).group(1)
	return lang
