import sublime

from unittest import TestCase
from SmojSubmit.tests.mox import IsA, Mox

import SmojSubmit.libs.code
from SmojSubmit.libs.exception import InvalidInput


class TestCode(TestCase):
    def setUp(self):
        self.mox = Mox()
        self.view = self.mox.CreateMock(sublime.View)
        self.code = ("""// 1235.cpp"""
                     """#include <cstdio>"""
                     """int main() {"""
                     """    return 0;"""
                     """}""")

    def tearDown(self):
        self.mox.UnsetStubs()

    def mock_active_view(self):
        self.mox.StubOutWithMock(SmojSubmit.libs.code, 'get_active_view')
        SmojSubmit.libs.code.get_active_view().AndReturn(self.view)

    def mock_get_lang(self, return_value):
        self.mox.StubOutWithMock(SmojSubmit.libs.code, 'get_lang')
        SmojSubmit.libs.code.get_lang().AndReturn(return_value)

    def test_get_code(self):
        self.mock_active_view()

        self.view.size().AndReturn(len(self.code))
        self.view.substr(sublime.Region(0, len(self.code))).AndReturn(self.code)

        self.mox.ReplayAll()
        self.assertEqual(SmojSubmit.libs.code.get_text(), self.code)
        self.mox.VerifyAll()

    def test_invalid_pid(self):
        self.mock_active_view()
        self.mock_get_lang('C++')

        self.view.find_all(IsA(str), IsA(int)).AndReturn([])

        self.mox.ReplayAll()
        with self.assertRaises(InvalidInput):
            SmojSubmit.libs.code.get_pid()
        self.mox.VerifyAll()

    def test_multiple_pids(self):
        self.mock_active_view()
        self.mock_get_lang('C++')

        self.view.find_all(IsA(str), IsA(int)).AndReturn([sublime.Region(1, 2), sublime.Region(3, 4)])

        self.mox.ReplayAll()
        with self.assertRaises(InvalidInput):
            SmojSubmit.libs.code.get_pid()
        self.mox.VerifyAll()

    def test_get_pid(self):
        self.mock_active_view()
        self.mock_get_lang('C++')

        region = sublime.Region(0, 11)  # match '// 1235.cpp' in self.code
        self.view.find_all(IsA(str), IsA(int)).AndReturn([region])
        self.view.substr(region).AndReturn('// 1235.cpp')

        self.mox.ReplayAll()
        self.assertEqual(SmojSubmit.libs.code.get_pid(), '1235')
        self.mox.VerifyAll()

    def test_get_lang(self):
        self.mock_active_view()

        settings = self.mox.CreateMock(sublime.Settings)
        self.view.settings().AndReturn(settings)
        settings.get('syntax').AndReturn('Packages/Python/Python.sublime-syntax')

        self.mox.ReplayAll()
        self.assertEqual(SmojSubmit.libs.code.get_lang(), 'Python')
        self.mox.VerifyAll()

    def test_active_view(self):
        self.mox.StubOutWithMock(sublime, 'active_window')
        window = self.mox.CreateMock(sublime.Window)
        sublime.active_window().AndReturn(window)
        window.active_view().AndReturn(self.view)

        self.mox.ReplayAll()
        self.assertEqual(SmojSubmit.libs.code.get_active_view(), self.view)
        self.mox.VerifyAll()

    def test_no_active_view(self):
        self.mox.StubOutWithMock(sublime, 'active_window')
        window = self.mox.CreateMock(sublime.Window)
        sublime.active_window().AndReturn(window)
        window.active_view().AndReturn(None)

        self.mox.ReplayAll()
        with self.assertRaises(InvalidInput):
            SmojSubmit.libs.code.get_active_view()
        self.mox.VerifyAll()
