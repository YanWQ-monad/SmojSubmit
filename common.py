# -*- coding: utf-8 -*-

import sublime_plugin
import importlib
import sublime

class SmojSubmitInsertHelperCommand(sublime_plugin.TextCommand):
    def run(self, edit, st):
        self.view.insert(edit, self.view.size(), st)

headers ={'User-Agent': r'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.75 Safari/537.36'}

figlet_link = {
'Accepted': 'Accept',
'Wrong Answer': 'Wrong',
'Compile Error': 'CE',
'Time Limit Exceeded': 'TLE',
'Runtime Error': 'RE',
'File Name Error': 'FNE',
'Memory Limit Exceeded': 'MLE',
'SIGFPE Error': 'SE',
'Output Limit Exceeded': 'OLE',
'Restrict Function': 'RF'
}

def getFiglet(key):
	try:
		figlet = importlib.import_module('.figlet.'+figlet_link[key], __package__)
		return figlet.figlet
	except:
		return ''
