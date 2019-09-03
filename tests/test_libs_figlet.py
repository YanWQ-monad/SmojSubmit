from unittest import TestCase

from SmojSubmit.libs.figlet import get_figlet


class TestFiglet(TestCase):
    def test_normal(self):
        self.assertEqual(7, len(get_figlet('Accepted').split('\n')))

    def test_not_found(self):
        self.assertEqual('', get_figlet('No Figlet'))
