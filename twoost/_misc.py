# coding: utf-8

import re
import os
import errno
import functools
import itertools

from twisted.python import log
from twisted.internet import defer, reactor


_DIGITS_RE = re.compile(r"([0-9]+)")


class lazycol(object):

    __slots__ = ('_iterable',)

    def __new__(cls, _iterable):
        if isinstance(_iterable, (tuple, frozenset, lazycol)):
            return _iterable
        lc = object.__new__(cls)
        lc._iterable = _iterable
        return lc

    def __iter__(self):
        self._iterable, result = itertools.tee(self._iterable)
        return result


def natural_sorted(iterable):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in _DIGITS_RE.split(key)]
    return sorted(iterable, key=alphanum_key)


@property
def required_attr(self):
    raise NotImplementedError


class cached_property(object):

    __miss = object()

    def __init__(self, func, name=None, doc=None):
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        value = obj.__dict__.get(self.__name__, self.__miss)
        if value is self.__miss:
            value = self.func(obj)
            obj.__dict__[self.__name__] = value
        return value


def ignore_errors(f, logger=None):

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return defer.maybeDeferred(f, *args, **kwargs).addErrback(log.err)

    return wrapper


def get_attached_clock(obj):
    return getattr(obj, 'clock', None) or reactor


def subdict(d, keys=None):
    d = dict(d)
    if keys is None:
        return d
    return dict(
        (k, v)
        for k, v in d.items()
        if k in keys
    )


def merge_dicts(ds):
    d = {}
    for x in ds:
        d.update(x)
    return d


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise