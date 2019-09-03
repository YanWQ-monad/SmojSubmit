# -*- coding: utf-8 -*-

import re


_fre_re = re.compile(r'freopen\("([^.])+\.(in|out)"( ?), "(r|w)", std(in |out)\);')
_cm1_re = re.compile(r'/\*(\s*)((freopen(.*,.*,.*)\s*){1,2})\s*\*/')
_cm2_re = re.compile(r'(\s*)//(\s*)(freopen\("([^.])+\.(in|out)"( ?), "(r|w)", std(in|out)( ?)\);)')


def freopen_filter(code, pid=None):
    result = code
    if pid is None:
        result = re.sub(_fre_re, '', result)
    else:
        result = re.sub(_fre_re, r'freopen("{}.\2"\3, "\4", std\5);'.format(pid), result)
        result = re.sub(_cm1_re, r'\1\2'                                        , result)
        result = re.sub(_cm2_re, r'\1\3'                                        , result)
    return result
