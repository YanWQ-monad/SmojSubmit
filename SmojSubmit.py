# -*- coding: utf-8 -*-

import sublime, sublime_plugin
import re, urllib.request, urllib.parse, http.cookiejar, threading, json, time

_cpp_re = re.compile(r'// ?(\d{4})\.cpp')
_fre_re = re.compile(r'freopen\("([^.])+\.(in|out)"( ?), "(r|w)", std(in|out)( ?)\);')
_cm1_re = re.compile(r'/\*(\s*)((freopen(.*,.*,.*)\s*){1,2})\s*\*/')
_cm2_re = re.compile(r'(\s*)//(\s*)(freopen\("([^.])+\.(in|out)"( ?), "(r|w)", std(in|out)( ?)\);)')
_res_re = re.compile(r'<td><a href="#" id="result"><input type="hidden" value="(.*)"><input type="hidden" value="(\d{4,})"><input type="hidden" id="submitTime" value="(\d+)">((\d+)/(\d+)|点击查看)</a></td>')
_isw_re = re.compile(r'<td><a href="showproblem\?id=\d{4,}">\d{4,}</a></td>\s*<td>([a-zA-Z ]*)</td>')

headers ={'User-Agent': r'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.75 Safari/537.36'}
rot_url = 'http://smoj.nhedu.net'
pst_url = 'http://smoj.nhedu.net/submit_problem?pid=%d'
res_url = 'http://smoj.nhedu.net/allmysubmits'
det_url = 'http://smoj.nhedu.net/showresult'

result_link = {
    'Accept': 'Accepted',
    'Wrong_Answer': 'Wrong Answer',
    'compile_error': 'Compile Error',
    'monitor_time_limit_exceeded9(超时)': 'Time Limit Exceeded',
    'monitor_segment_error(段错误,爆内存或爆栈?)': 'Runtime Error',
    'monitor_file_name_error(你的文件名出错了?)': 'File Name Error',
    'monitor_memory_limit_exceeded': 'Memory Limit Exceeded',
    'monitor_SIGFPE_error(算术运算错误,除数是0?浮点运算出错？溢出？)': 'SIGFPE Error',
    'monitor_time_limit_exceeded14(超时,没用文件操作或者你的程序崩溃)': 'Output Limit Exceeded'
    # monitor_invalid_syscall_id 
}

class SmojSubmitInsertHelperCommand(sublime_plugin.TextCommand):
    def run(self, edit, st):
        self.view.insert(edit, self.view.size(), st)

class SmojSubmitCommand(sublime_plugin.TextCommand):
    def __init__(self, view):
        self.Login = False
        if not self.legalFileName(view.file_name()):
            return None
        config = sublime.load_settings('SmojSubmit.sublime-settings')
        username = config.get('username')
        password = config.get('password')
        self.opener = self.login(username, password)
        sublime_plugin.TextCommand.__init__(self, view)

    def legalFileName(self, name):
        if name is None:
            return True
        if len(name) < 4:
            return False
        if name[-4:] in ('.cpp'):
            return True
        return False

    def is_enabled(self):
        return self.Login

    def setOpener(self, opener):
        self.opener = opener

    def setLoginFlag(self, flag):
        self.Login = flag

    def post(self, cpp, problem, edit):
        sublime.status_message('Posting to SMOJ...')
        result_thread = self.ResultThreading(self.opener, self.view)
    #    result_thread.start()
        thread = self.PostThreading(self.opener, cpp, problem, result_thread.start)
        thread.start()

    def login(self, username, password):
        sublime.status_message('Logining to SMOJ...')
        thread = self.LoginThreading(username, password, self.setOpener, self.setLoginFlag)
        thread.start()

    def getProblemNum(self):
        sublime.status_message('Search problem number')
        chunk = self.view.find_all(r'// ?(\d{4})\.cpp', 0)
        if len(chunk) < 1:
            sublime.status_message('Not found problem number')
            sublime. error_message('Not found problem number')
            return None
        chunk = chunk[0]
        cpp_name = self.view.substr(sublime.Region(chunk.a, chunk.b))
        m = _cpp_re.search(cpp_name)
        cpp_num  = m.group(1)
        return int(cpp_num)

    def getContent(self):
        return self.view.substr(sublime.Region(0, self.view.size()))

    def fillFreopen(self, content, problem):
        result = content
        result = re.sub(_fre_re, r'freopen("%d.\2"\3, "\4", std\5\6);' % problem, result)
        result = re.sub(_cm1_re, r'\1\2'                                        , result)
        result = re.sub(_cm2_re, r'\1\2\3'                                      , result)
        return result

    def run(self, edit):
        problem = self.getProblemNum()
        if not problem:
            return None
        content = self.getContent()
        content = self.fillFreopen(content, problem)
        self.post(content, problem, edit)

    class LoginThreading(threading.Thread):
        def __init__(self, username, password, callback_opener, callback_loginf):
            self.username        = username
            self.password        = password
            self.callback_opener = callback_opener
            self.callback_loginf = callback_loginf
            self.result          = None
            threading.Thread.__init__(self)

        def run(self):
            cookie  = http.cookiejar.CookieJar()
            handler = urllib.request.HTTPCookieProcessor(cookie)
            opener  = urllib.request.build_opener(handler)
            values  = {'redirect_to':'', 'username':self.username, 'password':self.password}
            r = urllib.request.Request(url=rot_url+'/login', data=urllib.parse.urlencode(values).encode(), headers=headers)
            response = opener.open(r)
            if response.read().decode().find('石中信息学奥赛勇夺全省三连冠') != -1:
                self.callback_opener(opener)
                self.callback_loginf(True)
                self.result = True
                sublime.status_message('Login OK')
            else:
                self.callback_loginf(False)
                sublime.status_message('Login fail')

    class PostThreading(threading.Thread):
        def __init__(self, opener, cpp, problem, callback):
            self.opener   = opener
            self.cpp      = cpp
            self.problem  = problem
            self.callback = callback
            self.result   = None
            threading.Thread.__init__(self)

        def run(self):
            try:
                values  = {'pid':str(self.problem), 'language':'.cpp', 'code':self.cpp}
                r = urllib.request.Request(url=(pst_url % self.problem), data=urllib.parse.urlencode(values).encode(), headers=headers)
                response = self.opener.open(r)
                sublime.status_message('Submit OK')
                self.result  = True
                self.callback()
            except urllib.request.HTTPError as e:
                sublime.status_message('Submit Fail')
                sublime. error_message('%s: HTTP error %s contacting API' % (__name__, str(e.code)))
                self.result  = False
            except urllib.request.URLError as e:
                sublime.status_message('Submit Fail')
                sublime. error_message('%s: URL error %s contacting API' % (__name__, str(e.reason)))
                self.result  = False

    class ResultThreading(threading.Thread):
        def __init__(self, opener, view):
            self.opener  = opener
            self.view    = view
            self.result  = None
            threading.Thread.__init__(self)

        def new_file(self):
            return self.view.window().new_file()

        def write_line(self, view, st):
            view.run_command('smoj_submit_insert_helper', {'st':st+'\n'})

        def getName(self, st):
            try:
                if len(st) >= 26 and st[:26] == 'monitor_invalid_syscall_id':
                    return 'Restrict Function'
                return result_link[st]
            except:
                return st

        def printer(self, result, score, compile_info=None):
            temp = result.split(';')
            result = []
            for item in temp:
                result.append(item.split(':'))
            result = result[:-1]
            max_len = [6, 5, 4, 6]
            for item in result:
                item[0] = self.getName(item[0])
                for i in range(0, 4):
                    max_len[i] = max(max_len[i], len(item[i])+2)
            fix  = [0, 0, 3, 3]
            head = ['Result', 'Score', 'Time', 'Memory']
            for i in range(0, 4):
                head[i] = head[i].center(max_len[i] + fix[i])
            for item in result:
                item[0] = item[0].center(max_len[0])
                item[1] = item[1].rjust (max_len[1])
                item[2] = item[2].replace('不可用', 'NaN')
                item[2] = item[2].rjust (max_len[2])
                item[3] = item[3].replace('不可用', 'NaN')
                item[3] = item[3].rjust (max_len[3])
            tab = self.new_file()
            if compile_info:
                self.write_line(tab, 'Compile INFO :')
                self.write_line(tab, compile_info.replace('\r', '\n'))
            self.write_line(tab, 'Result        -> %s <-' % score)
            self.write_line(tab, '-%s-%s-%s-%s-' % ((len(head[0])+2)*'-', (len(head[1])+2)*'-', (len(head[2])+2)*'-', (len(head[3])+2)*'-'))
            self.write_line(tab, '| %s | %s | %s | %s |' % (head[0], head[1], head[2], head[3]))
            self.write_line(tab, '|%s|%s|%s|%s|' % ((len(head[0])+2)*'-', (len(head[1])+2)*'-', (len(head[2])+2)*'-', (len(head[3])+2)*'-'))
            for item in result:
                self.write_line(tab, '| %s | %-3s | %s ms | %s KB |' % (item[0], item[1], item[2], item[3]))
            self.write_line(tab, '-%s-%s-%s-%s-' % ((len(head[0])+2)*'-', (len(head[1])+2)*'-', (len(head[2])+2)*'-', (len(head[3])+2)*'-'))

        def run(self):
            while True:
                sublime.status_message('Waiting for judging...')
                r = urllib.request.Request(url=res_url, headers=headers)
                response = self.opener.open(r)
                tmp = response.read()
                html = ''
                while tmp:
                    html += tmp.decode()
                    tmp = response.read()
                m = _isw_re.search(html)
                if m.group(1) == 'done':
                    break
                time.sleep(0.01)
            sublime.status_message('Loading result...')
            m = _res_re.search(html)
            name    = m.group(1)
            problem = m.group(2)
            stamp   = m.group(3)
            score   = m.group(4)
            values = {'submitTime':stamp, 'pid':problem, 'user': name}
            r = urllib.request.Request(url=det_url, data=urllib.parse.urlencode(values).encode(), headers=headers)
            response = self.opener.open(r)
            result = json.loads(response.read().decode())
            if result['result'] == 'OI_MODE':
                sublime.status_message('This is an OI-MODE problem')
                self.result = True
                return None
            compile_info = None
            try:
                compile_info = result['compileInfo'][0]
            except:
                pass
            self.printer(result['result'].replace('\n', ''), score, compile_info)
