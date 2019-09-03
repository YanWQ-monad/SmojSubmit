import sublime

from unittest import TestCase
from SmojSubmit.tests.mox import Func, IgnoreArg, IsA, Mox, Verify

from SmojSubmit.libs.config import Config, ConfigSingleton


class TestConfig(TestCase):
    def setUp(self):
        self.mox = Mox()

    def mock_sublime_settings(self):
        self.settings_dict = {}
        self.settings = self.mox.CreateMock(sublime.Settings)
        self.settings.get(IsA(str)).WithSideEffects(self._settings_get).MultipleTimes()
        self.settings.set(IsA(str), IgnoreArg()).WithSideEffects(self._settings_set).MultipleTimes()
        self.settings.add_on_change(IsA(str), Func(callable))
        self.mox.StubOutWithMock(sublime, 'load_settings')
        sublime.load_settings('SmojSubmit.sublime-settings').AndReturn(self.settings)
        self.mox.StubOutWithMock(sublime, 'save_settings')
        sublime.save_settings('SmojSubmit.sublime-settings').MultipleTimes()

    def tearDown(self):
        self.mox.UnsetStubs()
        ConfigSingleton._instances = {}

    def _settings_get(self, key):
        return self.settings_dict.get(key)

    def _settings_set(self, key, value):
        self.settings_dict[key] = value

    def test_get(self):
        self.mock_sublime_settings()
        self.mox.ReplayAll()

        config = Config('SmojSubmit')
        self.settings_dict['A'] = {'B': {'C': 'a.b.c'}, 'D': 'a.d'}
        self.settings_dict['E'] = 'e'

        self.assertEqual(config.get('E'), 'e')
        self.assertEqual(config.get('A.B.C'), 'a.b.c')
        self.assertEqual(config.get('A.D'), 'a.d')
        self.assertEqual(config.get('A'), {'B': {'C': 'a.b.c'}, 'D': 'a.d'})
        self.assertEqual(config.get('Z'), None)
        self.assertEqual(config.get('Z', 'default'), 'default')
        Verify(sublime.load_settings)

    def test_set(self):
        self.mock_sublime_settings()
        self.mox.ReplayAll()

        config = Config('SmojSubmit')
        config.set('A', 'a')
        config.set('B.C.D', 'b.c.d')
        config.set('B.E', 'b.e')

        Verify(sublime.save_settings)
        self.assertEqual(self.settings_dict, {
            'A': 'a',
            'B': {
                'C': {'D': 'b.c.d'},
                'E': 'b.e'
            }
        })
        self.assertEqual(config.get('B'), {'C': {'D': 'b.c.d'}, 'E': 'b.e'})

    def test_singleton(self):
        self.mock_sublime_settings()
        self.mox.ReplayAll()

        self.assertEqual(id(Config('SmojSubmit')), id(Config('SmojSubmit')))
        self.assertNotEqual(id(Config('SmojSubmit')), id(Config('SmojSubmit-2')))

    def test_on_change(self):
        callback = self.mox.CreateMockAnything()
        callback()
        self.mox.StubOutWithMock(sublime, 'save_settings')
        sublime.save_settings('Preferences.sublime-settings')
        self.mox.ReplayAll()

        try:
            config = Config('Preferences')
            config.add_on_change('word_wrap', callback)
            config.set('word_wrap', not config.get('word_wrap'))

            self.mox.VerifyAll()
        finally:
            config.settings.clear_on_change('word_wrap')
