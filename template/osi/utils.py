import functools, itertools, operator

def checksum(bytes):
    array = itertools.chain(bytearray(bytes), [0] if len(bytes) % 2 else [])
    iterable = map(functools.partial(functools.reduce, lambda agg, item: 0x100 * agg + item), zip(*[iter(array)] * 2))
    shorts = [item for item in iterable]
    seed = sum(shorts)
    shifted, _ = divmod(seed, pow(2, 16))
    checksum = shifted + (seed & 0XFFFF)
    return 0xFFFF & ~checksum
