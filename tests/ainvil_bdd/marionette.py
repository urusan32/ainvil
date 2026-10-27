"""A minimal Marionette client (Firefox's remote protocol) over a raw socket, Python stdlib only.

Marionette frames are `<byte length>:<json>`. Commands are [0, id, name, params] and replies are
[1, id, error, result].
"""
import json
import os
import socket
import subprocess
import time


class MarionetteError(Exception):
    pass


class Marionette:
    # `profile` is reused between runs (nothing is deleted); the tests reset the page's storage themselves.
    def __init__(self, profile, firefox='firefox', headless=True, width=1600, height=1000, system_access=False):
        self.profile = profile
        os.makedirs(profile, exist_ok=True)
        self.port = _free_port()
        with open(os.path.join(self.profile, 'user.js'), 'w') as f:
            for k, v in {
                'marionette.port': self.port,
                'browser.shell.checkDefaultBrowser': False,
                'browser.startup.homepage_override.mstone': 'ignore',
                'datareporting.policy.dataSubmissionEnabled': False,
                'toolkit.telemetry.reportingpolicy.firstRun': False,
                'browser.aboutwelcome.enabled': False,
                'dom.disable_beforeunload': True,
                # file:// pages may keep localStorage and IndexedDB like any other origin.
                'dom.storage.enabled': True,
                'browser.download.useDownloadDir': True,
                'browser.download.dir': os.path.join(self.profile, 'downloads'),
                'browser.download.folderList': 2,
            }.items():
                f.write(f'user_pref({json.dumps(k)}, {json.dumps(v)});\n')
        args = [firefox, '-marionette', '-no-remote', '-profile', self.profile]
        if headless:
            args.append('-headless')
        if system_access:
            args.append('-remote-allow-system-access')
        env = dict(os.environ, MOZ_HEADLESS_WIDTH=str(width), MOZ_HEADLESS_HEIGHT=str(height))
        self.proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
        self.sock = self._connect()
        self._buf = b''
        self._id = 0
        self._recv()  # handshake: {"applicationType": "gecko", "marionetteProtocol": 3}
        self.command('WebDriver:NewSession', {'capabilities': {'alwaysMatch': {'acceptInsecureCerts': True}}})
        self.command('WebDriver:SetTimeouts', {'script': 300000, 'pageLoad': 60000, 'implicit': 0})
        self.command('WebDriver:SetWindowRect', {'width': width, 'height': height})

    def _connect(self, timeout=60):
        end = time.time() + timeout
        while time.time() < end:
            if self.proc.poll() is not None:
                raise MarionetteError('Firefox exited during startup')
            try:
                return socket.create_connection(('127.0.0.1', self.port), timeout=5)
            except OSError:
                time.sleep(0.2)
        raise MarionetteError('Could not connect to Marionette')

    def _recv(self):
        while b':' not in self._buf:
            self._read()
        n, rest = self._buf.split(b':', 1)
        n = int(n)
        while len(rest) < n:
            chunk = self.sock.recv(1 << 20)
            if not chunk:
                raise MarionetteError('Marionette connection closed')
            rest += chunk
        self._buf = rest[n:]
        return json.loads(rest[:n])

    def _read(self):
        chunk = self.sock.recv(1 << 20)
        if not chunk:
            raise MarionetteError('Marionette connection closed')
        self._buf += chunk

    def command(self, name, params=None, timeout=330):
        self._id += 1
        data = json.dumps([0, self._id, name, params or {}]).encode()
        self.sock.settimeout(timeout)
        self.sock.sendall(str(len(data)).encode() + b':' + data)
        while True:
            msg = self._recv()
            if msg[0] == 1 and msg[1] == self._id:
                break
        if msg[2]:
            err = msg[2]
            raise MarionetteError(f"{err.get('error')}: {err.get('message')}\n{err.get('stacktrace', '')}".strip())
        r = msg[3]
        return r.get('value', r) if isinstance(r, dict) else r

    def navigate(self, url):
        self.command('WebDriver:Navigate', {'url': url})

    def execute(self, script, args=None, timeout=330):
        return self.command('WebDriver:ExecuteScript', {'script': script, 'args': args or []}, timeout=timeout)

    def set_context(self, context):
        self.command('Marionette:SetContext', {'value': context})

    def screenshot(self):
        return self.command('WebDriver:TakeScreenshot', {'full': True})

    def quit(self):
        try:
            self.command('Marionette:Quit', {'flags': ['eForceQuit']}, timeout=10)
        except Exception:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def _free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port
