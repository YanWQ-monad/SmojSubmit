import sublime_plugin
import time

from unittest import TestCase
from SmojSubmit.tests.mox import IsA, Mox

from SmojSubmit.libs.loader import MonadApplicationLoader


class TestLoader(TestCase):
    def setUp(self):
        self.mox = Mox()

    def tearDown(self):
        self.mox.UnsetStubs()

    def test_loader(self):
        self.mox.StubOutWithMock(sublime_plugin.ApplicationCommand, '__init__')
        sublime_plugin.ApplicationCommand.__init__(IsA(sublime_plugin.ApplicationCommand))
        callback = self.mox.CreateMockAnything()
        callback()

        class MockedApplication(MonadApplicationLoader):
            def delay_init(self):
                callback()

        self.mox.ReplayAll()
        application = MockedApplication()  # noqa: F841
        time.sleep(1.5)

        self.mox.VerifyAll()
