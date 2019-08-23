# -*- coding: utf-8 -*-

import logging.config
import logging
import traceback


PLUGIN_NAME = 'SmojSubmit'


class SmojSubmitFormatter(logging.Formatter):
	def format(self, record):
		level = record.levelname[0]
		name = record.name
		if name.startswith(PLUGIN_NAME + '.'):
			name = name[len(PLUGIN_NAME) + 1 : ]
		if record.exc_info is not None:
			trace = ''.join(traceback.format_exception(*record.exc_info))
			s = PLUGIN_NAME + ': [{0} {1}:{2.lineno}] {2.msg}. Traceback:\n{3}'.format(level, name, record, trace)
		else:
			s = PLUGIN_NAME + ': [{0} {1}:{2.lineno}] {2.msg}'.format(level, name, record)
		return s


def init_logging():
	config = {
		'version': 1,
		'disable_existing_loggers': False,
		'formatters': {
			'smojsubmit_fmt': {
				'()': __name__ + '.SmojSubmitFormatter'
			}
		},
		'handlers': {
			'smojsubmit_handler': {
				'level': 'WARNING',
				'formatter': 'smojsubmit_fmt',
				'class': 'logging.StreamHandler',
				'stream': 'ext://sys.stderr'
			}
		},
		'loggers': {
			'SmojSubmit': {
				'handlers': ['smojsubmit_handler'],
				'level': 'WARNING',
				'propagate': False
			}
		}
	}
	logging.config.dictConfig(config)

	logger = logging.getLogger(__name__)
	logger.info('logging initialized')
