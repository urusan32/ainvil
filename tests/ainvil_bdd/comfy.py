"""Direct access to the ComfyUI test server, for checking what Ainvil did (stdlib urllib)."""
import json
import struct
import urllib.parse
import urllib.request


class Comfy:
    def __init__(self, base):
        self.base = base if base.endswith('/') else base + '/'
        self._oi = None

    def get(self, path, raw=False):
        with urllib.request.urlopen(self.base + path.lstrip('/'), timeout=60) as r:
            data = r.read()
        return data if raw else json.loads(data)

    def object_info(self):
        if self._oi is None:
            self._oi = self.get('object_info')
        return self._oi

    def options(self, cls, inp):
        spec = self.object_info()[cls]['input']
        s = spec.get('required', {}).get(inp) or spec.get('optional', {}).get(inp)
        if isinstance(s[0], list):
            return s[0]
        return s[1].get('options', [])

    def history(self, prompt_id=None):
        return self.get('history/' + prompt_id if prompt_id else 'history?max_items=50')

    def queue(self):
        return self.get('queue')

    def queued_ids(self):
        q = self.queue()
        return {e[1] for e in q.get('queue_running', []) + q.get('queue_pending', [])}

    def view(self, filename, subfolder='', type='output'):
        q = urllib.parse.urlencode({'filename': filename, 'subfolder': subfolder, 'type': type})
        return self.get('view?' + q, raw=True)

    def exists(self, filename, subfolder='', type='input'):
        try:
            self.view(filename, subfolder, type)
            return True
        except Exception:
            return False


def png_size(data):
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('not a PNG')
    return struct.unpack('>II', data[16:24])


def png_with_text(png, chunks):
    """Adds tEXt chunks (key -> text) to a PNG, the way ComfyUI stores "prompt" and "workflow"."""
    import zlib
    out = png[:33]  # signature + IHDR
    for k, v in chunks.items():
        data = k.encode('latin1') + b'\0' + v.encode('latin1', 'replace')
        out += struct.pack('>I', len(data)) + b'tEXt' + data + struct.pack('>I', zlib.crc32(b'tEXt' + data) & 0xffffffff)
    return out + png[33:]


def tiny_png(w=8, h=8, rgb=(128, 128, 128)):
    import zlib
    raw = b''.join(b'\0' + bytes(rgb) * w for _ in range(h))
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))
