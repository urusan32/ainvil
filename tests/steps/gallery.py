"""Output Gallery, full-screen viewer, server History and Image Stash steps."""
import io
import json
import re
import zipfile

from ainvil_bdd.registry import given, then, when
from steps.common import TEST_PREFIX, download_bytes, downloaded, rows
from steps.generate import GEN_TIMEOUT, wait_idle
from steps.images import image_spec


# ---------- a gallery with real generated images ----------
@given('the Output Gallery holds {int} images generated with seeds from {int}')
def gallery_with_images(ctx, n, seed):
    """Generates once per run (small and fast), then reuses the server images like History › Add to Gallery does."""
    key = ('gallery', n, seed)
    cached = ctx.run.get(key)
    if cached is None:
        ctx.app.js('''
          for (const [k, v] of Object.entries(args[0])) __t.set(k, v, k === "Seed" ? "Generation Parameters" : undefined);
          __t.set("Random", false);
          __t.set("Seed", String(args[1]), "Generation Parameters");
        ''', {'Prompt': 'safe, a small red apple on a plain table', 'Width': '256', 'Height': '256', 'Steps': '4',
              'Batch count': str(n)}, seed)
        ctx.app.click('Generate', 'Main')
        ctx.app.wait('(0, window.eval)("busy")', 5)
        wait_idle(ctx)
        cached = ctx.app.ev('(0, window.eval)("gallery.items").map(({blob, url, src, ...x}) => x)')
        if len(cached) != n:
            raise AssertionError(f'Generated {len(cached)} images: ' + ctx.app.ev('document.querySelector("#genStatus").textContent'))
        ctx.run[key] = cached
        ctx.app.js('(0, window.eval)("clearGallery")(false);')
    ctx.app.js('''
      const g = (0, window.eval)("gallery"), item = (0, window.eval)("galleryItem");
      for (const x of args[0]) g.items.push({ ...(await item({ filename: x.filename, subfolder: x.subfolder, type: x.type }, x.seed, x.batchIndex)), a: x.a, text: x.text, model: x.model, number: x.number, time: x.time });
      g.sel = 0;
      g.render();
    ''', cached)
    ctx.vars['gallery'] = cached


@when('I click gallery thumbnail {int}')
def click_thumb(ctx, n):
    ctx.app.js('document.querySelectorAll("#galleryThumbs img")[args[0] - 1].click();', n)


@then('gallery thumbnail {int} is selected')
def thumb_selected(ctx, n):
    sel = ctx.app.ev('[...document.querySelectorAll("#galleryThumbs img")].findIndex((i) => i.classList.contains("sel")) + 1')
    if sel != n:
        raise AssertionError(f'Thumbnail {sel} is selected')


# ---------- the viewer ----------
@when('I click the main gallery image')
def click_main(ctx):
    ctx.app.js('document.querySelector("#galleryMain img").click();')


@when('I click the main Extras output image')
def click_ex_main(ctx):
    ctx.app.js('document.querySelector("#exGalleryMain img").click();')


@then('the viewer is open')
def viewer_open(ctx):
    ctx.app.wait('!document.querySelector("#viewer").hidden', 5, 'The viewer is not open')


@then('the viewer is closed')
def viewer_closed(ctx):
    ctx.app.wait('document.querySelector("#viewer").hidden', 5, 'The viewer is still open')


@then('the viewer shows image {int}')
def viewer_shows(ctx, n):
    want = ctx.vars['gallery'][n - 1]['filename'] if 'gallery' in ctx.vars else None
    got = ctx.app.ev('document.querySelector("#viewerLink").download')
    if want and got != want:
        raise AssertionError(f'The viewer shows {got}, expected {want}')
    ctx.vars['viewer_file'] = got


@then('the viewer shows {string}')
def viewer_shows_name(ctx, name):
    got = ctx.app.ev('document.querySelector("#viewerLink").download')
    if got != name:
        raise AssertionError(f'The viewer shows {got}')


@then('the viewer loads the image from the server with its filename')
def viewer_url(ctx):
    src = ctx.app.ev('document.querySelector("#viewerImg").getAttribute("src")')
    if not (src.startswith(ctx.app.server_url + 'view?') or src.startswith('blob:')):
        raise AssertionError(f'The viewer image is {src}')
    href = ctx.app.ev('document.querySelector("#viewerLink").getAttribute("href")')
    if not href:
        raise AssertionError('The viewer has no download link')


@when('I click the viewer background')
def viewer_bg(ctx):
    ctx.app.js('document.querySelector("#viewer").click();')


# ---------- downloads ----------
@then('the downloaded image is gallery image {int}')
def dl_is_gallery(ctx, n):
    want = ctx.vars['gallery'][n - 1]['filename']
    d = downloaded(ctx, want)
    data = download_bytes(ctx, want)
    if not data.startswith(b'\x89PNG'):
        raise AssertionError(f'{d["name"]} is not a PNG')


@then('the downloaded ZIP {string} holds {int} PNG images')
def zip_holds(ctx, pattern, n):
    data = download_bytes(ctx, pattern)
    z = zipfile.ZipFile(io.BytesIO(data))
    if z.testzip() is not None:
        raise AssertionError('The ZIP is corrupt')
    names = z.namelist()
    if len(names) != n or not all(z.read(x).startswith(b'\x89PNG') for x in names):
        raise AssertionError(f'ZIP entries: {names}')
    ctx.vars['zip_names'] = names


@then('the ZIP entries are named like the gallery images')
def zip_names(ctx):
    want = [x['filename'] for x in ctx.vars['gallery']]
    if ctx.vars['zip_names'] != want:
        raise AssertionError(f'ZIP entries: {ctx.vars["zip_names"]}, gallery: {want}')


@then('the downloaded ZIP {string} has the entries')
def zip_entries(ctx, pattern):
    want = [r[0] for r in rows(ctx, header=False)]
    names = zipfile.ZipFile(io.BytesIO(download_bytes(ctx, pattern))).namelist()
    if names != want:
        raise AssertionError(f'ZIP entries: {names}')


# ---------- server history ----------
@when('I open the History')
def open_history(ctx):
    ctx.app.click('History…', 'the Output Gallery')
    ctx.app.wait('!document.querySelector("#historyDlg").hidden && !document.querySelector("#histList").textContent.includes("Loading…")', 30, 'The History did not load')


def hist_row(number):
    return f'''(() => {{
      const r = [...document.querySelectorAll("#histList .hist-row")].find((x) => x.querySelector(".hist-meta b")?.textContent === "#" + {json.dumps(str(number))});
      if (!r) throw new Error("No history entry #{number}");
      return r;
    }})()'''


def my_number(ctx, which='last'):
    nums = [x['number'] for x in ctx.vars.get('gallery', [])] or ctx.app.ev('(0, window.eval)("gallery.items").map((x) => x.number)')
    if not nums:
        raise AssertionError('No generated prompt to look for')
    return nums[-1] if which == 'last' else nums[0]


@then('the History lists my prompt with')
def history_lists(ctx):
    n = my_number(ctx)
    ctx.vars['hist_number'] = n
    text = ctx.app.ev(f'{hist_row(n)}.innerText')
    for (want,) in rows(ctx, header=False):
        if want not in text:
            raise AssertionError(f'History entry #{n} does not show "{want}":\n{text}')


@when('I click {string} for my prompt in the History')
def history_click(ctx, button):
    n = ctx.vars.get('hist_number') or my_number(ctx)
    ctx.app.js(f'[...{hist_row(n)}.querySelectorAll("button")].find((b) => b.textContent === args[0]).click();', button)


@when('I click the thumbnail of my prompt in the History')
def history_thumb(ctx):
    n = ctx.vars.get('hist_number') or my_number(ctx)
    ctx.app.js(f'{hist_row(n)}.querySelector(".hist-thumbs img").click();')


@then('the History is open')
def history_open(ctx):
    ctx.app.wait('!document.querySelector("#historyDlg").hidden', 5, 'The History is not open')


@then('the History is closed')
def history_closed(ctx):
    ctx.app.wait('document.querySelector("#historyDlg").hidden', 5, 'The History is still open')


@then('the History shows at most {int} entries')
def history_max(ctx, n):
    ctx.app.wait('!document.querySelector("#histList").textContent.includes("Loading…")', 30)
    got = ctx.app.ev('document.querySelectorAll("#histList .hist-row").length')
    if got > n or got == 0:
        raise AssertionError(f'The History shows {got} entries')


@then('the History entries are newest first')
def history_order(ctx):
    nums = ctx.app.ev('[...document.querySelectorAll("#histList .hist-row .hist-meta b")].map((b) => Number(b.textContent.slice(1)))')
    if nums != sorted(nums, reverse=True):
        raise AssertionError(f'History order: {nums}')


# ---------- the Image Stash ----------
def stash_names(ctx):
    return ctx.app.js('await (0, window.eval)("loadStash")(); return (0, window.eval)("stash.items").map((x) => x.filename);')


@then('the Image Stash holds')
def stash_holds(ctx):
    want = [r[0] for r in rows(ctx, header=False)]
    got = ctx.app.js('''
      await (0, window.eval)("loadStash")();
      return await __t.until(() => { const l = (0, window.eval)("stash.items").map((x) => x.filename); return JSON.stringify(l) === JSON.stringify(args[0]) ? true : null; }, 5000)
        || (0, window.eval)("stash.items").map((x) => x.filename);
    ''', want)
    if got is not True:
        raise AssertionError(f'The Image Stash holds {got}')


@then('the Image Stash is empty')
def stash_empty(ctx):
    got = stash_names(ctx)
    if got:
        raise AssertionError(f'The Image Stash holds {got}')


@then('the Image Stash holds {int} image(s)')
def stash_count(ctx, n):
    got = ctx.app.js('await (0, window.eval)("loadStash")(); return await __t.until(() => (0, window.eval)("stash.items").length === args[0], 10000) ? args[0] : (0, window.eval)("stash.items").length;', n)
    if got != n:
        raise AssertionError(f'The Image Stash holds {got} images')


@given('the Image Stash holds the images')
def stash_seed(ctx):
    # | name | size |
    specs = []
    for name, size in rows(ctx):
        w, h = (int(v) for v in re.split(r'\s*[x×]\s*', size))
        specs.append(image_spec(name, (w, h)))
    # Stashed one after another, like dropping them on the stash: the last one ends up on top.
    ctx.app.js('for (const f of await __t.files(args[0])) await (0, window.eval)("stashFile")(f);', specs)


@when('I open the Image Stash')
def open_stash(ctx):
    ctx.app.click('Stash…', 'the Output Gallery')
    ctx.app.wait('!document.querySelector("#stashDlg").hidden && !document.querySelector("#stashList").textContent.includes("Loading…")', 15, 'The stash did not open')


@then('the Image Stash dialog lists')
def stash_dialog_lists(ctx):
    want = [r for r in rows(ctx)]
    cols = len(want[0]) if want else 1
    got = ctx.app.js('''
      return [...document.querySelectorAll("#stashList .hist-row")].map((r) => [r.querySelector(".hist-meta b").textContent,
        r.querySelector("button.toggle").textContent].slice(0, args[0]));
    ''', cols)
    if got != want:
        raise AssertionError(f'The stash dialog lists {got}')


@then('the Image Stash dialog says {string}')
def stash_says(ctx, text):
    ctx.app.wait('document.querySelector("#stashDlg").innerText.includes(args[0])', 10, f'The stash dialog does not say "{text}"', text)


def stash_row(name):
    return f'''(() => {{
      const r = [...document.querySelectorAll("#stashList .hist-row")].find((x) => x.querySelector(".hist-meta b").textContent === {json.dumps(name)});
      if (!r) throw new Error("No stashed image {name}");
      return r;
    }})()'''


@when('I click {string} for {string} in the Image Stash')
def stash_click(ctx, button, name):
    ctx.app.js(f'[...{stash_row(name)}.querySelectorAll("button")].find((b) => b.textContent === args[0]).click();', button)
    ctx.app.js('await new Promise((r) => setTimeout(r, 200));')


@when('I click the thumbnail of {string} in the Image Stash')
def stash_thumb(ctx, name):
    ctx.app.js(f'{stash_row(name)}.querySelector("img").click();')


@when('I drop these images on the Image Stash')
def drop_on_stash(ctx):
    specs = []
    for name, size in rows(ctx):
        w, h = (int(v) for v in re.split(r'\s*[x×]\s*', size))
        specs.append(image_spec(name, (w, h)))
    ctx.app.js('__t.drop(document.querySelector("#stashDrop"), await __t.files(args[0]));', specs)
    ctx.app.js('await new Promise((r) => setTimeout(r, 300));')


@when('I click the Image Stash drop box and choose these images')
def choose_for_stash(ctx):
    specs = []
    for name, size in rows(ctx):
        w, h = (int(v) for v in re.split(r'\s*[x×]\s*', size))
        specs.append(image_spec(name, (w, h)))
    ctx.app.js('__t.nextFiles.push(await __t.files(args[0])); document.querySelector("#stashDrop").click();', specs)
    ctx.app.js('await new Promise((r) => setTimeout(r, 300));')


@when('I drop a text file {string} on the Image Stash')
def drop_text_stash(ctx, name):
    ctx.app.js('__t.drop(document.querySelector("#stashDrop"), await __t.files([args[0]]));', {'text': 'x', 'name': name, 'type': 'text/plain'})


@then('the Image Stash dialog is closed')
def stash_closed(ctx):
    ctx.app.wait('document.querySelector("#stashDlg").hidden', 5, 'The stash is still open')


@then('the gallery image {int} is {string}')
def gallery_item_name(ctx, n, name):
    got = ctx.app.ev('(0, window.eval)("gallery.items")[args[0] - 1]?.filename', n)
    if got != name:
        raise AssertionError(f'Gallery image {n} is {got}')


@then('the Extras image list for {string} has {int} image(s)')
def ex_list_count(ctx, param, n):
    got = ctx.app.ev('Object.values((0, window.eval)("exImages")[(0, window.eval)("currentCw")().name] || {})[0]?.length ?? 0')
    if got != n:
        raise AssertionError(f'{param} has {got} images')
