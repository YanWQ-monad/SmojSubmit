import sublime
import time

from unittest import TestCase

import SmojSubmit.libs.printer


class TestPrinterView(TestCase):
    def setUp(self):
        self.result_view = SmojSubmit.libs.printer.SmojResultView('TITLE')
        self.result_view.create_view()

    @property
    def view(self):
        return self.result_view.view

    def tearDown(self):
        if self.view:
            self.view.set_scratch(True)
            self.view.window().focus_view(self.view)
            self.view.window().run_command('close_file')

    def get_row(self, row):
        return self.view.substr(self.view.line(self.view.text_point(row, 0)))

    def test_title(self):
        self.assertEqual(self.view.name(), 'TITLE')

    def test_readonly(self):
        self.view.window().run_command('insert', {'characters': '#content#'})
        self.assertEqual(0, len(self.view.find_all('#content#')))

    def test_add_line(self):
        self.result_view.add_line('Content 1')
        self.result_view.add_line('Content 2', 1)
        self.assertEqual(self.get_row(0), 'Content 2')
        self.assertEqual(self.get_row(1), 'Content 1')


class TestFormatter(TestCase):
    def test_normal(self):
        header, details = SmojSubmit.libs.printer.pretty_format(
            ['Header 1', '<<<<< Header 2 >>>>>>'],
            [
                ['Content 1 1 >>>>>>>', 'Content 1 2'],
                ['Content 2 1', 'Content 2 2'],
            ])

        details.append(header)
        row_1_width = [len(details[0]) for details in details]
        row_2_width = [len(details[1]) for details in details]

        self.assertEqual(1, len(set(row_1_width)))
        self.assertEqual(1, len(set(row_2_width)))

    def test_align(self):
        header, details = SmojSubmit.libs.printer.pretty_format(
            ['Normal', 'Time', 'Memory', 'Score'],  # Normal: center, other: right
            [['AA', '1', '2', '3']])
        self.assertEqual('  AA  ', details[0][0])
        self.assertEqual('   1', details[0][1])
        self.assertEqual('     2', details[0][2])
        self.assertEqual('    3', details[0][3])


class TestPrintResult(TestCase):
    def tearDown(self):
        if sublime.active_window().active_view().name() == 'Result':
            sublime.active_window().run_command('close_file')

    def get_content(self):
        view = sublime.active_window().active_view()
        return view.substr(sublime.Region(0, view.size()))

    def test_normal(self):
        header = ['ID', 'Result', 'Time']
        details = [
            ['1', 'Accepted', '10 ms'],
            ['2', 'Time Limit Exceeded', '1010 ms'],
        ]
        expected_content = (
            'Problem ID : P1000\n'
            r" _____ _                  _     _           _ _     _____                       _          _ " + "\n"
            r"|_   _(_)_ __ ___   ___  | |   (_)_ __ ___ (_) |_  | ____|_  _____ ___  ___  __| | ___  __| |" + "\n"
            r"  | | | | '_ ` _ \ / _ \ | |   | | '_ ` _ \| | __| |  _| \ \/ / __/ _ \/ _ \/ _` |/ _ \/ _` |" + "\n"
            r"  | | | | | | | | |  __/ | |___| | | | | | | | |_  | |___ >  < (_|  __/  __/ (_| |  __/ (_| |" + "\n"
            r"  |_| |_|_| |_| |_|\___| |_____|_|_| |_| |_|_|\__| |_____/_/\_\___\___|\___|\__,_|\___|\__,_|" + "\n"
            '\n'
            'Result        -> 50 <-\n'
            '--------------------------------------\n'
            '| ID |        Result       |   Time  |\n'
            '|------------------------------------|\n'
            '| 1  |       Accepted      |   10 ms |\n'
            '| 2  | Time Limit Exceeded | 1010 ms |\n'
            '--------------------------------------\n')

        SmojSubmit.libs.printer.print_result(
            header, details, 'Time Limit Exceeded', '50', None, 'P1000')

        time.sleep(0.3)

        self.assertEqual(sublime.active_window().active_view().name(), 'Result')
        self.assertEqual(self.get_content(), expected_content)

    def test_with_completion_message(self):
        header = ['ID', 'Result', 'Time']
        details = [
            ['1', 'Compile Error', 'NaN ms'],
            ['2', 'Compile Error', 'NaN ms'],
        ]

        compile_message = (
            'source.cpp: In function ‘int main()’:\n'
            'source.cpp:7:2: error: ‘scanf’ was not declared in this scope\n'
            '  scanf("%d", &n);\n'
            '  ^~~~~\n')

        expected_content = (
            'Problem ID : P1000\n'
            r"  ____                      _ _        _____                     " + "\n"
            r" / ___|___  _ __ ___  _ __ (_) | ___  | ____|_ __ _ __ ___  _ __ " + "\n"
            r"| |   / _ \| '_ ` _ \| '_ \| | |/ _ \ |  _| | '__| '__/ _ \| '__|" + "\n"
            r"| |__| (_) | | | | | | |_) | | |  __/ | |___| |  | | | (_) | |   " + "\n"
            r" \____\___/|_| |_| |_| .__/|_|_|\___| |_____|_|  |_|  \___/|_|   " + "\n"
            r"                     |_|                                         " + "\n"
            'Compile INFO:\n') + compile_message + (
            'Result        -> 0 <-\n'
            '-------------------------------\n'
            '| ID |     Result    |  Time  |\n'
            '|-----------------------------|\n'
            '| 1  | Compile Error | NaN ms |\n'
            '| 2  | Compile Error | NaN ms |\n'
            '-------------------------------\n')

        SmojSubmit.libs.printer.print_result(
            header, details, 'Compile Error', '0', compile_message, 'P1000')

        time.sleep(0.3)

        self.assertEqual(sublime.active_window().active_view().name(), 'Result')
        self.assertEqual(self.get_content(), expected_content)
