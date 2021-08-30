import sys, itertools, functools

__izip_longest__ = itertools.izip_longest if sys.version_info.major < 3 else itertools.zip_longest

intofdata = lambda data: functools.reduce(lambda t, c: t * 256 | c, bytearray(data), 0)
dataofint = lambda integer: ((integer == 0) and b'\0') or (dataofint(integer // 256).lstrip(b'\0') + bytes(bytearray([integer % 256])[:1]))

from . import jp2, jfif
