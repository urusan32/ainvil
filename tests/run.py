#!/usr/bin/env python3
"""Ainvil end-to-end tests: Gherkin features in tests/features, run in headless Firefox (Marionette) against a
real ComfyUI server. Python stdlib only.

  python3 tests/run.py                          # everything
  python3 tests/run.py --tags '~@gpu'           # only scenarios that don't run generations on the server
  python3 tests/run.py tests/features/stash.feature:12
  python3 tests/run.py -k "focused" --coverage  # by name, with function coverage of index.html
  python3 tests/run.py --dry-run                # check that every step has a definition
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from ainvil_bdd.app import App  # noqa: E402
from ainvil_bdd.comfy import Comfy  # noqa: E402
from ainvil_bdd.coverage import Coverage  # noqa: E402
from ainvil_bdd.runner import Runner, load_steps  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('paths', nargs='*', help='feature files or directories (file.feature:LINE runs one scenario)')
    ap.add_argument('--server', default=os.environ.get('AINVIL_TEST_SERVER', 'http://10.0.0.137:8188/'),
                    help='ComfyUI server to test against (env AINVIL_TEST_SERVER)')
    ap.add_argument('-t', '--tags', help="tag filter: '@a,@b' any of, '~@c' not, ';' between groups that must all match")
    ap.add_argument('-k', '--name', help='only scenarios whose feature or scenario name contains this text')
    ap.add_argument('--headed', action='store_true', help='show the Firefox window')
    ap.add_argument('--coverage', action='store_true', help='report which functions of index.html the run called')
    ap.add_argument('--dry-run', action='store_true', help='list the scenarios and check their steps without running')
    ap.add_argument('--list', action='store_true', help='list the selected scenarios')
    ap.add_argument('-x', '--fail-fast', action='store_true', help='stop at the first failure')
    ap.add_argument('-v', '--verbose', action='store_true', help='print every step and full tracebacks')
    opts = ap.parse_args()

    out_dir = os.path.join(HERE, '.out')
    os.makedirs(out_dir, exist_ok=True)
    opts.out_dir = out_dir
    page = os.path.join(ROOT, 'index.html')
    cov = Coverage(page, os.path.join(out_dir, 'coverage')) if opts.coverage else None
    page_url = 'file://' + (cov.path if cov else page)

    def make_app():
        return App(page_url, opts.server, os.path.join(out_dir, 'firefox-profile'), headless=not opts.headed, coverage=cov)

    load_steps(os.path.join(HERE, 'steps'))
    runner = Runner(opts, make_app, Comfy(opts.server))
    features = runner.load(opts.paths or [os.path.join(HERE, 'features')])
    try:
        code = runner.run(features)
    finally:
        if runner._app:
            runner._app.close()
    if cov and not (opts.dry_run or opts.list):
        cov.report(print)
    return code


if __name__ == '__main__':
    sys.exit(main())
