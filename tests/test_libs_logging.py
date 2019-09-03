import logging

from unittest import TestCase

from SmojSubmit.libs.logging import SmojSubmitFormatter


class RecordsCollector(logging.Handler):
    def __init__(self, *args, **kwargs):
        super(RecordsCollector, self).__init__(*args, **kwargs)
        self.messages = []

    def emit(self, record):
        self.messages.append(self.format(record))


class TestLogging(TestCase):
    def setUp(self):
        self.collector = RecordsCollector()
        self.collector.setFormatter(SmojSubmitFormatter())
        logging.getLogger('SmojSubmit.test').addHandler(self.collector)

    def tearDown(self):
        logging.getLogger('SmojSubmit.test').removeHandler(self.collector)

    def test_error(self):
        logger = logging.getLogger('SmojSubmit.test')
        logger.error('Error message')
        self.assertEqual(len(self.collector.messages), 1)
        message = next(iter(self.collector.messages))
        self.assertRegex(message, r'SmojSubmit: \[E test:\d+\] Error message')

    def test_exception(self):
        logger = logging.getLogger('SmojSubmit.test')
        try:
            raise Exception('Exception message')
        except Exception as e:
            logger.exception(str(e))
        self.assertEqual(len(self.collector.messages), 1)
        message = next(iter(self.collector.messages))
        self.assertRegex(message, r'SmojSubmit: \[E test:\d+\] Exception message\. Traceback:\n'
                                  r'Traceback \(most recent call last\):.*')
