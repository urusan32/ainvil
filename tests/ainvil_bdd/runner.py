"""Runs Gherkin features against Ainvil in headless Firefox."""
import glob
import importlib
import os
import re
import sys
import time
import traceback

from . import gherkin, registry
from .registry import Ambiguous, Undefined

TTY = sys.stdout.isatty()
GREEN, RED, YELLOW, DIM, BOLD, RESET = (('\033[32m', '\033[31m', '\033[33m', '\033[2m', '\033[1m', '\033[0m') if TTY else ('',) * 6)


class Context:
    """What step functions get: the page (`app`), the server (`comfy`), the current step, per-scenario
    variables (`vars`) and run-wide caches (`run`)."""

    def __init__(self, runner):
        self.runner = runner
        self.run = runner.run_cache
        self.vars = {}
        self.scenario = None
        self.step = None

    @property
    def app(self):
        return self.runner.app()

    @property
    def comfy(self):
        return self.runner.comfy

    @property
    def options(self):
        return self.runner.options


def tag_filter(expr):
    """'@a,@b' = any of; '~@c' or 'not @c' excludes; space-separated groups must all match."""
    if not expr:
        return lambda tags: True
    groups = []
    for group in re.split(r'\s+and\s+|\s{2,}|;', expr.strip()):
        if not group.strip():
            continue
        alts = [a.strip() for a in group.split(',') if a.strip()]
        groups.append(alts)

    def ok(tags):
        for alts in groups:
            hit = False
            for a in alts:
                neg = a.startswith('~') or a.startswith('not ')
                t = a[1:] if a.startswith('~') else a[4:] if a.startswith('not ') else a
                if (t in tags) != neg:
                    hit = True
            if not hit:
                return False
        return True
    return ok


class Runner:
    def __init__(self, options, app_factory, comfy):
        self.options = options
        self._app_factory = app_factory
        self._app = None
        self.comfy = comfy
        self.run_cache = {}
        self.results = []

    def app(self):
        if self._app is None:
            self._app = self._app_factory()
        return self._app

    def load(self, paths):
        features = []
        for p in paths:
            line = None
            if re.search(r':\d+$', p):
                p, line = p.rsplit(':', 1)
                line = int(line)
            files = sorted(glob.glob(os.path.join(p, '**', '*.feature'), recursive=True)) if os.path.isdir(p) else [p]
            for f in files:
                feat = gherkin.parse(open(f, encoding='utf-8').read(), os.path.relpath(f))
                if line:
                    feat.scenarios = [s for s in feat.scenarios if s.line == line or (s.example is None and s.line <= line and line < s.line + 1 + len(s.steps))]
                features.append(feat)
        return features

    def selected(self, features):
        want = tag_filter(self.options.tags)
        name = self.options.name.lower() if self.options.name else None
        for f in features:
            for s in f.scenarios:
                if '@wip' in s.tags and not self.options.tags:
                    continue
                if want(s.tags) and (not name or name in (f.name + ' ' + s.name).lower()):
                    yield f, s

    def check_steps(self, pairs):
        problems = []
        for f, s in pairs:
            for st in f.background + getattr(s, 'rule_background', []) + s.steps:
                try:
                    registry.find(st.keyword, st.text)
                except (Undefined, Ambiguous) as e:
                    problems.append(f'{f.path}:{st.line}: {type(e).__name__}: {e}')
        return sorted(set(problems))

    def run(self, features):
        pairs = list(self.selected(features))
        problems = self.check_steps(pairs)
        out = print
        if problems:
            out(f'{RED}Step problems:{RESET}\n  ' + '\n  '.join(problems))
            if not self.options.dry_run:
                return 2
        if self.options.dry_run or self.options.list:
            cur = None
            for f, s in pairs:
                if f is not cur:
                    out(f'{BOLD}{f.name}{RESET} {DIM}({f.path}){RESET}')
                    cur = f
                out(f'  {s.name} {DIM}{" ".join(s.tags)} :{s.line}{RESET}')
            out(f'\n{len(pairs)} scenario(s)')
            return 1 if problems else 0
        start = time.time()
        for hook in registry.HOOKS['before_all']:
            hook(self)
        cur = None
        try:
            for f, s in pairs:
                if f is not cur:
                    out(f'\n{BOLD}Feature: {f.name}{RESET} {DIM}{f.path}{RESET}')
                    cur = f
                self.run_scenario(f, s)
                if self.options.fail_fast and self.results[-1][2] != 'passed':
                    break
        finally:
            for hook in registry.HOOKS['after_all']:
                try:
                    hook(self)
                except Exception:
                    traceback.print_exc()
        return self.summary(time.time() - start)

    def run_scenario(self, f, s):
        ctx = Context(self)
        ctx.scenario = s
        t0 = time.time()
        status, failure = 'passed', None
        steps = f.background + getattr(s, 'rule_background', []) + s.steps
        if TTY:
            print(f'  {s.name} {DIM}:{s.line}{RESET}', end='', flush=True)
        done = []
        try:
            for hook in registry.HOOKS['before_scenario']:
                hook(ctx)
            for st in steps:
                ctx.step = st
                fn, args = registry.find(st.keyword, st.text)
                ts = time.time()
                fn(ctx, *args)
                done.append((st, time.time() - ts))
        except Exception as e:
            status = 'failed'
            failure = (ctx.step, e, traceback.format_exc())
        finally:
            ctx.step = None
            for hook in registry.HOOKS['after_scenario']:
                try:
                    hook(ctx, status, failure)
                except Exception as e:
                    if status == 'passed':
                        status, failure = 'failed', (None, e, traceback.format_exc())
        dt = time.time() - t0
        mark = f'{GREEN}✓{RESET}' if status == 'passed' else f'{RED}✗{RESET}'
        print(('\r' if TTY else '') + f'  {mark} {s.name} {DIM}({dt:.1f} s){RESET}' + (' ' * 10 if TTY else ''), flush=True)
        if self.options.verbose or status != 'passed':
            for st, sdt in done:
                print(f'      {GREEN}{st.raw_keyword} {st.text}{RESET} {DIM}{sdt:.1f} s{RESET}')
        if failure:
            st, e, tb = failure
            if st is not None:
                print(f'      {RED}{st.raw_keyword} {st.text}{RESET}  {DIM}{f.path}:{st.line}{RESET}')
            print(f'        {RED}{type(e).__name__}: {e}{RESET}'.replace('\n', '\n        '))
            if self.options.verbose:
                print(DIM + tb + RESET)
            shot = getattr(ctx, 'screenshot_path', None)
            if shot:
                print(f'        {DIM}screenshot: {shot}{RESET}')
        self.results.append((f, s, status, dt, failure))

    def summary(self, dt):
        passed = sum(1 for r in self.results if r[2] == 'passed')
        failed = [r for r in self.results if r[2] != 'passed']
        print(f'\n{BOLD}{len(self.results)} scenario(s): {GREEN}{passed} passed{RESET}' +
              (f', {RED}{len(failed)} failed{RESET}' if failed else '') + f' {DIM}in {dt / 60:.1f} min{RESET}')
        for f, s, _, _, fail in failed:
            print(f'  {RED}✗{RESET} {f.path}:{s.line} {s.name}')
        return 1 if failed else 0


def load_steps(dirname):
    sys.path.insert(0, os.path.dirname(dirname))
    for p in sorted(glob.glob(os.path.join(dirname, '*.py'))):
        name = os.path.splitext(os.path.basename(p))[0]
        if name != '__init__':
            importlib.import_module(f'{os.path.basename(dirname)}.{name}')
