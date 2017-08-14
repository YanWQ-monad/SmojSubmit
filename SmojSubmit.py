import sublime, sublime_plugin
import re, urllib.request, urllib.parse, http.cookiejar, threading

_cpp_re = re.compile(r'// ?(\d{4})\.cpp'                                                           )
_fre_re = re.compile(r'freopen\("([^.])+\.(in|out)"( ?), "(r|w)", std(in|out)( ?)\);'              )
_cm1_re = re.compile(r'/\*(\s*)((freopen(.*,.*,.*)\s*){1,2})\s*\*/'                                )
_cm2_re = re.compile(r'(\s*)//(\s*)(freopen\("([^.])+\.(in|out)"( ?), "(r|w)", std(in|out)( ?)\);)')

class SmojSubmitCommand(sublime_plugin.TextCommand):
    def __init__(self, view):
        config = sublime.load_settings('SmojSubmit.sublime-settings')
        self.url      =  'http://smoj.nhedu.net'
        self.headers  = {'User-Agent': r'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.75 Safari/537.36'}
        self.post_url =  'http://smoj.nhedu.net/submit_problem?pid=%d'
        username = config.get('username')
        password = config.get('password')
        self.opener = self.login(username, password)
        sublime_plugin.TextCommand.__init__(self, view)

    def setOpener(self, opener):
        self.opener = opener

    def post(self, cpp, problem):
        sublime.status_message('Posting to SMOJ')
        thread = self.PostThreading(self.opener, self.post_url, cpp, problem, self.headers)
        thread.start()

    def login(self, username, password):
        thread = self.LoginThreading(self.url, username, password, self.headers, self.setOpener)
        thread.start()

    def getProblemNum(self):
        sublime.status_message('Search problem number')
        chunk = self.view.find_all(r'// ?(\d{4})\.cpp', 0)
        if len(chunk) < 1:
            sublime.status_message('Not found problem number')
            sublime.error_message ('Not found problem number')
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
        self.post(content, problem)

    class LoginThreading(threading.Thread):
        def __init__(self, url, username, password, headers, callback):
            self.url      = url
            self.username = username
            self.password = password
            self.headers  = headers
            self.callback = callback
            self.result   = None
            threading.Thread.__init__(self)

        def run(self):
            cookie  = http.cookiejar.CookieJar()
            handler = urllib.request.HTTPCookieProcessor(cookie)
            opener  = urllib.request.build_opener(handler)
            values  = {'redirect_to':'', 'username':self.username, 'password':self.password}
            r = urllib.request.Request(url=self.url+'/login', data=urllib.parse.urlencode(values).encode(), headers=self.headers)
            response = opener.open(r)
            self.callback(opener)
            self.result = True

    class PostThreading(threading.Thread):
        def __init__(self, opener, url, cpp, problem, headers):
            self.opener  = opener
            self.url     = url
            self.cpp     = cpp
            self.problem = problem
            self.headers = headers
            self.result  = None
            threading.Thread.__init__(self)

        def run(self):
            try:
                values  = {'pid':str(self.problem), 'language':'.cpp', 'code':self.cpp}
                r = urllib.request.Request(url=(self.url % self.problem), data=urllib.parse.urlencode(values).encode(), headers=self.headers)
                response = self.opener.open(r)
                sublime.status_message('Submit OK')
                self.result  = True
            except urllib.request.HTTPError as e:
                sublime.status_message('Submit Fail')
                sublime.error_message('%s: HTTP error %s contacting API' % (__name__, str(e.code)))
                self.result  = False
            except urllib.request.URLError as e:
                sublime.status_message('Submit Fail')
                sublime.error_message('%s: URL error %s contacting API' % (__name__, str(e.reason)))
                self.result  = False
