"""Generate tab steps: the form, the workflow Ainvil builds, generation runs and jobs."""
import json
import re
import time

from ainvil_bdd.registry import given, then, when
from steps.common import TEST_PREFIX, download_bytes, downloaded, lit, rows

GEN_TIMEOUT = 600   # seconds; the shared server may be busy with other work


# ---------- form state ----------
@then('the mode is {word}')
def mode_is(ctx, mode):
    ctx.app.wait('document.querySelector("#modeBadge").textContent === args[0]', 10,
                 lambda: f'Mode is {ctx.app.ev("document.querySelector(`#modeBadge`).textContent")}, expected {mode}', mode)


@then('the resolution buttons {string} and {string} are selected')
def res_buttons(ctx, profile, ratio):
    on = ctx.app.ev('[...document.querySelectorAll("#resProfiles button.on, #resRatios button.on")].map((b) => b.textContent)')
    if on != [profile, ratio]:
        raise AssertionError(f'Selected resolution buttons: {on}')


@then('only the resolution button {string} is selected')
def res_custom(ctx, name):
    on = ctx.app.ev('[...document.querySelectorAll("#resProfiles button.on, #resRatios button.on")].map((b) => b.textContent)')
    if on != [name]:
        raise AssertionError(f'Selected resolution buttons: {on}')


@then('the denoise slider is at {int} of {int}')
def slider(ctx, v, mx):
    got = ctx.app.ev('[Number(document.querySelector("#denoiseSlider").value), Number(document.querySelector("#denoiseSlider").max)]')
    if got != [v, mx]:
        raise AssertionError(f'Slider at {got[0]} of {got[1]}')


@when('I move the denoise slider to {int}')
def move_slider(ctx, v):
    ctx.app.js('const s = document.querySelector("#denoiseSlider"); s.value = args[0]; s.dispatchEvent(new Event("input", {bubbles: true}));', v)


@when('I type {string} into the model search')
def model_search(ctx, q):
    ctx.app.set('Search', q, 'Main')


@then('the model list is')
def model_list(ctx):
    want = [r[0] for r in rows(ctx, header=False)]
    got = ctx.app.ev('[...document.querySelectorAll("#modelSelect option")].map((o) => o.textContent)')
    if got != want:
        raise AssertionError(f'Model list: {got}')


@then('the model list has {int} entries')
def model_count(ctx, n):
    got = ctx.app.ev('document.querySelectorAll("#modelSelect option").length')
    if got != n:
        raise AssertionError(f'The model list has {got} entries')


@then('the custom parameters are')
def custom_params(ctx):
    want = [r[0] for r in rows(ctx, header=False)]
    got = ctx.app.ev('[...document.querySelectorAll("#customParams > label")].map((l) => __t.norm(l.firstChild.textContent || l.textContent))')
    if got != want:
        raise AssertionError(f'Custom parameters: {got}')


@then('the CADS section says {string}')
def cads_says(ctx, text):
    ctx.app.wait('document.querySelector("#cadsStatus").textContent.includes(args[0])', 5,
                 lambda: f'CADS status: "{ctx.app.ev("document.querySelector(`#cadsStatus`).textContent")}"', text)


@then('the CADS section has no message')
def cads_no_msg(ctx):
    t = ctx.app.ev('document.querySelector("#cadsStatus").textContent')
    if t:
        raise AssertionError(f'CADS status: "{t}"')


@given('CADS is supported by the server')
def cads_supported(ctx):
    ctx.app.js('document.querySelector("#cfgCads").checked = true; document.querySelector("#cfgCads").dispatchEvent(new Event("change"));')


@given('live preview is enabled')
def live_on(ctx):
    ctx.app.js('const c = document.querySelector("#cfgLivePreview"); c.checked = true; c.dispatchEvent(new Event("change"));')


@then('the input parameters hint says {string}')
def inparams_hint(ctx, text):
    ctx.app.wait('document.querySelector("#inparamsHint").textContent.includes(args[0])', 5,
                 lambda: f'Hint: "{ctx.app.ev("document.querySelector(`#inparamsHint`).textContent")}"', text)


@then('the saved Generate form has {string} = {any}')
def saved_form(ctx, key, value):
    ctx.app.js('await new Promise((r) => setTimeout(r, 400));')
    got = ctx.app.ev('JSON.parse(localStorage.getItem("ainvil.generate") || "{}")[args[0]]', key)
    if got != lit(value):
        raise AssertionError(f'Saved {key} = {got!r}')


# ---------- LoRAs ----------
@when('I add a LoRA')
def add_lora(ctx):
    ctx.app.click('+ Add LoRA')


@when('I type {string} into the LoRA search')
def lora_search(ctx, q):
    ctx.app.set('Search LoRAs', q, 'LoRA')


@then('the LoRA list is')
def lora_list(ctx):
    # | on/off | name | weight |
    want = [[c for c in r] for r in rows(ctx)]
    got = ctx.app.ev('''[...document.querySelectorAll("#loraList .lora-row")].map((r) => [
        r.querySelector("button.toggle").textContent, r.querySelector("select").value.split("/").pop(), r.querySelector("input").value])''')
    if got != want:
        raise AssertionError(f'LoRA list: {got}')


@then('the LoRA section says {string}')
def lora_says(ctx, text):
    ctx.app.wait('document.querySelector("#loraList").textContent.includes(args[0])', 5,
                 lambda: f'LoRA section: {ctx.app.ev("document.querySelector(`#loraList`).textContent")}', text)


def lora_row(ctx, n):
    return f'document.querySelectorAll("#loraList .lora-row")[{n - 1}]'


@when('I set LoRA {int} to {string} with weight {string}')
def set_lora(ctx, n, name, weight):
    ctx.app.js(f'''
      const r = {lora_row(ctx, n)};
      __t.set(r.querySelector("select"), args[0]);
      __t.set(r.querySelector("input"), args[1]);
    ''', name, weight)


@when('I switch LoRA {int} off')
@when('I switch LoRA {int} on')
def toggle_lora(ctx, n):
    ctx.app.js(f'{lora_row(ctx, n)}.querySelector("button.toggle").click();')


@when('I remove LoRA {int}')
def remove_lora(ctx, n):
    ctx.app.js(f'{lora_row(ctx, n)}.querySelector("button.danger").click();')


# ---------- the workflow Ainvil builds ----------
@when('I download the workflow')
def download_workflow(ctx):
    n = len(ctx.app.downloads())
    ctx.app.click('Generate Workflow', 'Main')
    ok = ctx.app.js('''
      return await __t.until(() => /Downloaded|error/.test(document.querySelector("#genStatus").className + document.querySelector("#genStatus").textContent)
        && __t.downloads.length > args[0] || document.querySelector("#genStatus").classList.contains("error"), 60000);
    ''', n)
    if not ok:
        raise AssertionError('No workflow was downloaded: ' + ctx.app.ev('document.querySelector("#genStatus").textContent'))
    if ctx.app.ev('document.querySelector("#genStatus").classList.contains("error")'):
        raise AssertionError('Generate Workflow failed: ' + ctx.app.ev('document.querySelector("#genStatus").textContent'))
    ctx.vars['wf'] = json.loads(download_bytes(ctx, '*-api.json'))


def wf(ctx):
    if 'wf' not in ctx.vars:
        ctx.vars['wf'] = json.loads(download_bytes(ctx, '*-api.json'))
    return ctx.vars['wf']


def node(ctx, nid):
    a = wf(ctx)
    if str(nid) not in a:
        raise AssertionError(f'The workflow has no node {nid}: {sorted(a, key=lambda k: int(k) if k.isdigit() else 0)}')
    return a[str(nid)]


def by_title(ctx, title):
    hits = [(k, n) for k, n in wf(ctx).items() if n.get('_meta', {}).get('title') == title or (n['class_type'] == title)]
    if len(hits) != 1:
        raise AssertionError(f'{len(hits)} nodes titled "{title}"')
    return hits[0]


def check_value(where, got, want):
    if isinstance(want, str) and want.startswith('/') and want.endswith('/') and len(want) > 1:
        if not isinstance(got, str) or not re.search(want[1:-1], got):
            raise AssertionError(f'{where} is {got!r}, expected to match {want}')
        return
    if isinstance(want, (int, float)) and isinstance(got, (int, float)) and not isinstance(want, bool):
        if abs(got - want) > 1e-9:
            raise AssertionError(f'{where} is {got!r}, expected {want!r}')
        return
    if got != want:
        raise AssertionError(f'{where} is {got!r}, expected {want!r}')


@then('the workflow sets')
def wf_sets(ctx):
    # | node | input | value |   (value: JSON, or /regex/)
    for nid, inp, value in rows(ctx):
        n = node(ctx, nid)
        if inp not in n['inputs']:
            raise AssertionError(f'Node {nid} ({n["class_type"]}) has no input "{inp}"')
        check_value(f'Node {nid} {inp}', n['inputs'][inp], lit(value))


@then('the workflow sets node {int} {string} to {any}')
def wf_node_input(ctx, nid, inp, value):
    check_value(f'Node {nid} {inp}', node(ctx, nid)['inputs'].get(inp), lit(value))


@then('the workflow has node {int} ({word})')
def wf_has_node(ctx, nid, cls):
    n = node(ctx, nid)
    if n['class_type'] != cls:
        raise AssertionError(f'Node {nid} is a {n["class_type"]}')


@then('the workflow has no node {int}')
def wf_no_node(ctx, nid):
    if str(nid) in wf(ctx):
        raise AssertionError(f'The workflow has node {nid} ({wf(ctx)[str(nid)]["class_type"]})')


@then('the workflow has {int} {word} node(s)')
def wf_count(ctx, n, cls):
    got = sum(1 for x in wf(ctx).values() if x['class_type'] == cls)
    if got != n:
        raise AssertionError(f'The workflow has {got} {cls} nodes')


@then('the workflow has no {word} node')
def wf_none(ctx, cls):
    wf_count(ctx, 0, cls)


@then('the workflow node {int} {string} is linked to node {int}')
def wf_link(ctx, nid, inp, src):
    v = node(ctx, nid)['inputs'].get(inp)
    if not (isinstance(v, list) and str(v[0]) == str(src)):
        raise AssertionError(f'Node {nid} {inp} is {v!r}')


@then('the workflow node {int} {string} is linked to the {string} node')
def wf_link_title(ctx, nid, inp, title):
    k, _ = by_title(ctx, title)
    wf_link(ctx, nid, inp, int(k) if k.isdigit() else k)


@then('the workflow has a node titled {string} with')
def wf_titled(ctx, title):
    _, n = by_title(ctx, title)
    for inp, value in rows(ctx):
        check_value(f'"{title}" {inp}', n['inputs'].get(inp), lit(value))


@then('the workflow has no node titled {string}')
def wf_no_titled(ctx, title):
    hits = [n for n in wf(ctx).values() if n.get('_meta', {}).get('title') == title]
    if hits:
        raise AssertionError(f'The workflow has a node titled "{title}"')


@then('the {string} input of the {string} node is linked to the {string} node')
def wf_titled_link(ctx, inp, title, src):
    _, n = by_title(ctx, title)
    k, _ = by_title(ctx, src)
    v = n['inputs'].get(inp)
    if not (isinstance(v, list) and v[0] == k):
        raise AssertionError(f'"{title}" {inp} is {v!r}, expected a link to node {k}')


def describe_model_path(a, start='19', inp='model'):
    out = []
    ref = a[start]['inputs'].get(inp)
    seen = 0
    while isinstance(ref, list) and seen < 20:
        seen += 1
        n = a[str(ref[0])]
        c = n['class_type']
        if c.startswith('LoraLoader'):
            out.append(f"LoRA {n['inputs']['lora_name'].split('/')[-1]} ×{n['inputs']['strength_model']:g}")
        else:
            out.append(c)
        nxt = n['inputs'].get('model')
        if nxt is None and c == 'ComfySwitchNode':
            nxt = n['inputs'].get('on_true' if n['inputs'].get('switch') else 'on_false')
        ref = nxt
    return ' ← '.join(out)


@then('the sampler\'s model comes from {string}')
def model_path(ctx, want):
    got = describe_model_path(wf(ctx))
    if got != want:
        raise AssertionError(f'The sampler\'s model comes from "{got}"')


@then('the workflow\'s filename prefix starts with {string}')
def wf_prefix(ctx, prefix):
    for n in wf(ctx).values():
        v = n['inputs'].get('filename_prefix')
        if v is not None:
            if not v.startswith(prefix) or '%' in v:
                raise AssertionError(f'filename_prefix is {v!r}')
            return
    raise AssertionError('No filename_prefix in the workflow')


@then('the workflow\'s filename prefix is today\'s date followed by {string}')
def wf_prefix_date(ctx, rest):
    today = time.strftime('%Y%m%d')
    want = rest.replace('{date}', today)
    for n in wf(ctx).values():
        v = n['inputs'].get('filename_prefix')
        if v is not None:
            if v != want:
                raise AssertionError(f'filename_prefix is {v!r}, expected {want!r}')
            return
    raise AssertionError('No filename_prefix in the workflow')


@then('the workflow loads the input image from {string}')
def wf_loads(ctx, pattern):
    v = node(ctx, 51)['inputs']['image']
    if not re.fullmatch(pattern, v):
        raise AssertionError(f'Node 51 image is {v!r}')
    ctx.vars['image_ref'] = v


@then('the status says {string}')
def status_says(ctx, text):
    ctx.app.wait('document.querySelector("#genStatus").textContent.includes(args[0])', 30,
                 lambda: f'Status: "{ctx.app.ev("document.querySelector(`#genStatus`).textContent")}"', text)


@then('the status is an error saying {string}')
def status_error(ctx, text):
    status_says(ctx, text)
    if not ctx.app.ev('document.querySelector("#genStatus").classList.contains("error")'):
        raise AssertionError('The status is not an error')


# ---------- generating ----------
def wait_idle(ctx, timeout=GEN_TIMEOUT):
    ctx.app.wait('!(0, window.eval)("busy")', timeout, 'The generation did not finish')


@when('I generate')
def generate(ctx):
    ctx.app.click('Generate', 'Main')
    ctx.app.wait('(0, window.eval)("busy")', 5, 'Generate did not start')
    wait_idle(ctx)


@when('the generation finishes')
@then('the generation finishes')
def generation_finishes(ctx):
    wait_idle(ctx)


@then('the generation succeeds with {int} image(s)')
def gen_ok(ctx, n):
    status_says(ctx, f'Done — {n} image(s)')
    gallery_count(ctx, n)


@then('the Output Gallery shows {int} image(s)')
def gallery_count(ctx, n):
    got = ctx.app.js('return await __t.until(() => (0, window.eval)("gallery.items.length") === args[0], 10000) ? args[0] : (0, window.eval)("gallery.items.length");', n)
    if got != n:
        raise AssertionError(f'The Output Gallery has {got} images')
    thumbs = ctx.app.ev('document.querySelectorAll("#galleryThumbs img").length')
    if thumbs != n:
        raise AssertionError(f'The Output Gallery shows {thumbs} thumbnails')


@then('the Output Gallery is empty')
def gallery_empty(ctx):
    gallery_count(ctx, 0)
    ctx.app.wait('document.querySelector("#galleryMain").textContent.includes("No images yet")', 5)


@then('the gallery info says {string}')
def gallery_info(ctx, text):
    ctx.app.wait('document.querySelector("#galleryInfo").textContent.includes(args[0])', 10,
                 lambda: f'Gallery info: "{ctx.app.ev("document.querySelector(`#galleryInfo`).textContent")}"', text)


@then('the gallery images have the seeds {any}')
def gallery_seeds(ctx, seeds):
    want = [int(s) for s in re.findall(r'\d+', seeds)]
    got = ctx.app.ev('(0, window.eval)("gallery.items").map((x) => x.seed)')
    if got != want:
        raise AssertionError(f'Seeds: {got}')


@then('every gallery image was saved in the test folder')
def saved_in_test_folder(ctx):
    items = ctx.app.ev('(0, window.eval)("gallery.items").map((x) => [x.type, x.subfolder, x.filename])')
    for typ, sub, fn in items:
        if typ != 'output' or not sub.startswith(TEST_PREFIX):
            raise AssertionError(f'{sub}/{fn} ({typ}) is not in {TEST_PREFIX}/')


@then('every gallery image is a temporary preview')
def temp_previews(ctx):
    items = ctx.app.ev('(0, window.eval)("gallery.items").map((x) => x.type)')
    if not items or any(t != 'temp' for t in items):
        raise AssertionError(f'Image types: {items}')


@then('every gallery image is {size} pixels')
def gallery_sizes(ctx, size):
    sizes = ctx.app.js('return await Promise.all((0, window.eval)("gallery.items").map((x) => __t.size(x.blob)));')
    for s in sizes:
        if tuple(s) != size:
            raise AssertionError(f'Image sizes: {sizes}')


@when('I start generating')
@when('I start generating again')
def press_generate(ctx):
    ctx.app.click('Generate', 'Main')


@then('Generate is running')
def is_busy(ctx):
    ctx.app.wait('(0, window.eval)("busy")', 5, 'Generate is not running')


@when('the first image is being generated')
def first_running(ctx):
    # The job waits for its first prompt and the server says it is executing it.
    ctx.app.wait('(0, window.eval)("runningJob?.n === 1 && runningJob.cur && runningJob.cur === runningJob.prompts[0] && progress.running === runningJob.cur.id")',
                 GEN_TIMEOUT, 'The first image did not start')


@when('the job has {int} image(s) done')
def job_done(ctx, n):
    ctx.app.wait(f'(0, window.eval)("runningJob?.done ?? -1") >= {n}', GEN_TIMEOUT, f'The job did not get to {n} done images')


@then('the server has none of the job\'s prompts queued')
def none_queued(ctx):
    ids = set(ctx.app.ev('(0, window.eval)("[...progress.promptIds]")'))
    time.sleep(1)
    left = ids & ctx.comfy.queued_ids()
    if left:
        raise AssertionError(f'Still queued on the server: {left}')


@then('the Manage Jobs button says {string}')
def jobs_button(ctx, text):
    ctx.app.wait('document.querySelector("#btnJobs").textContent === args[0]', 30,
                 lambda: f'Manage Jobs says "{ctx.app.ev("document.querySelector(`#btnJobs`).textContent")}"', text)


@then('the jobs dialog lists')
def jobs_list(ctx):
    # | job | state |
    want = [[r[0], r[1]] for r in rows(ctx)]
    ok = ctx.app.js('''
      const want = args[0];
      const got = () => [...document.querySelectorAll("#jobsList .job-row")].map((r) => {
        const t = r.querySelector(".hist-meta div").textContent; const m = /^(#\\d+) · (.*)$/.exec(t); return m ? [m[1], m[2]] : [t, ''];
      });
      return await __t.until(() => JSON.stringify(got().map(([j, s], i) => [j, want[i] && s.startsWith(want[i][1]) ? want[i][1] : s])) === JSON.stringify(want), 20000) || got();
    ''', want)
    if ok is not True:
        raise AssertionError(f'Jobs: {ok}')


@then('the jobs dialog says {string}')
def jobs_says(ctx, text):
    ctx.app.wait('document.querySelector("#jobsDlg").innerText.includes(args[0])', 30, f'The jobs dialog does not say "{text}"', text)


@when('I cancel job {string} in the jobs dialog')
def cancel_job(ctx, job):
    ctx.app.js('''
      const r = [...document.querySelectorAll("#jobsList .job-row")].find((x) => x.querySelector("b").textContent === args[0]);
      if (!r) throw new Error("No job " + args[0]);
      r.querySelector("button").click();
    ''', job)


@then('the gallery images have the prompts')
def gallery_prompts(ctx):
    want = [r[0] for r in rows(ctx, header=False)]
    got = ctx.app.ev('(0, window.eval)("gallery.items").map((x) => x.text)')
    if got != want:
        raise AssertionError(f'Prompts: {got}')


@when('I watch the gallery info')
def watch_info(ctx):
    ctx.app.js('__t.watch("#galleryInfo");')


@then('the gallery showed a live preview while generating')
def saw_preview(ctx):
    seen = ctx.app.ev('__t.seen["#galleryInfo"] || []')
    if not any(s.startswith('Live preview') for s in seen):
        raise AssertionError(f'The gallery info never said "Live preview": {seen}')


@given('the saved Generate form has the model {string}')
def saved_model(ctx, model):
    ctx.app.js('gen.model = args[0]; localStorage.setItem("ainvil.generate", JSON.stringify(gen));', model)
    ctx.app.reload()
    ctx.app.wait('(0, window.eval)("connected")', 30)


@then('the uploaded input image is on the server')
def upload_on_server(ctx):
    ref = node(ctx, 51)['inputs']['image']
    sub, _, name = ref.rpartition('/')
    if not ctx.comfy.exists(name, sub, 'input'):
        raise AssertionError(f'input/{ref} is not on the server')


@given('the server reports no CADS node type')
def no_cads_class(ctx):
    # As if comfyui-cads weren't installed: the object_info has no CADS entry.
    ctx.app.js('delete OI.CADS; oiStamp++; refreshGenerateOptions();')


@then('{int} file(s) was downloaded')
@then('{int} file(s) were downloaded')
def n_downloads(ctx, n):
    got = len(ctx.app.downloads())
    if got != n:
        raise AssertionError(f'{got} files were downloaded')


@then('LoRA {int} lists {string}')
def lora_lists(ctx, n, text):
    opts = ctx.app.ev(f'[...{lora_row(ctx, n)}.querySelector("select").options].map((o) => o.textContent)')
    if text not in opts:
        raise AssertionError(f'LoRA {n} lists {opts}')


@then('every gallery image matches the input image outside {int}, {int} of size {size}')
def same_outside(ctx, x, y, size):
    diffs = ctx.app.js('''
      return await Promise.all((0, window.eval)("gallery.items").map((it) => __t.diff(it.blob, (0, window.eval)("input.blob"), args[0], { outside: true })));
    ''', {'x': x, 'y': y, 'w': size[0], 'h': size[1]})
    if any(d > 1 for d in diffs):
        raise AssertionError(f'Largest pixel differences outside the mask: {diffs}')


@then('every gallery image differs from the input image inside {int}, {int} of size {size}')
def differs_inside(ctx, x, y, size):
    diffs = ctx.app.js('''
      return await Promise.all((0, window.eval)("gallery.items").map((it) => __t.diff(it.blob, (0, window.eval)("input.blob"), args[0])));
    ''', {'x': x, 'y': y, 'w': size[0], 'h': size[1]})
    if any(d < 10 for d in diffs):
        raise AssertionError(f'Largest pixel differences inside the mask: {diffs}')
