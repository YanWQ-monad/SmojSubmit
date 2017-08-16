# -*- coding: utf-8 -*-

import urllib.request
import urllib.parse
import threading
import sublime
import json
import time
import re

from .. import common
from .  import config

_res_re = re.compile(r'<td><a href="#" id="result"><input type="hidden" value="(.*)"><input type="hidden" value="(\d{4,})"><input type="hidden" id="submitTime" value="(\d+)">((\d+)/(\d+)|点击查看)</a></td>')
_isw_re = re.compile(r'<td><a href="showproblem\?id=\d{4,}">\d{4,}</a></td>\s*<td>([a-zA-Z ]*)</td>')

res_url = config.root_url + '/allmysubmits'
det_url = config.root_url + '/showresult'

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

    def separate(self, result):
        temp = result.split(';')
        result = []
        for item in temp:
            result.append(item.split(':'))
        result = result[:-1]
        return result

    def print_accept(self, tab):
        self.write_line(tab, '')
        self.write_line(tab, '                            _           _ ')
        self.write_line(tab, '    /\\                     | |         | |')
        self.write_line(tab, '   /  \\   ___ ___ ___ _ __ | |_ ___  __| |')
        self.write_line(tab, '  / /\\ \\ / __/ __/ _ \\ \'_ \\| __/ _ \\/ _` |')
        self.write_line(tab, ' / ____ \\ (_| (_|  __/ |_) | ||  __/ (_| |')
        self.write_line(tab, '/_/    \\_\\___\\___\\___| .__/ \\__\\___|\\__,_|')
        self.write_line(tab, '                     | |                  ')
        self.write_line(tab, '                     |_|                  ')
        self.write_line(tab, '')

    def print_compile_info(self, tab, compile):
        self.write_line(tab, 'Compile INFO :')
        self.write_line(tab, compile_info.replace('\r', '\n'))

    def print_head(self, tab, head):
        tot_len = 0
        for i in range(0, 4):
            tot_len += len(head[i])+2
        self.write_line(tab, '%s%s%s' % ('|', '-'*(tot_len+3), '|'))
        self.write_line(tab, '| %s | %s | %s | %s |' % (head[0], head[1], head[2], head[3]))
        self.write_line(tab, '%s%s%s' % ('|', '-'*(tot_len+3), '|'))

    def printer(self, result, score, compile_info=None):
        result = self.separate(result)
        fix     = [0       ,  0     , 3     , 3       ]
        head    = ['Result', 'Score', 'Time', 'Memory']
        max_len = [len(head[i]) for i in range(0, 4)]
        for item in result:
            item[0] = self.getName(item[0])
            item[2] = item[2].replace('不可用', 'NaN')
            item[3] = item[3].replace('不可用', 'NaN')
            for i in range(0, 4):
                max_len[i] = max(max_len[i], len(item[i])+2)
        for i in range(0, 4):
            head[i] = head[i].center(max_len[i] + fix[i])
        for item in result:
            item[0] = item[0].center(max_len[0])
            item[1] = item[1].rjust (max_len[1])
            item[2] = item[2].rjust (max_len[2])
            item[3] = item[3].rjust (max_len[3])
        tab = self.new_file()
        if score.find('100/100') != -1:
            self.print_accept(tab)
        if compile_info:
            self.print_compile_info(tab, compile_info)
        self.write_line(tab, 'Result        -> %s <-' % score)
        self.print_head(tab, head)
        for item in result:
            self.write_line(tab, '| %s | %-3s | %s ms | %s KB |' % (item[0], item[1], item[2], item[3]))
        self.write_line(tab, '-%s-%s-%s-%s-' % ((len(head[0])+2)*'-', (len(head[1])+2)*'-', (len(head[2])+2)*'-', (len(head[3])+2)*'-'))

    def wait_judge(self):
        name, problem, stamp, score = None, None, None, None
        while True:
            sublime.status_message('Waiting for judging...')
            r = urllib.request.Request(url=res_url, headers=common.headers)
            response = self.opener.open(r)
            tmp = response.read()
            html = ''
            while tmp:
                html += tmp.decode()
                tmp = response.read()
            m = _isw_re.search(html)
            if name is None:
                match = _res_re.search(html)
                name    = match.group(1)
                problem = match.group(2)
                stamp   = match.group(3)
            if m.group(1) == 'done':
                match = _res_re.search(html)
                score = match.group(4)
                break
            time.sleep(0.05)
        return name, problem, stamp, score


    def run(self):
        name, problem, stamp, score = self.wait_judge()
        sublime.status_message('Loading result...')
        values = {'submitTime':stamp, 'pid':problem, 'user': name}
        r = urllib.request.Request(url=det_url, data=urllib.parse.urlencode(values).encode(), headers=common.headers)
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
