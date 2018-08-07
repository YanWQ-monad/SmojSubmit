# -*- coding: utf-8 -*-

import http.cookiejar
import urllib.request
import urllib.parse
import sublime
import json
import time
import re

from ..libs import logging as log
from ..libs import printer
from ..main import headers


username = None
password = None
opener = None

root_url = 'http://10.3.35.134'
post_url = root_url + '/submit_problem?pid={}'
rest_url = root_url + '/allmysubmits'
detl_url = root_url + '/showresult'

_fre_re = re.compile(r'freopen\("([^.])+\.(in|out)"( ?), "(r|w)", std(in |out)\);')
_cm1_re = re.compile(r'/\*(\s*)((freopen(.*,.*,.*)\s*){1,2})\s*\*/')
_cm2_re = re.compile(r'(\s*)//(\s*)(freopen\("([^.])+\.(in|out)"( ?), "(r|w)", std(in|out)( ?)\);)')
_res_re = re.compile(r'<td><a href="#" id="result"><input type="hidden" value="(.*)"><input type="hidden" value="(\d{4,})"><input type="hidden" id="submitTime" value="(\d+)">((\d+)/(\d+)|点击查看)</a></td>')
_isw_re = re.compile(r'<td><a href="showproblem\?id=\d{4,}">\d{4,}</a></td>\s*<td>([a-zA-Z ]*)</td>')

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
	# monitor_invalid_syscall_id: Restrict Function
	# 测评机出错--无法清空沙箱或者无法复制文件.in到沙箱: No Data
}


def init(config):
	global username
	global password
	username = config['username']
	password = config['password']
	if config.get('init_login', False):
		login(username, password)


def check_login(resp=None):
	if opener is None:
		return 'Object "opener" is None'
	if resp is None:
		r = urllib.request.Request(url=root_url, headers=headers)
		resp = opener.open(r)
	if resp.url.find('/login') != -1:
		return resp.read().decode()[:100]


def login(username, password):
	sublime.status_message('Logging in to SMOJ...')
	global opener
	cookie  = http.cookiejar.CookieJar()
	handler = urllib.request.HTTPCookieProcessor(cookie)
	opener  = urllib.request.build_opener(handler)

	values  = {
		'redirect_to': '',
		'username': username,
		'password': password
	}

	r = urllib.request.Request(url=root_url+'/login', data=urllib.parse.urlencode(values).encode(), headers=headers)
	resp = opener.open(r)
	info = check_login(resp)
	if info:
		sublime.status_message('Login to SMOJ fail: {}'.format(info))
		log.error('Login to SMOJ fail: {}'.format(info))
		return False
	else:
		sublime.status_message('Login to SMOJ OK')
		log.info('Login to SMOJ: OK')
		return True


def code_filter(code, pid):
	result = code
	result = re.sub(_fre_re, r'freopen("{}.\2"\3, "\4", std\5);'.format(pid), result)
	result = re.sub(_cm1_re, r'\1\2'                                        , result)
	result = re.sub(_cm2_re, r'\1\2\3'                                      , result)
	return result


def submit(pid, code, lang):
	if check_login():
		if not login(username, password):
			log.error('Submit fail: Cannot login')
			return False
	assert lang == 'C++' or lang == 'C'

	code = code_filter(code, pid)
	sublime.status_message('Submitting code to SMOJ...')
	log.debug             ('Submitting code to SMOJ...')

	values  = {
		'pid': str(pid),
		'language': '.cpp',
		'code': code
	}
	r = urllib.request.Request(url=(post_url.format(pid)), data=urllib.parse.urlencode(values).encode(), headers=headers)
	resp = opener.open(r)
	if resp.url.find('allmysubmits') == -1:
		if resp.url.find('login') != -1:
			sublime.status_message('Submit Fail: Invalid login')
			log.warning('Submit Fail. Redirect to {}'.format(resp.url))
		else:
			info = resp.read().decode()[:100]
			sublime.status_message('Submit Fail: {}'.format(info))
			log.warning('Submit Fail: {}'.format(info))
		return False
	else:
		sublime.status_message('Submit OK, fetching result...')
		log.info('Submit OK')

	fetch_result()


def wait_for_judge():
	name, pid, stamp, score = None, None, None, None
	while True:
		time.sleep(1)
		sublime.status_message('Waiting for judging...')
		r = urllib.request.Request(url=rest_url, headers=headers)
		resp = opener.open(r)
		html = resp.read().decode()
		m = _isw_re.search(html)
		if name is None:
			match = _res_re.search(html)
			name  = match.group(1)
			pid   = match.group(2)
			stamp = match.group(3)
		if m.group(1) == 'done':
			match = _res_re.search(html)
			score = match.group(4)
			break
	return name, pid, stamp, score


def get_status_name(st):
	if st[:3] == 'goc':
		st = st[3:]
	try:
		if len(st) >= 26 and st[:26] == 'monitor_invalid_syscall_id':
			return 'Restrict Function'
		if len(st) >= 21 and st[:21] == '测评机出错--无法清空沙箱或者无法复制文件':
			return 'No Data'
		return result_link[st]
	except KeyError:
		return st


def load_result(name, pid, stamp):
	sublime.status_message('Loading result...')

	values = {
		'submitTime': stamp,
		'pid': pid,
		'user': name
	}
	r = urllib.request.Request(url=detl_url, data=urllib.parse.urlencode(values).encode(), headers=headers)
	resp = opener.open(r)
	result = json.loads(resp.read().decode())
	if result['result'] == 'OI_MODE':
		sublime.status_message('This is an OI-MODE problem')
		return None, None, None
	compile_info = None
	try:
		compile_info = result['compileInfo'][0]
	except:
		pass

	temp = result['result'].replace('\n', '')
	detail = [ item.split(':') for item in temp.split(';') ][:-1]
	for row in detail:
		row[0] = get_status_name(row[0])
		row[2] = row[2].replace('不可用', 'NaN') + ' ms'
		row[3] = row[3].replace('不可用', 'NaN') + ' KB'

	non_ac_list = list(filter(lambda x: x != 'Accepted', [ item[0] for item in detail ]))
	main = non_ac_list[0] if len(non_ac_list) else 'Accepted'

	return detail, main, compile_info


def fetch_result():
	head = ['Result', 'Score', 'Time', 'Memory']

	name, pid, stamp, score = wait_for_judge()
	detail, main, cpl_info = load_result(name, pid, stamp)
	if main is not None:
		printer.print_result(head, detail, main, score, cpl_info, pid)
