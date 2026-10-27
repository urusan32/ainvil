"""The Ainvil page under test, driven through Marionette."""
import base64
import json
import os
import time

from .marionette import Marionette, MarionetteError

HERE = os.path.dirname(os.path.abspath(__file__))
HELPERS = open(os.path.join(HERE, 'page_helpers.js')).read()

# Runs `code` as the body of an async function in the page's global scope, so the app's top-level
# let/const bindings (gen, config, input, …) are visible. Marionette waits for the returned promise.
_RUNNER = '''
const [code, args] = arguments;
return (0, window.eval)('(async (...args) => {\\n' + code + '\\n})')(...args);
'''


class App:
    def __init__(self, page_url, server_url, profile, headless=True, width=1600, height=1000, coverage=None):
        self.page_url = page_url
        self.server_url = server_url
        self.coverage = coverage
        self.size = (width, height)
        self.m = Marionette(profile, headless=headless, width=width, height=height)

    def close(self):
        self.harvest_coverage()
        self.m.quit()

    # ---------- JavaScript ----------
    def js(self, code, *args, timeout=330):
        try:
            return self.m.execute(_RUNNER, [code, list(args)], timeout=timeout)
        except MarionetteError as e:
            msg = str(e)
            first = msg.split('\n')[0]
            raise AssertionError('In the page: ' + first.replace('javascript error: ', '')) from None

    def ev(self, expr, *args):
        """Evaluates a JavaScript expression in the page (args are available as args[0], …)."""
        return self.js('return (' + expr + ');', *args)

    def wait(self, expr, timeout=30, message=None, *args):
        """Waits until the expression is truthy and returns its value."""
        v = self.js(f'const v = await __t.until(async () => ({expr}), {int(timeout * 1000)}); return v instanceof Node || v instanceof Window ? true : v;',
                    *args, timeout=timeout + 60)
        if not v:
            if callable(message):
                message = message()
            raise AssertionError(message or f'Timed out after {timeout} s waiting for: {expr}')
        return v

    # ---------- page lifecycle ----------
    def harvest_coverage(self):
        if not self.coverage:
            return
        try:
            hits = self.m.execute('return (0, window.eval)("window.__cov || null")')
        except Exception:
            return
        if hits:
            self.coverage.add(hits)

    def navigate(self):
        self.harvest_coverage()
        self.m.navigate(self.page_url)
        self.install_helpers()

    def reload(self):
        self.harvest_coverage()
        self.m.command('WebDriver:Refresh')
        self.install_helpers()

    def install_helpers(self):
        self.m.execute('(0, window.eval)(arguments[0]);', [HELPERS])

    def reset(self, *, server=True, window=None):
        """A fresh Ainvil: empty localStorage and Image Stash, default configuration pointed at the test server."""
        w, h = window or self.size
        if (w, h) != self.current_size():
            self.m.command('WebDriver:SetWindowRect', {'width': w, 'height': h})
        self.navigate()
        self.js('''
          localStorage.clear();
          await new Promise((resolve) => {
            const r = indexedDB.deleteDatabase('ainvil-stash');
            r.onsuccess = r.onerror = r.onblocked = () => resolve();
          });
          if (args[0]) {
            const c = defaultConfig();
            c.connection.apiUrl = args[0];
            localStorage.setItem('ainvil.config', JSON.stringify(c));
          }
        ''', self.server_url if server else None)
        self.reload()
        if server:
            self.wait('(0, window.eval)("connected")', 30, 'Ainvil did not connect to the test server')

    def current_size(self):
        r = self.m.command('WebDriver:GetWindowRect')
        return (r['width'], r['height'])

    def set_window(self, w, h):
        self.m.command('WebDriver:SetWindowRect', {'width': w, 'height': h})
        self.wait(f'window.innerWidth <= {w}', 10)
        self.js('window.dispatchEvent(new Event("resize"));')

    def screenshot(self, path):
        data = self.m.screenshot()
        with open(path, 'wb') as f:
            f.write(base64.b64decode(data))

    def mouse_drag(self, points, button=0):
        """A real mouse drag (WebDriver actions) through viewport points [(x, y), …]."""
        acts = [{'type': 'pointerMove', 'duration': 0, 'x': int(points[0][0]), 'y': int(points[0][1]), 'origin': 'viewport'},
                {'type': 'pointerDown', 'button': button}]
        for x, y in points[1:]:
            acts.append({'type': 'pointerMove', 'duration': 150, 'x': int(x), 'y': int(y), 'origin': 'viewport'})
        acts.append({'type': 'pointerUp', 'button': button})
        self.m.command('WebDriver:PerformActions', {'actions': [{'type': 'pointer', 'id': 'mouse', 'parameters': {'pointerType': 'mouse'}, 'actions': acts}]})
        self.m.command('WebDriver:ReleaseActions')

    # ---------- user-level helpers ----------
    def click(self, text, scope=None):
        self.js('__t.click(args[0], args[1]);', text, scope)

    def set(self, label, value, scope=None):
        self.js('__t.set(args[0], args[1], args[2]);', label, value, scope)

    def value(self, label, scope=None):
        return self.js('return __t.value(args[0], args[1]);', label, scope)

    def downloads(self):
        self.js('await __t.settle();')
        return self.ev('__t.downloads.map(({href, ...d}) => d)')

    def last_download(self, name_like=None):
        d = self.downloads()
        if name_like:
            d = [x for x in d if name_like in x['name']]
        if not d:
            raise AssertionError('Nothing was downloaded' + (f' named like "{name_like}"' if name_like else ''))
        return d[-1]

    def download_json(self, name_like=None):
        d = self.last_download(name_like)
        return json.loads(base64.b64decode(d['b64']).decode())

    def toasts(self):
        return self.ev('__t.toasts')

    def errors(self):
        return self.ev('__t.errors')


def wait_py(fn, timeout=30, interval=0.3, message='condition'):
    end = time.time() + timeout
    while True:
        v = fn()
        if v:
            return v
        if time.time() > end:
            raise AssertionError(f'Timed out waiting for {message}')
        time.sleep(interval)
