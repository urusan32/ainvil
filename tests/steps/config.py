"""Configuration tab steps: connection, import/export, preferences, functional and custom workflow editing."""
import json
import os

from ainvil_bdd.comfy import png_with_text, tiny_png
from ainvil_bdd.registry import given, then, when
from steps.common import download_bytes, lit, rows

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORKFLOWS = os.path.join(ROOT, 'workflows')
FIXTURES = os.path.join(ROOT, 'tests', 'fixtures')


# ---------- connection ----------
@when('I set "ComfyUI API URL" to the test server address')
def set_test_url(ctx):
    ctx.app.set('ComfyUI API URL', ctx.app.server_url)


@when('I set "ComfyUI API URL" to the test server address without "http://"')
def set_test_url_bare(ctx):
    ctx.app.set('ComfyUI API URL', ctx.app.server_url.replace('http://', '').rstrip('/'))


@then('"ComfyUI API URL" shows the test server address')
def shows_test_url(ctx):
    v = ctx.app.value('ComfyUI API URL')
    if v != ctx.app.server_url:
        raise AssertionError(f'"ComfyUI API URL" shows {v}')


@then('the connection result says {string}')
def conn_result(ctx, text):
    ctx.app.wait('document.querySelector("#connResult").textContent.includes(args[0])', 30,
                 lambda: f'Connection result does not say "{text}": {ctx.app.ev("document.querySelector(`#connResult`).textContent")}', text)


@then('the connection result is an error saying {string}')
def conn_error(ctx, text):
    conn_result(ctx, text)
    if 'error' not in ctx.app.ev('document.querySelector("#connResult").className'):
        raise AssertionError('The connection result is not shown as an error')


@then('the header shows the server version and host')
def header_conn(ctx):
    host = ctx.app.server_url.split('//')[1].rstrip('/')
    version = ctx.comfy.get('system_stats')['system']['comfyui_version']
    ctx.app.wait('document.querySelector("#connStatus").textContent === args[0]', 15,
                 lambda: f'Header status is "{ctx.app.ev("document.querySelector(`#connStatus`).textContent")}"', f'ComfyUI {version} · {host}')


@then('the header says {string}')
def header_says(ctx, text):
    ctx.app.wait('document.querySelector("#connStatus").textContent === args[0]', 15, f'Header does not say "{text}"', text)


@when('I click the connection status in the header')
def click_conn(ctx):
    ctx.app.js('document.querySelector("#connStatus").click();')


# ---------- stored configuration ----------
def js_path(path):
    """'functionalWorkflows[0].name' -> JS accessor suffix."""
    return ''.join(f'[{p}]' if p.isdigit() else f'[{json.dumps(p)}]' for p in path.replace('[', '.').replace(']', '').split('.') if p)


@given('the configuration has {string} set to {any}')
def config_set(ctx, path, value):
    # Let the debounced form saves land first, so the form survives the reload.
    ctx.app.js(f'config{js_path(path)} = args[0]; saveConfig(); await new Promise((r) => setTimeout(r, 400));', lit(value))
    ctx.app.reload()
    ctx.app.wait('(0, window.eval)("connected")', 30)


@given('the stored configuration is')
def stored_config(ctx):
    ctx.app.js('localStorage.setItem("ainvil.config", args[0]);', ctx.step.doc)
    ctx.app.reload()


@then('the configuration has {string} = {any}')
def config_is(ctx, path, value):
    got = ctx.app.ev(f'(0, window.eval)("config"){js_path(path)}')
    if got != lit(value):
        raise AssertionError(f'config.{path} is {got!r}')


@then('the saved configuration has {string} = {any}')
def saved_config_is(ctx, path, value):
    got = ctx.app.ev(f'JSON.parse(localStorage.getItem("ainvil.config")){js_path(path)}')
    if got != lit(value):
        raise AssertionError(f'Saved config.{path} is {got!r}')


def get_path(obj, path):
    for p in path.replace('[', '.').replace(']', '').split('.'):
        if not p:
            continue
        obj = obj[int(p)] if isinstance(obj, list) else obj[p]
    return obj


@then('the downloaded file {string} has')
def download_has(ctx, pattern):
    data = json.loads(download_bytes(ctx, pattern))
    for path, value in rows(ctx):
        try:
            got = get_path(data, path)
        except (KeyError, IndexError, TypeError):
            raise AssertionError(f'{pattern} has no {path}')
        want = lit(value)
        if want == '<object>':
            ok = isinstance(got, dict)
        elif want == '<absent>':
            ok = False
        else:
            ok = got == want
        if not ok:
            raise AssertionError(f'{path} is {json.dumps(got)[:200]}, expected {value}')


# ---------- import ----------
def stage_file(ctx, name, text, how='drop'):
    spec = {'text': text, 'name': name, 'type': 'application/json'}
    if how == 'drop':
        ctx.app.js('__t.drop(document.querySelector("#importBox"), await __t.files([args[0]]));', spec)
    else:
        ctx.app.js('__t.nextFiles.push(await __t.files([args[0]]));', spec)
        ctx.app.click('choose a file', 'Global Import & Export')
    ctx.app.wait('!document.querySelector("#btnImport").disabled', 5, 'The import button did not enable')


@when('I drop the downloaded {string} on the import box')
def drop_download(ctx, pattern):
    stage_file(ctx, pattern.replace('*', 'x'), download_bytes(ctx, pattern).decode())


@when('I choose the downloaded {string} with "choose a file"')
def choose_download(ctx, pattern):
    stage_file(ctx, pattern.replace('*', 'x'), download_bytes(ctx, pattern).decode(), how='pick')


@when('I drop a file {string} on the import box containing')
def drop_import_doc(ctx, name):
    stage_file(ctx, name, ctx.step.doc)


@when('I drop the workflow file {string} on the import box')
def drop_workflow_import(ctx, name):
    stage_file(ctx, name, open(fixture_path(name)).read())


@then('the import box shows {string}')
def import_box_shows(ctx, text):
    ctx.app.wait('document.querySelector("#importFileName").textContent.includes(args[0])', 5,
                 lambda: f'Import box: {ctx.app.ev("document.querySelector(`#importFileName`).textContent")}', text)


@then('the import error says {string}')
def import_error(ctx, text):
    ctx.app.wait('!document.querySelector("#importError").hidden && document.querySelector("#importError").textContent.includes(args[0])', 10,
                 lambda: f'Import error: {ctx.app.ev("document.querySelector(`#importError`).textContent")!r}', text)


@then('the import error box is hidden')
def import_error_hidden(ctx):
    if not ctx.app.ev('document.querySelector("#importError").hidden'):
        raise AssertionError('The import error is shown')


def fixture_path(name):
    for d in (FIXTURES, WORKFLOWS):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    raise AssertionError(f'No fixture {name}')


# ---------- workflow sections ----------
@when('I expand {string}')
@given('{string} is expanded')
def expand(ctx, scope):
    ctx.app.js('const d = __t.scope(args[0]); if (d.tagName !== "DETAILS") throw new Error(args[0] + " is not collapsible"); d.open = true;', scope)


@when('I collapse {string}')
def collapse(ctx, scope):
    ctx.app.js('__t.scope(args[0]).open = false;', scope)


@then('{string} is expanded')
def is_expanded(ctx, scope):
    if not ctx.app.ev('__t.scope(args[0]).open', scope):
        raise AssertionError(f'{scope} is collapsed')


@then('the functional workflows are')
def fw_list(ctx):
    want = [r for r in rows(ctx)]
    got = ctx.app.ev('''[...document.querySelectorAll("#fwList > details > summary")].map((s) => [s.firstChild.firstChild.textContent, s.querySelector(".sub").textContent])''')
    if got != want:
        raise AssertionError(f'Functional workflows: {got}')


@then('the custom workflows are')
def cw_list(ctx):
    want = [r for r in rows(ctx)]
    got = ctx.app.ev('''[...document.querySelectorAll("#cwList > details > summary")].map((s) => [s.firstChild.firstChild.textContent, s.querySelector(".sub").textContent])''')
    if got != want:
        raise AssertionError(f'Custom workflows: {got}')


@then('{string} says {string}')
def section_summary(ctx, scope, text):
    got = ctx.app.ev('__t.norm(__t.scope(args[0]).querySelector("summary").textContent)', scope)
    if text not in got:
        raise AssertionError(f'{scope} says "{got}"')


@when('I load the workflow file {string} into {string}')
def load_wf_file(ctx, name, scope):
    p = fixture_path(name)
    if name.endswith('.png'):
        spec = {'b64': __import__('base64').b64encode(open(p, 'rb').read()).decode(), 'name': name, 'type': 'image/png'}
    else:
        spec = {'text': open(p).read(), 'name': name, 'type': 'application/json'}
    _load_wf(ctx, spec, scope)


def _load_wf(ctx, spec, scope):
    ctx.app.js('''
      __t.nextFiles.push(await __t.files([args[0]]));
      const root = __t.scope(args[1]);
      const b = [...root.querySelectorAll("button")].find((x) => /^(Load|Replace) workflow…$/.test(x.textContent) && x.closest("details") === root);
      if (!b) throw new Error("No Load workflow button in " + args[1]);
      b.click();
    ''', spec, scope)
    ctx.app.js('await new Promise((r) => setTimeout(r, 300));')


@when('I load a PNG with an embedded copy of {string} into {string}')
def load_wf_png(ctx, name, scope):
    import base64
    png = png_with_text(tiny_png(), {'workflow': open(fixture_path(name)).read()})
    _load_wf(ctx, {'b64': base64.b64encode(png).decode(), 'name': 'with-workflow.png', 'type': 'image/png'}, scope)


@when('I load a PNG without a workflow into {string}')
def load_plain_png(ctx, scope):
    import base64
    _load_wf(ctx, {'b64': base64.b64encode(tiny_png()).decode(), 'name': 'plain.png', 'type': 'image/png'}, scope)


@when('I load a file {string} into {string} containing')
def load_wf_doc(ctx, name, scope):
    _load_wf(ctx, {'text': ctx.step.doc, 'name': name, 'type': 'application/json'}, scope)


@then('{string} shows the error {string}')
def scope_error(ctx, scope, text):
    ctx.app.wait('[...__t.scope(args[0]).querySelectorAll("pre.errorbox")].some((e) => !e.hidden && e.textContent.includes(args[1]))', 10,
                 f'No error "{text}" in {scope}', scope, text)


@then('the {word} mappings of {string} are')
def mappings_are(ctx, mode, fw):
    want = {r[0]: r[1] for r in rows(ctx)}
    got = ctx.app.ev('(0, window.eval)("config").functionalWorkflows.find((f) => f.name === args[0]).workflows[args[1]].mappings', fw, mode)
    flat = {k: ', '.join(f"{t['node']}.{t['input']}" if t.get('input') else t['node'] for t in v) for k, v in got.items() if v}
    if flat != want:
        extra = {k: v for k, v in flat.items() if want.get(k) != v}
        missing = {k: v for k, v in want.items() if flat.get(k) != v}
        raise AssertionError(f'Mappings differ.\n  got: {extra}\n  expected: {missing}')


def map_row(scope, label):
    return f'''(() => {{
      const root = __t.scope({json.dumps(scope)});
      const tr = [...root.querySelectorAll("table.map tr")].find((r) => __t.norm(r.cells[0].firstChild.textContent) === {json.dumps(label)} && r.closest("details") === root);
      if (!tr) throw new Error("No mapping row {label}");
      return tr;
    }})()'''


@when('I remove the {string} mapping target in {string}')
def remove_target(ctx, label, scope):
    ctx.app.js(f'{map_row(scope, label)}.querySelector(".target button.danger").click();')


@when('I map {string} in {string} to node {string} input {string}')
def map_target(ctx, label, scope, nid, inp):
    ctx.app.js(f'''
      let tr = {map_row(scope, label)};
      [...tr.querySelectorAll("button")].find((b) => b.textContent === "+ target").click();
      tr = {map_row(scope, label)};
      const t = [...tr.querySelectorAll(".target")].pop(), [ns, is] = t.querySelectorAll("select");
      __t.set(ns, args[0]);
      if (args[1]) {{
        const t2 = [...{map_row(scope, label)}.querySelectorAll(".target")].pop();
        __t.set(t2.querySelectorAll("select")[1], args[1]);
      }}
    ''', nid, inp)


@then('the {string} mapping in {string} shows {string}')
def map_shows(ctx, label, scope, text):
    got = ctx.app.ev(f'''[...{map_row(scope, label)}.querySelectorAll(".target")].map((t) => [...t.querySelectorAll("select")].map((s) => s.selectedOptions[0]?.textContent).join(" / ")).join("; ")''')
    if got != text:
        raise AssertionError(f'{label} mapping shows "{got}"')


@then('the mapping node choices in {string} include {string}')
def node_choices(ctx, scope, text):
    opts = ctx.app.ev(f'[...{map_row(scope, "Seed")}.querySelector("select").options].map((o) => o.textContent)')
    if text not in opts:
        raise AssertionError(f'Node choices: {opts}')


@when('I set parameter {int} of {string} to')
def param_card(ctx, n, scope):
    # | field label | value |
    for r in rows(ctx, header=False):
        ctx.app.js('''
          const card = __t.scope(args[0]).querySelectorAll(".param-card")[args[1] - 1];
          if (!card) throw new Error("No parameter card " + args[1]);
          const l = [...card.querySelectorAll(".fields > label")].find((x) => __t.norm([...x.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join(" ")) === args[2]);
          if (!l) throw new Error("No field " + args[2]);
          __t.set(l.querySelector("input, select"), args[3]);
        ''', scope, n, r[0], r[1])


@when('I map parameter {int} of {string} for {word} to node {string} input {string}')
def param_map_mode(ctx, n, scope, mode, nid, inp):
    ctx.app.js('''
      const card = () => __t.scope(args[0]).querySelectorAll(".param-card")[args[1] - 1];
      const row = () => [...card().querySelectorAll("table.map tr")].find((r) => r.cells[0].textContent === args[2]);
      [...row().querySelectorAll("button")].find((b) => b.textContent === "+ target").click();
      __t.set([...row().querySelectorAll(".target")].pop().querySelectorAll("select")[0], args[3]);
      __t.set([...row().querySelectorAll(".target")].pop().querySelectorAll("select")[1], args[4]);
    ''', scope, n, mode, nid, inp)


@when('I map parameter {int} of {string} to node {string} input {string}')
def param_map(ctx, n, scope, nid, inp):
    ctx.app.js('''
      const card = () => __t.scope(args[0]).querySelectorAll(".param-card")[args[1] - 1];
      [...card().querySelectorAll("button")].find((b) => b.textContent === "+ target").click();
      __t.set([...card().querySelectorAll(".target")].pop().querySelectorAll("select")[0], args[2]);
      __t.set([...card().querySelectorAll(".target")].pop().querySelectorAll("select")[1], args[3]);
    ''', scope, n, nid, inp)


@then('parameter {int} of {string} shows the fields')
def param_fields(ctx, n, scope):
    want = [r[0] for r in rows(ctx, header=False)]
    got = ctx.app.ev('''[...__t.scope(args[0]).querySelectorAll(".param-card")[args[1] - 1].querySelectorAll(".fields > label")].filter((l) => !l.hidden)
                        .map((l) => __t.norm([...l.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join(" ")))''', scope, n)
    if got != want:
        raise AssertionError(f'Fields: {got}')


@when('I import the functional workflow file from the downloaded {string}')
def import_fw_download(ctx, pattern):
    ctx.app.js('__t.nextFiles.push(await __t.files([args[0]]));', {'text': download_bytes(ctx, pattern).decode(), 'name': 'fw.json', 'type': 'application/json'})
    ctx.app.click('Import functional workflow…')


@when('I import the custom workflow file from the downloaded {string}')
def import_cw_download(ctx, pattern):
    ctx.app.js('__t.nextFiles.push(await __t.files([args[0]]));', {'text': download_bytes(ctx, pattern).decode(), 'name': 'cw.json', 'type': 'application/json'})
    ctx.app.click('Import custom workflow…')


@when('I import a {word} workflow file {string} containing')
def import_item_doc(ctx, kind, name):
    ctx.app.js('__t.nextFiles.push(await __t.files([args[0]]));', {'text': ctx.step.doc, 'name': name, 'type': 'application/json'})
    ctx.app.click('Import functional workflow…' if kind == 'functional' else 'Import custom workflow…')


@then('the {word} workflow import error says {string}')
def item_import_error(ctx, kind, text):
    sel = '#fwImportError' if kind == 'functional' else '#cwImportError'
    ctx.app.wait(f'!document.querySelector("{sel}").hidden && document.querySelector("{sel}").textContent.includes(args[0])', 10,
                 lambda: f'{kind} import error: {ctx.app.ev(f"document.querySelector(`{sel}`).textContent")!r}', text)


# ---------- preferences ----------
@then('the gallery thumbnails are laid out {int} per row and {int} rows high')
def gallery_layout(ctx, cols, rows_):
    got = ctx.app.ev('["#galleryThumbs", "#exThumbs"].map((s) => [document.querySelector(s).style.getPropertyValue("--cols"), document.querySelector(s).style.getPropertyValue("--rows")])')
    if got != [[str(cols), str(rows_)]] * 2:
        raise AssertionError(f'Thumbnail layout: {got}')


@then('{string} lists the server\'s {word} {word} options')
def lists_server_options(ctx, label, cls, inp):
    opts = ctx.app.js('return [...__t.field(args[0]).options].map((o) => o.value);', label)
    server = ctx.comfy.options(cls, inp)
    if [o for o in opts if o] != server:
        raise AssertionError(f'"{label}" lists {opts}, the server has {server}')


@when('I remove parameter {int} of {string}')
def remove_param(ctx, n, scope):
    ctx.app.js('''
      const card = __t.scope(args[0]).querySelectorAll(".param-card")[args[1] - 1];
      [...card.querySelectorAll("button")].find((b) => b.textContent === "Remove parameter").click();
    ''', scope, n)


@when('I rename {string} to {string}')
def rename(ctx, scope, name):
    ctx.app.js('''
      const d = __t.scope(args[0]);
      const l = [...d.querySelectorAll(":scope > .fields > label")].find((x) => x.firstChild.textContent === "Name");
      __t.set(l.querySelector("input"), args[1]);
    ''', scope, name)
