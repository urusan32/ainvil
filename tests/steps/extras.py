"""Extras tab steps: custom workflow parameters, image lists, runs and the Extras output."""
import json
import re

from ainvil_bdd.registry import given, then, when
from steps.common import download_bytes, rows
from steps.generate import GEN_TIMEOUT
from steps.images import image_spec


def param_box(name):
    return f'''(() => {{
      const box = [...document.querySelectorAll("#exParams > div.full")].find((d) => d.querySelector("label")?.firstChild?.textContent === {json.dumps(name)});
      if (!box) throw new Error("No image parameter {name}");
      return box;
    }})()'''


def specs(ctx):
    # | name | size |
    out = []
    for name, size in rows(ctx):
        w, h = (int(v) for v in re.split(r'\s*[x×]\s*', size))
        out.append(image_spec(name, (w, h)))
    return out


@when('I add these images to {string} in Extras')
@given('these images are added to {string} in Extras')
def add_images(ctx, param):
    ctx.app.js(f'__t.drop({param_box(param)}.querySelector(".dropbox"), await __t.files(args[0]));', specs(ctx))
    ctx.app.wait(f'{param_box(param)}.querySelectorAll(".imglist img").length >= args[0]', 10, 'The images were not added', len(specs(ctx)))


@when('I choose these images for {string} with "choose files"')
def choose_images(ctx, param):
    ctx.app.js('__t.nextFiles.push(await __t.files(args[0]));', specs(ctx))
    ctx.app.js(f'[...{param_box(param)}.querySelectorAll("button")].find((b) => b.textContent === "choose files").click();')
    ctx.app.wait(f'{param_box(param)}.querySelectorAll(".imglist img").length >= args[0]', 10, 'The images were not added', len(specs(ctx)))


@when('I paste an image {string} of {size} pixels in Extras')
def paste_extras(ctx, name, size):
    ctx.app.js('document.activeElement?.blur(); __t.paste(await __t.files([args[0]]));', image_spec(name, size))


@then('{string} in Extras has the images')
def has_images(ctx, param):
    want = [r[0] for r in rows(ctx, header=False)]
    got = ctx.app.js(f'return await __t.until(() => {{ const l = [...{param_box(param)}.querySelectorAll(".imglist img")].map((i) => i.alt); return l.length === args[0] && l; }}, 5000) || [...{param_box(param)}.querySelectorAll(".imglist img")].map((i) => i.alt);', len(want))
    if got != want:
        raise AssertionError(f'Images: {got}')


@then('{string} in Extras has no images')
def no_images(ctx, param):
    n = ctx.app.ev(f'{param_box(param)}.querySelectorAll(".imglist img").length')
    if n:
        raise AssertionError(f'{param} has {n} images')


@then('{string} in Extras says {string}')
def param_count(ctx, param, text):
    got = ctx.app.ev(f'{param_box(param)}.querySelector("label .sub").textContent')
    if got != text:
        raise AssertionError(f'{param} says "{got}"')


@when('I remove image {int} from {string} in Extras')
def remove_image(ctx, n, param):
    ctx.app.js(f'{param_box(param)}.querySelectorAll(".imglist .im button")[args[0] - 1].click();', n)


@when('I click "Clear images" for {string} in Extras')
def clear_images(ctx, param):
    ctx.app.js(f'[...{param_box(param)}.querySelectorAll("button")].find((b) => b.textContent === "Clear images").click();')


@then('the Extras parameters are')
def ex_params(ctx):
    want = [r[0] for r in rows(ctx, header=False)]
    got = ctx.app.ev('''[...document.querySelectorAll("#exParams > *")].map((el) => {
        const l = el.tagName === "LABEL" ? el : el.querySelector("label");
        return l ? __t.norm(l.firstChild.nodeType === 3 ? l.firstChild.textContent : l.textContent) : __t.norm(el.textContent);
      })''')
    if got != want:
        raise AssertionError(f'Extras parameters: {got}')


@then('the Extras hint for {string} is {string}')
def ex_hint(ctx, param, text):
    got = ctx.app.ev('''[...document.querySelectorAll("#exParams > *")].find((el) => (el.tagName === "LABEL" ? el : el.querySelector("label"))?.textContent.startsWith(args[0]))?.querySelector(".hint")?.textContent''', param)
    if got != text:
        raise AssertionError(f'Hint: {got!r}')


@then('the Extras status says {string}')
def ex_status(ctx, text):
    ctx.app.wait('document.querySelector("#exStatus").textContent.includes(args[0])', 30,
                 lambda: f'Extras status: "{ctx.app.ev("document.querySelector(`#exStatus`).textContent")}"', text)


@then('the Extras status is an error saying {string}')
def ex_status_error(ctx, text):
    ex_status(ctx, text)
    if not ctx.app.ev('document.querySelector("#exStatus").classList.contains("error")'):
        raise AssertionError('The Extras status is not an error')


@when('I download the Extras workflow')
def ex_download(ctx):
    n = len(ctx.app.downloads())
    ctx.app.click('Generate Workflow', 'Extras')
    ok = ctx.app.js('''return await __t.until(() => __t.downloads.length > args[0] || document.querySelector("#exStatus").classList.contains("error"), 60000);''', n)
    if not ok or ctx.app.ev('document.querySelector("#exStatus").classList.contains("error")'):
        raise AssertionError('No Extras workflow was downloaded: ' + ctx.app.ev('document.querySelector("#exStatus").textContent'))
    ctx.vars['wf'] = json.loads(download_bytes(ctx, '*-api.json'))


@when('I run the Extras workflow')
def ex_run(ctx):
    ctx.app.click('Run', 'Extras')
    ctx.app.wait('!(0, window.eval)("exBusy")', GEN_TIMEOUT, 'The Extras run did not finish')


@when('I press Run in Extras')
def ex_press_run(ctx):
    ctx.app.click('Run', 'Extras')


@then('Extras is running')
def ex_busy(ctx):
    ctx.app.wait('(0, window.eval)("exBusy")', 10, 'Extras is not running')


@when('the Extras run finishes')
def ex_finishes(ctx):
    ctx.app.wait('!(0, window.eval)("exBusy")', GEN_TIMEOUT, 'The Extras run did not finish')


@then('the Extras output shows {int} image(s)')
def ex_out_count(ctx, n):
    got = ctx.app.js('return await __t.until(() => (0, window.eval)("exOut.items.length") === args[0], 10000) ? args[0] : (0, window.eval)("exOut.items.length");', n)
    if got != n:
        raise AssertionError(f'The Extras output has {got} images')


@then('the Extras output images are')
def ex_out_images(ctx):
    # | input | size |
    want = [[r[0], r[1].replace('x', '×')] for r in rows(ctx)]
    got = ctx.app.js('return await Promise.all((0, window.eval)("exOut.items").map(async (x) => [x.input, (await __t.size(x.blob)).join("×")]));')
    if got != want:
        raise AssertionError(f'Extras output: {got}')


@then('the Extras output info says {string}')
def ex_info(ctx, text):
    ctx.app.wait('document.querySelector("#exGalleryInfo").textContent.includes(args[0])', 10,
                 lambda: f'Extras info: "{ctx.app.ev("document.querySelector(`#exGalleryInfo`).textContent")}"', text)


@then('every Extras output image was saved in the test folder')
def ex_saved(ctx):
    from steps.common import TEST_PREFIX
    items = ctx.app.ev('(0, window.eval)("exOut.items").map((x) => [x.type, x.subfolder, x.filename])')
    for typ, sub, fn in items:
        if typ != 'output' or not sub.startswith(TEST_PREFIX):
            raise AssertionError(f'{sub}/{fn} ({typ}) is not in {TEST_PREFIX}/')


@then('the Extras output is empty')
def ex_empty(ctx):
    ex_out_count(ctx, 0)


@when('I click Extras output thumbnail {int}')
def ex_thumb(ctx, n):
    ctx.app.js('document.querySelectorAll("#exThumbs img")[args[0] - 1].click();', n)
