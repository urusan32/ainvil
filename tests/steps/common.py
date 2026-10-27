"""Shared steps: opening Ainvil, generic clicking/typing/checking, toasts, downloads."""
import base64
import fnmatch
import json
import os
import re
import time

from ainvil_bdd.registry import given, hook, then, when

TEST_PREFIX = 'ainvil-test/e2e'


def lit(s):
    """A table/step value: JSON when it parses (numbers, true, "quoted", [..]), otherwise the text itself."""
    s = s.strip()
    try:
        return json.loads(s)
    except ValueError:
        return s


def scope_of(where):
    if not where:
        return None
    s = re.sub(r'^(?:in|on) ', '', where.strip())
    return s[1:-1] if len(s) > 1 and s[0] == s[-1] == '"' else s


def rows(ctx, header=True):
    t = ctx.step.table or []
    return t[1:] if header else t


# ---------- hooks ----------
@hook('after_scenario')
def after(ctx, status, failure):
    app = ctx.runner._app
    if app is None:
        return
    if status != 'passed':
        name = re.sub(r'[^\w-]+', '_', f'{os.path.basename(ctx.scenario.feature.path)}-{ctx.scenario.line}')
        path = os.path.join(ctx.options.out_dir, name + '.png')
        try:
            app.screenshot(path)
            ctx.screenshot_path = path
        except Exception:
            pass
        return
    if '@js-errors' in ctx.scenario.tags:
        return
    errs = app.errors()
    if errs:
        raise AssertionError('The page had uncaught errors:\n  ' + '\n  '.join(errs))


# ---------- opening the app ----------
@given('Ainvil is open and connected to the test server')
def open_connected(ctx):
    ctx.app.reset()


@given('Ainvil is opened for the first time')
def open_first_time(ctx):
    ctx.app.reset(server=False)


@given('Ainvil is open with the test server configured but no connection yet')
def open_not_connected(ctx):
    ctx.app.reset()


@given('test outputs go to the "ainvil-test" folder')
def test_outputs(ctx):
    # The Filename prefix custom parameters of the built-in workflows, for Generate and Extras.
    ctx.app.js('''
      for (const fw of config.functionalWorkflows) (gen.custom[fw.name] ??= {})['Filename prefix'] = args[0] + '/' + fw.name + '_%date:hhmmss%';
      for (const cw of config.customWorkflows) (ex.values[cw.name] ??= {})['Filename prefix'] = args[0] + '/extras_%input%';
      localStorage.setItem('ainvil.generate', JSON.stringify(gen));
      localStorage.setItem('ainvil.extras', JSON.stringify(ex));
      renderCustomParams(); renderExParams();
    ''', TEST_PREFIX)


@given('the window is {int} × {int} pixels', 'the window is {int} x {int} pixels')
@when('I resize the window to {int} × {int} pixels', 'I resize the window to {int} x {int} pixels')
def window_size(ctx, w, h):
    ctx.app.set_window(w, h)


@when('I reload the page')
@given('I reload the page')
def reload_page(ctx):
    ctx.app.js('await new Promise((r) => setTimeout(r, 400));')  # let the debounced form saves land
    ctx.app.reload()
    ctx.app.wait('document.readyState === "complete"', 10)


@when('I wait until Ainvil is connected')
@then('Ainvil connects to the server')
def wait_connected(ctx):
    ctx.app.wait('(0, window.eval)("connected")', 30, 'Ainvil did not connect')


@given('the {string} tab is open')
@when('I open the {string} tab')
def open_tab(ctx, name):
    ctx.app.js('''
      const b = [...document.querySelectorAll('.tab')].find((x) => x.textContent.trim() === args[0]);
      if (!b) throw new Error('No tab ' + args[0]);
      b.click();
    ''', name)


@then('the {string} tab is shown')
def tab_shown(ctx, name):
    ctx.app.wait(f'''[...document.querySelectorAll('.tab')].find((x) => x.textContent.trim() === args[0])?.classList.contains('active')''',
                 5, f'The {name} tab is not shown', name)


# ---------- clicking and typing ----------
@when('I click {string}')
@given('I click {string}')
def click(ctx, text):
    ctx.app.click(text)


@when('I click {string} {where}')
@given('I click {string} {where}')
def click_in(ctx, text, where):
    ctx.app.click(text, scope_of(where))


@when('I set {string} to {string}')
@given('{string} is set to {string}')
def set_field(ctx, label, value):
    ctx.app.set(label, value)


@when('I set {string} {where} to {string}')
@given('{string} {where} is set to {string}')
def set_field_in(ctx, label, where, value):
    ctx.app.set(label, value, scope_of(where))


@when('I check {string}')
@given('{string} is checked')
def check(ctx, label):
    ctx.app.set(label, True)


@when('I uncheck {string}')
@given('{string} is unchecked')
def uncheck(ctx, label):
    ctx.app.set(label, False)


@when('I check {string} {where}')
def check_in(ctx, label, where):
    ctx.app.set(label, True, scope_of(where))


@when('I uncheck {string} {where}')
def uncheck_in(ctx, label, where):
    ctx.app.set(label, False, scope_of(where))


@when('I select {string} as {string}')
@given('{string} is selected as {string}')
def select(ctx, value, label):
    ctx.app.set(label, value)


@when('I fill in')
@given('the form is filled in with')
@given('I fill in')
def fill_in(ctx):
    # | label | value | (optional) section |
    for r in rows(ctx, header=False):
        ctx.app.set(r[0], r[1], r[2] if len(r) > 2 and r[2] else None)


KEYS = {'esc': 'Escape', 'escape': 'Escape', 'enter': 'Enter', 'space': ' ', 'left': 'ArrowLeft', 'right': 'ArrowRight'}


def press(ctx, combo, target=None):
    parts = combo.split('+') if combo != '+' else ['+']
    key = parts[-1]
    opts = {m.lower() + 'Key': True for m in parts[:-1]}
    if 'controlKey' in opts:
        opts['ctrlKey'] = opts.pop('controlKey')
    key = KEYS.get(key.lower(), key if len(key) > 1 else key.lower() if opts.get('ctrlKey') else key)
    ctx.app.js('__t.key(args[0], args[1], args[2] ? document.querySelector(args[2]) : undefined);', key, opts, target)


@when('I press {word}')
def press_key(ctx, combo):
    press(ctx, combo)


@when('I press {word} in the prompt')
def press_in_prompt(ctx, combo):
    press(ctx, combo, '#prompt')


# ---------- checking what is shown ----------
@then('I see {string}')
def see(ctx, text):
    ctx.app.wait('document.body.innerText.includes(args[0])', 10, f'"{text}" is not on the page', text)


@then('I see {string} {where}')
def see_in(ctx, text, where):
    ctx.app.wait('__t.scope(args[1]).innerText.includes(args[0])', 10, f'"{text}" is not shown {where}', text, scope_of(where))


@then('I don\'t see {string}')
def not_see(ctx, text):
    if ctx.app.ev('document.body.innerText.includes(args[0])', text):
        raise AssertionError(f'"{text}" is on the page')


@then('I don\'t see {string} {where}')
def not_see_in(ctx, text, where):
    if ctx.app.ev('__t.scope(args[1]).innerText.includes(args[0])', text, scope_of(where)):
        raise AssertionError(f'"{text}" is shown {where}')


@then('{string} shows {string}')
def field_shows(ctx, label, value):
    v =ctx.app.js('return await __t.until(() => String(__t.value(args[0])) === args[1], 5000) ? null : String(__t.value(args[0]));', label, value)
    if v is not None:
        raise AssertionError(f'"{label}" shows "{v}", expected "{value}"')


@then('{string} {where} shows {string}')
def field_in_shows(ctx, label, where, value):
    v = ctx.app.js('return await __t.until(() => String(__t.value(args[0], args[2])) === args[1], 5000) ? null : String(__t.value(args[0], args[2]));',
                   label, value, scope_of(where))
    if v is not None:
        raise AssertionError(f'"{label}" {where} shows "{v}", expected "{value}"')


@then('the form shows')
def form_shows(ctx):
    for r in rows(ctx, header=False):
        if len(r) > 2 and r[2]:
            field_in_shows(ctx, r[0], 'in ' + r[2], r[1])
        else:
            field_shows(ctx, r[0], r[1])


@then('{string} is checked')
def is_checked(ctx, label):
    if ctx.app.value(label) is not True:
        raise AssertionError(f'"{label}" is not checked')


@then('{string} is not checked')
def is_unchecked(ctx, label):
    if ctx.app.value(label) is not False:
        raise AssertionError(f'"{label}" is checked')


@then('{string} is disabled')
def field_disabled(ctx, label):
    if not ctx.app.ev('__t.field(args[0]).disabled', label):
        raise AssertionError(f'"{label}" is enabled')


@then('{string} is enabled')
def field_enabled(ctx, label):
    if ctx.app.ev('__t.field(args[0]).disabled', label):
        raise AssertionError(f'"{label}" is disabled')


def _button_state(ctx, text, where, state):
    js = {
        'visible': 'T.visible(b)', 'shown': 'T.visible(b)', 'hidden': '!T.visible(b)',
        'disabled': 'b.disabled', 'enabled': '!b.disabled && T.visible(b)',
    }[state]
    ok = ctx.app.js(f'''
      const T = __t;
      return await T.until(() => {{ const b = T.button(args[0], args[1], {{ any: true }}); return {js}; }}, 5000);
    ''', text, scope_of(where))
    if not ok:
        raise AssertionError(f'The "{text}" button{" " + where if where else ""} is not {state}')


@then('the {string} button is {word}')
def button_state(ctx, text, state):
    _button_state(ctx, text, None, state)


@then('the {string} button {where} is {word}')
def button_state_in(ctx, text, where, state):
    _button_state(ctx, text, where, state)


@then('{string} lists {string}')
def select_lists(ctx, label, option):
    opts = ctx.app.js('return __t.options(__t.field(args[0]));', label)
    if not any(o == option or o.endswith('/' + option) for o in opts):
        raise AssertionError(f'"{label}" does not list "{option}": {opts}')


@then('{string} does not list {string}')
def select_not_lists(ctx, label, option):
    opts = ctx.app.js('return __t.options(__t.field(args[0]));', label)
    if any(option in o for o in opts):
        raise AssertionError(f'"{label}" lists "{option}": {opts}')


@then('{string} lists only')
def select_lists_only(ctx, label):
    want = [r[0] for r in rows(ctx, header=False)]
    opts = ctx.app.js('return __t.options(__t.field(args[0]));', label)
    short = [o.split('/')[-1] for o in opts]
    if short != want and opts != want:
        raise AssertionError(f'"{label}" lists {opts}, expected {want}')


# ---------- toasts ----------
def wait_toast(ctx, text, kind=None, timeout=15):
    found = ctx.app.js('''
      return await __t.until(() => __t.toasts.find((x) => x.text.includes(args[0]) && (!args[1] || x.kind === args[1])), args[2]);
    ''', text, kind, timeout * 1000)
    if not found:
        raise AssertionError(f'No {kind + " " if kind else ""}toast saying "{text}". Toasts: {[t["text"] for t in ctx.app.toasts()]}')


@then('a toast says {string}')
def toast_says(ctx, text):
    wait_toast(ctx, text)


@then('an error toast says {string}')
def error_toast(ctx, text):
    wait_toast(ctx, text, 'error')


@then('no error toast is shown')
def no_error_toast(ctx):
    errs = [t['text'] for t in ctx.app.toasts() if t['kind'] == 'error']
    if errs:
        raise AssertionError(f'Error toasts: {errs}')


# ---------- confirm dialogs ----------
@given('I will answer "Cancel" to the confirmation')
@when('I will answer "Cancel" to the confirmation')
def confirm_cancel(ctx):
    ctx.app.js('__t.confirmAnswer = false;')


@then('I was asked {string}')
def was_asked(ctx, text):
    asked = ctx.app.ev('__t.confirms')
    if not any(text in a for a in asked):
        raise AssertionError(f'No confirmation like "{text}": {asked}')


# ---------- downloads ----------
def downloaded(ctx, pattern):
    for d in reversed(ctx.app.downloads()):
        if fnmatch.fnmatch(d['name'], pattern):
            return d
    raise AssertionError(f'No download named like "{pattern}". Downloads: {[d["name"] for d in ctx.app.downloads()]}')


def download_bytes(ctx, pattern):
    return base64.b64decode(downloaded(ctx, pattern)['b64'])


@then('a file named like {string} is downloaded')
@then('a file named {string} is downloaded')
def file_downloaded(ctx, pattern):
    ctx.vars['download'] = downloaded(ctx, pattern)


@then('nothing is downloaded')
def nothing_downloaded(ctx):
    d = ctx.app.downloads()
    if d:
        raise AssertionError(f'Downloaded: {[x["name"] for x in d]}')


@when('I wait {float} seconds')
def wait_seconds(ctx, s):
    time.sleep(s)


@then('the {string} field is {word}')
def field_visibility(ctx, label, state):
    vis = ctx.app.ev('__t.visible(__t.field(args[0]))', label)
    if vis != (state in ('visible', 'shown')):
        raise AssertionError(f'The "{label}" field is {"visible" if vis else "hidden"}')
