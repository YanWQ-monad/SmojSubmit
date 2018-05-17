# -*- coding: utf-8 -*-

import sublime_plugin
import sublime
import re

from .SMOJ import login, result, post, config
from .plug import timer
from . import common
from . import log

_cpp_re = re.compile(r'// ?(\d{4})\.cpp')
_fre_re = re.compile(r'freopen\("([^.])+\.(in|out)"( ?), "(r|w)", std(in|out)( ?)\);')
_cm1_re = re.compile(r'/\*(\s*)((freopen(.*,.*,.*)\s*){1,2})\s*\*/')
_cm2_re = re.compile(r'(\s*)//(\s*)(freopen\("([^.])+\.(in|out)"( ?), "(r|w)", std(in|out)( ?)\);)')

settings = None
config_callback = None

class SmojSubmitCommand(sublime_plugin.ApplicationCommand):
    def __init__(self):
        sublime_plugin.ApplicationCommand.__init__(self)
        log.info('Delay to load')
        self.Login = False
        timer.Timer(3, self.configs)

    def configs(self):
        setting = sublime.load_settings('SmojSubmit.sublime-settings')
        if not setting.get('smoj').get('enable'):
            return None
        setting.add_on_change(common.PLUGIN_NAME, self.reload_settings)
        setting  = setting.get('smoj')
        username = setting.get('username')
        password = setting.get('password')
        self.login(username, password)
        log.info('SMOJ plugin loaded')
        self.setting = setting

    def legalFileName(self, name):
        if name is None:
            return False
        if len(name) < 4:
            return False
        if name[-4:] in ('.cpp'):
            return True
        return False

    def is_enabled(self):
        return self.Login

    def reload_settings(self):
        log.info('Reloading settings...')
        setting = sublime.load_settings(common.PLUGIN_NAME + '.sublime-settings')
        setting.clear_on_change(common.PLUGIN_NAME)
        if not setting.get('smoj').get('enable'):
            return None
        setting.add_on_change(common.PLUGIN_NAME, self.reload_settings)
        setting  = setting.get('smoj')
        username = setting.get('username')
        password = setting.get('password')
        self.relogin(username, password)
        self.setting = setting

    def setOpener(self, opener):
        self.opener = opener

    def setLoginFlag(self, flag):
        self.Login = flag

    def post(self, cpp, problem, view):
        result_thread = result.ResultThreading(self.opener, view)
    #    result_thread.start()
        thread = post.PostThreading(self.opener, cpp, problem, result_thread.start)
        thread.start()

    def relogin(self, username, password):
        thread = login.LoginThreading(username, password, self.setOpener, self.setLoginFlag, True , self.opener)
        thread.start()

    def login(self, username, password):
        self.Login = False
        thread = login.LoginThreading(username, password, self.setOpener, self.setLoginFlag, False)
        thread.start()

    def getProblemNum(self, view):
        chunk = view.find_all(r'// ?(\d{4})\.cpp', 0)
        if len(chunk) < 1:
            log.warning           ('Not found problem number')
            sublime.status_message('Not found problem number')
            sublime. error_message('Not found problem number')
            return None
        chunk = chunk[0]
        cpp_name = view.substr(sublime.Region(chunk.a, chunk.b))
        m = _cpp_re.search(cpp_name)
        cpp_num  = m.group(1)
        return int(cpp_num)

    def getContent(self, view):
        return view.substr(sublime.Region(0, view.size()))

    def fillFreopen(self, content, problem):
        result = content
        result = re.sub(_fre_re, r'freopen("%d.\2"\3, "\4", std\5\6);' % problem, result)
        result = re.sub(_cm1_re, r'\1\2'                                        , result)
        result = re.sub(_cm2_re, r'\1\2\3'                                      , result)
        return result

    def run(self, **kw):
        if kw['type'] == 'login':
            username = self.setting.get('username')
            password = self.setting.get('password')
            self.relogin(username, password)
        elif kw['type'] == 'submit':
            view = sublime.active_window().active_view()
            problem = self.getProblemNum(view)
            if not problem:
                return None
            content = self.getContent(view)
            content = self.fillFreopen(content, problem)
            self.post(content, problem, view)
