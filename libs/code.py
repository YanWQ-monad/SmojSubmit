# -*- coding: utf-8 -*-

import logging
import sublime
import re

from .exception import InvalidInput


logger = logging.getLogger(__name__)
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


def get_active_view():
    view = sublime.active_window().active_view()
    if view is None:
        raise InvalidInput('Could not get active view')
    return view


def get_text():
    view = get_active_view()
    text = view.substr(sublime.Region(0, view.size()))
    return text


def get_pid():
    suffix = suffix_map.get(get_lang(), '.cpp')
    regex = '// ?([\\w\\d]+)\\{}'.format(suffix)
    view = get_active_view()
    chunk = view.find_all(regex, 0)
    if len(chunk) != 1:
        raise InvalidInput('Not found pid or found multiple pids')
    match_str = view.substr(sublime.Region(chunk[0].a, chunk[0].b))
    pid = re.search(regex, match_str).group(1)
    return pid


def get_lang():
    view = get_active_view()
    syntax = view.settings().get('syntax')
    lang = syntax_regex.search(syntax).group(1)
    return lang
