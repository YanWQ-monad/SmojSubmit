# -*- coding: utf-8 -*-

from http.cookiejar import Cookie
import logging
import time

from .config import Config


logger = logging.getLogger(__name__)


def save_cookie(name, cookie, keys):
    config = Config('SmojSubmit-cookies')
    cookies = {item.name: item.value for item in cookie}
    for key in keys:
        logger.debug('Save cookie "{}" {} => {}'.format(name, key, cookies[key]))
        config.set('{}.{}'.format(name, key), cookies[key])


def load_cookie(name, domain, cookie, keys):
    config = Config('SmojSubmit-cookies')
    expires = str(int(time.time()) + 60 * 60 * 24 * 7)
    success = True
    for key in keys:
        value = config.get('{}.{}'.format(name, key))
        if value is None:
            logger.debug('cookie not found "{}" {} => [not set]'.format(name, key))
            success = False
            continue
        logger.debug('Load cookie "{}" {} => {}'.format(name, key, value))
        cookie.set_cookie(Cookie(0, key, value, None, False, domain, True, False, '/', True,
                                 True, expires, False, None, None, None))
    logger.debug('Load cookie "{}" {}successful'.format(name, '' if success else 'un'))
    return success
