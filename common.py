# -*- coding: utf-8 -*-

import sublime_plugin
import sublime

class SmojSubmitInsertHelperCommand(sublime_plugin.TextCommand):
    def run(self, edit, st):
        self.view.insert(edit, self.view.size(), st)

headers ={'User-Agent': r'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.75 Safari/537.36'}
