from . import riff, bitstream

class File(riff.Chunk):
    def alloc(self, **fields):
        fields.setdefault('data', RIFF)
        res = super(File, self).alloc(**fields)
        if 'id' not in fields:
            res['id'].set(RIFF.type)
        return res

