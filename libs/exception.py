class SmojsubmitException(Exception):
	def __init__(self, message):
		self.message = message
		super(SmojsubmitException, self).__init__(message)


class InvalidInput(SmojsubmitException):
	def __init__(self, message):
		super(InvalidInput, self).__init__(message)


class OjException(SmojsubmitException):
	def __init__(self, message):
		super(OjException, self).__init__(message)


class LoginFail(OjException):
	def __init__(self, reason=None):
		if reason is not None:
			message = 'Login failed: {}'.format(reason)
		else:
			message = 'Login failed'
		super(LoginFail, self).__init__(message)


class SubmitFail(OjException):
	def __init__(self, reason=None):
		if reason is not None:
			message = 'Submit failed: {}'.format(reason)
		else:
			message = 'Submit failed'
		super(SubmitFail, self).__init__(message)


class ExitScript(SmojsubmitException):
	def __init__(self):
		super(ExitScript, self).__init__('Exit script normally')
