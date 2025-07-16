from . import riff, vp8

class File(riff.Chunk):
    def alloc(self, **fields):
        fields.setdefault('data', riff.RIFF)
        res = super(File, self).alloc(**fields)
        if 'id' not in fields:
            res['id'].set(riff.RIFF.type)
        return res

