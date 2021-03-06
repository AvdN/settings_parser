# -*- coding: utf-8 -*-
"""
Created on Wed Nov 23 16:45:32 2016

@author: Pedro
"""

import sys
import tempfile
from contextlib import contextmanager
import os
import logging
import warnings
from functools import wraps

from typing import Generator, Callable, Any, Tuple, Dict


# http://stackoverflow.com/a/11892712
@contextmanager
def temp_filename(data: str = None, mode: str = 'wt') -> Generator:
    '''Creates a temporary file and writes text data to it. It returns its filename.
        It deletes the file after use in a context manager.
    '''
    # file won't be deleted after closing
    temp = tempfile.NamedTemporaryFile(mode=mode, delete=False)
    if data:
        temp.write(data)  # type: ignore
    temp.close()
    try:
        yield temp.name
    finally:
        os.unlink(temp.name)  # delete file


class cached_property():
    '''Computes attribute value and caches it in the instance.
    Python Cookbook (Denis Otkidach) http://stackoverflow.com/users/168352/denis-otkidach
    This decorator allows you to create a property which can be computed once and
    accessed many times. Sort of like memoization.
    http://stackoverflow.com/a/6429334
    '''
    def __init__(self, method: Callable, name: str = None) -> None:
        '''Record the unbound-method and the name'''
        self.method = method
        self.name = name or method.__name__
        self.__doc__ = method.__doc__

    def __get__(self, inst: object, cls: type) -> Any:
        '''self: <__main__.cache object at 0xb781340c>
           inst: <__main__.Foo object at 0xb781348c>
           cls: <class '__main__.Foo'>
        '''
        if inst is None:
            # instance attribute accessed on class, return self
            # You get here if you write `Foo.bar`
            return self
        # compute, cache and return the instance's attribute value
        result = self.method(inst)
        # setattr redefines the instance's attribute so this doesn't get called again
        setattr(inst, self.name, result)
        return result


def log_exceptions_warnings(function: Callable) -> Callable:
    '''Decorator to log exceptions and warnings'''
    @wraps(function)
    def wrapper(*args: Tuple, **kwargs: Dict) -> Any:
        try:
            with warnings.catch_warnings(record=True) as warn_list:
                # capture all warnings
                warnings.simplefilter('always')
                ret = function(*args, **kwargs)
        except Exception as exc:
            logger = logging.getLogger(function.__module__)
            logger.error(exc.args[0])
            raise
        for warn in warn_list:
            logger = logging.getLogger(function.__module__)
            msg = (warn.category.__name__ + ': "' + str(warn.message) +
                   '" in ' + os.path.basename(warn.filename) +
                   ', line: ' + str(warn.lineno) + '.')
            logger.warning(msg)
            # re-raise warnings
            warnings.warn(msg, warn.category)
        return ret
    return wrapper


@contextmanager
def console_logger_level(level: int) -> Generator:  # pragma: no cover
    '''Temporary change the console handler level.'''
    logger = logging.getLogger()  # root logger
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            if handler.stream == sys.stdout:  # type: ignore
                old_level = handler.level
                handler.setLevel(level)
                yield None
                handler.setLevel(old_level)
                return
    # in case no console handler exists
    yield None
    return


@contextmanager
def no_logging() -> Generator:  # pragma: no cover
    '''Temporary disable all logging.'''
    logging.disable(logging.CRITICAL)
    yield None
    logging.disable(logging.NOTSET)


class ConfigError(SyntaxError):
    '''Something in the configuration file is not correct'''
    pass


class ConfigWarning(UserWarning):
    '''Something in the configuration file is not correct'''
    pass
