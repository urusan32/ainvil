"""Input image, mask, mask editor, image editor and Focused inpainting steps.

Pixel coordinates in the steps are image pixels. Test images are made in the page: a gradient, optionally with
colored rectangles, so pixel checks have known values.
"""
import json
import re

from ainvil_bdd.registry import given, then, when
from steps.common import rows


def image_spec(name, size, **extra):
    w, h = size
    typ = 'image/jpeg' if name.lower().endswith(('.jpg', '.jpeg')) else 'image/webp' if name.lower().endswith('.webp') else 'image/png'
    return {'w': w, 'h': h, 'name': name, 'gradient': True, 'type': typ, **extra}


def wait_input(ctx, name=None):
    ctx.app.wait('(0, window.eval)("input.img") && (!args[0] || (0, window.eval)("input.name") === args[0])', 10, 'The input image did not load', name)


def drop(ctx, selector, specs):
    ctx.app.js('__t.drop(document.querySelector(args[0]), await __t.files(args[1]));', selector, specs)


# ---------- input image ----------
@given('an input image {string} of {size} pixels')
@when('I drop an image {string} of {size} pixels on the input image')
def input_image(ctx, name, size):
    drop(ctx, '#inputBox', [image_spec(name, size)])
    wait_input(ctx, name)


@given('an input image {string} of {size} pixels with a {word} square at {int}, {int} of size {int}')
def input_image_rect(ctx, name, size, color, x, y, s):
    drop(ctx, '#inputBox', [image_spec(name, size, gradient=False, fill='#406080', rects=[{'x': x, 'y': y, 'w': s, 'h': s, 'color': color}])])
    wait_input(ctx, name)


@given('an input image {string} of {size} pixels split into a {word} left half and a {word} right half')
def input_image_halves(ctx, name, size, left, right):
    w, h = size
    drop(ctx, '#inputBox', [image_spec(name, size, gradient=False, fill=left, rects=[{'x': w // 2, 'y': 0, 'w': w - w // 2, 'h': h, 'color': right}])])
    wait_input(ctx, name)


@when('I choose an image {string} of {size} pixels with {string} in Input Image')
def choose_image(ctx, name, size, button):
    ctx.app.js('__t.nextFiles.push(await __t.files([args[0]]));', image_spec(name, size))
    ctx.app.click(button, 'Input Image')
    wait_input(ctx, name)


@when('I click the empty input image box and choose {string} of {size} pixels')
def click_box_choose(ctx, name, size):
    ctx.app.js('__t.nextFiles.push(await __t.files([args[0]]));', image_spec(name, size))
    ctx.app.js('document.querySelector("#inputBox").click();')
    wait_input(ctx, name)


@when('I paste an image {string} of {size} pixels')
def paste_image(ctx, name, size):
    ctx.app.js('document.activeElement?.blur(); __t.paste(await __t.files([args[0]]));', image_spec(name, size))


@when('I drop a text file {string} on the input image')
def drop_text_file(ctx, name):
    drop(ctx, '#inputBox', [{'text': 'hello', 'name': name, 'type': 'text/plain'}])


@then('the input image is {string} of {size} pixels')
def input_is(ctx, name, size):
    wait_input(ctx, name)
    got = ctx.app.ev('[(0, window.eval)("input.name"), (0, window.eval)("input.w"), (0, window.eval)("input.h")]')
    if got != [name, *size]:
        raise AssertionError(f'Input image: {got}')


@then('the input image is {size} pixels')
def input_size(ctx, size):
    got = ctx.app.ev('[(0, window.eval)("input.w"), (0, window.eval)("input.h")]')
    if tuple(got) != size:
        raise AssertionError(f'Input image is {got}')


@then('the input image is named like {string}')
def input_named(ctx, pattern):
    name = ctx.app.ev('(0, window.eval)("input.name")')
    if not re.fullmatch(pattern, name):
        raise AssertionError(f'Input image is named {name!r}')


@then('there is no input image')
def no_input(ctx):
    if ctx.app.ev('!!(0, window.eval)("input.img")'):
        raise AssertionError('There is an input image')
    ctx.app.wait('document.querySelector("#inputBox").textContent.includes("Drop an image here")', 5)


@then('the input image pixel at {int}, {int} is {string}')
def input_pixel(ctx, x, y, color):
    px = ctx.app.js('return await __t.pixel((0, window.eval)("input.blob"), args[0], args[1]);', x, y)
    check_color(px, color, f'Input image pixel ({x}, {y})')


def check_color(px, color, where, tol=6):
    want = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
    if any(abs(a - b) > tol for a, b in zip(px[:3], want)):
        raise AssertionError(f'{where} is #{"".join(f"{v:02x}" for v in px[:3])}, expected {color}')


@when('I remember the input image')
def remember_input(ctx):
    ctx.vars['input_hash'] = ctx.app.ev('(0, window.eval)("input.hash")')


@then('the input image is unchanged')
def input_unchanged(ctx):
    if ctx.app.ev('(0, window.eval)("input.hash")') != ctx.vars['input_hash']:
        raise AssertionError('The input image changed')


@then('the input image has changed')
def input_changed(ctx):
    ctx.app.wait('(0, window.eval)("input.hash") !== args[0]', 10, 'The input image did not change', ctx.vars['input_hash'])


# ---------- masks ----------
def mask_spec(size, rects, name='mask.png'):
    w, h = size
    return {'w': w, 'h': h, 'name': name, 'fill': '#000000', 'rects': [{'x': x, 'y': y, 'w': rw, 'h': rh, 'color': '#ffffff'} for x, y, rw, rh in rects]}


def input_wh(ctx):
    return tuple(ctx.app.ev('[(0, window.eval)("input.w"), (0, window.eval)("input.h")]'))


@given('a mask covering {int}, {int} of size {size}')
@when('I drop a mask covering {int}, {int} of size {size} on the mask box')
def mask_rect(ctx, x, y, size):
    drop(ctx, '#maskBox', [mask_spec(input_wh(ctx), [(x, y, *size)])])
    ctx.app.wait('(0, window.eval)("input.mask")', 10, 'The mask did not load')


@when('I upload a mask covering {int}, {int} of size {size}')
def upload_mask(ctx, x, y, size):
    ctx.app.js('__t.nextFiles.push(await __t.files([args[0]]));', mask_spec(input_wh(ctx), [(x, y, *size)]))
    ctx.app.click('Upload', 'Input Image')
    ctx.app.wait('(0, window.eval)("input.mask")', 10, 'The mask did not load')


@when('I drop an all-black mask on the mask box')
def black_mask(ctx):
    drop(ctx, '#maskBox', [mask_spec(input_wh(ctx), [])])
    ctx.app.js('await new Promise((r) => setTimeout(r, 500));')


@then('the mask covers {int}, {int} of size {size}')
def mask_covers(ctx, x, y, size):
    want = {'x': x, 'y': y, 'w': size[0], 'h': size[1]}
    got = ctx.app.js('return await __t.until(() => (0, window.eval)("input.maskBounds"), 5000);')
    if got != want:
        raise AssertionError(f'Mask bounds: {got}')


@then('the mask bounds are about {int}, {int} of size {size}')
def mask_about(ctx, x, y, size):
    got = ctx.app.js('return await __t.until(() => (0, window.eval)("input.maskBounds"), 5000);')
    if not got:
        raise AssertionError('There is no mask')
    want = (x, y, *size)
    if any(abs(a - b) > 3 for a, b in zip((got['x'], got['y'], got['w'], got['h']), want)):
        raise AssertionError(f'Mask bounds: {got}')


@then('there is no mask')
def no_mask(ctx):
    if ctx.app.ev('!!(0, window.eval)("input.mask")'):
        raise AssertionError('There is a mask')


@then('the downloaded mask is white in {int}, {int} of size {size} and black elsewhere')
def downloaded_mask(ctx, x, y, size):
    from steps.common import downloaded
    d = downloaded(ctx, '*-mask.png')
    r = ctx.app.js('''
      const f = __t.fromB64(args[0], 'm.png', 'image/png');
      const [x, y, w, h] = args[1];
      return [await __t.pixel(f, x + 1, y + 1), await __t.pixel(f, x + w - 2, y + h - 2), await __t.pixel(f, 0, 0), await __t.pixel(f, x + w + 1, y)];
    ''', d['b64'], [x, y, *size])
    if r[0][:3] != [255, 255, 255] or r[1][:3] != [255, 255, 255] or r[2][:3] != [0, 0, 0] or r[3][:3] != [0, 0, 0]:
        raise AssertionError(f'Mask pixels: {r}')


@when('I click the mask box')
@when('I open the mask editor')
def open_mask_editor(ctx):
    ctx.app.js('document.querySelector("#maskBox").click();')


@then('the mask editor is open')
def me_open(ctx):
    ctx.app.wait('!document.querySelector("#maskEditor").hidden', 5, 'The mask editor is not open')


@then('the mask editor is closed')
def me_closed(ctx):
    ctx.app.wait('document.querySelector("#maskEditor").hidden', 5, 'The mask editor is still open')


ME_CANVAS = 'document.querySelector("#meWrap canvas")'


@when('I paint a mask stroke from {int}, {int} to {int}, {int}')
def me_stroke(ctx, x1, y1, x2, y2):
    ctx.app.js(f'__t.stroke({ME_CANVAS}, [[args[0], args[1]], [(args[0] + args[2]) / 2, (args[1] + args[3]) / 2], [args[2], args[3]]]);', x1, y1, x2, y2)


@when('I drag the window from {int}, {int} to {int}, {int}')
def me_drag(ctx, x1, y1, x2, y2):
    ctx.app.js(f'__t.stroke({ME_CANVAS}, [[args[0], args[1]], [args[2], args[3]]]);', x1, y1, x2, y2)


@when('I scroll the mouse wheel {word} over the mask editor')
def me_wheel(ctx, direction):
    ctx.app.js(f'''const c = {ME_CANVAS}; c.dispatchEvent(new WheelEvent("wheel", {{ deltaY: args[0], bubbles: true, cancelable: true, ...__t.client(c, 10, 10) }}));''',
               -100 if direction == 'up' else 100)


@then('the mask being edited has painted pixels around {int}, {int}')
def me_painted(ctx, x, y):
    a = ctx.app.js(f'return {ME_CANVAS}.getContext("2d").getImageData(args[0], args[1], 1, 1).data[3];', x, y)
    if a == 0:
        raise AssertionError(f'Pixel ({x}, {y}) of the mask is not painted')


@then('the mask being edited is empty')
def me_empty(ctx):
    if ctx.app.js(f'return (0, window.eval)("maskBounds")({ME_CANVAS});'):
        raise AssertionError('The mask being edited is not empty')


@then('the mask being edited covers the whole image')
def me_full(ctx):
    b = ctx.app.js(f'return (0, window.eval)("maskBounds")({ME_CANVAS});')
    w, h = input_wh(ctx)
    if b != {'x': 0, 'y': 0, 'w': w, 'h': h}:
        raise AssertionError(f'Mask bounds: {b}')


@then('the mask editor\'s active tool is {string}')
def me_tool(ctx, name):
    on = ctx.app.ev('[...document.querySelectorAll("#maskEditor .seg button.on")].map((b) => b.textContent)')
    if on != [name]:
        raise AssertionError(f'Active tool: {on}')


@then('the brush size of the mask editor is {int}')
def me_brush(ctx, n):
    got = ctx.app.ev('Number(document.querySelector("#meSize").value)')
    if got != n:
        raise AssertionError(f'Brush size is {got}')


@then('the mask editor shows {string}')
def me_info(ctx, text):
    ctx.app.wait('document.querySelector("#meCtxInfo").textContent === args[0]', 5,
                 lambda: f'Mask editor info: "{ctx.app.ev("document.querySelector(`#meCtxInfo`).textContent")}"', text)


@then('the mask editor shows no context window')
def me_no_window(ctx):
    if not ctx.app.ev('document.querySelector("#meCtx").hidden'):
        raise AssertionError('A context window is shown')


@then('the mask is displayed in {string}')
def mask_color(ctx, color):
    px = ctx.app.js('''
      const m = (0, window.eval)("input.mask"), b = (0, window.eval)("input.maskBounds");
      return [...m.getContext("2d").getImageData(b.x + (b.w >> 1), b.y + (b.h >> 1), 1, 1).data];
    ''')
    check_color(px, color, 'Mask display color', tol=1)


@when('I change the mask color in the mask editor to {string}')
def me_color(ctx, color):
    ctx.app.js('const c = document.querySelector("#meColor"); c.value = args[0]; c.dispatchEvent(new Event("input")); c.dispatchEvent(new Event("change"));', color)


@when('I remember the uploaded image name')
def remember_ref(ctx):
    from steps.generate import node
    ctx.vars['image_ref'] = node(ctx, 51)['inputs']['image']


@then('the workflow uses the same uploaded image')
def same_ref(ctx):
    from steps.generate import node
    got = node(ctx, 51)['inputs']['image']
    if got != ctx.vars['image_ref']:
        raise AssertionError(f'Uploaded image {got} differs from {ctx.vars["image_ref"]}')


# ---------- the context window (Focused inpainting) ----------
@then('the context window is {int}, {int} of size {size}')
def ctx_window(ctx, x, y, size):
    got = ctx.app.ev('(0, window.eval)("ctxBox()")')
    want = {'x': x, 'y': y, 'w': size[0], 'h': size[1]}
    if got != want:
        raise AssertionError(f'Context window: {got}')


@then('the context window has the aspect ratio of {size}')
def ctx_ratio(ctx, size):
    b = ctx.app.ev('(0, window.eval)("ctxBox()")')
    if abs(b['w'] / b['h'] - size[0] / size[1]) > 0.02:
        raise AssertionError(f'Context window {b["w"]}×{b["h"]}')


@then('the context window is shown on the mask box')
def ctx_on_box(ctx):
    # The dashed white outline is drawn over the mask preview at the window's edge.
    ok = ctx.app.js('''
      const c = document.querySelector("#maskBox canvas"), b = (0, window.eval)("ctxBox()"), k = c.width / (0, window.eval)("input.w");
      const d = c.getContext("2d").getImageData(Math.round(b.x * k + 1), Math.round(b.y * k + 1), Math.max(4, Math.round(b.w * k) - 2), 1).data;
      for (let i = 0; i < d.length; i += 4) if (d[i] > 240 && d[i + 1] > 240 && d[i + 2] > 240) return true;
      return false;
    ''')
    if not ok:
        raise AssertionError('No context window outline on the mask box')


# ---------- image editor ----------
IE_CANVAS = 'document.querySelector("#ieWrap canvas")'


@when('I click the input image')
@when('I open the image editor')
def open_ie(ctx):
    ctx.app.js('document.querySelector("#inputBox").click();')
    ctx.app.wait('!document.querySelector("#imageEditor").hidden', 5, 'The image editor did not open')


@then('the image editor is open')
def ie_open(ctx):
    ctx.app.wait('!document.querySelector("#imageEditor").hidden', 5, 'The image editor is not open')


@then('the image editor is closed')
def ie_closed(ctx):
    ctx.app.wait('document.querySelector("#imageEditor").hidden', 5, 'The image editor is still open')


@when('I set the paint color to {string}')
def ie_color(ctx, color):
    ctx.app.js('const c = document.querySelector("#ieColor"); c.value = args[0]; c.dispatchEvent(new Event("input"));', color)


@when('I set the brush size to {int}')
def ie_brush(ctx, n):
    ctx.app.js('const c = document.querySelector("#ieSize"); c.value = args[0]; c.dispatchEvent(new Event("input"));', n)


@when('I set the tolerance to {int}')
def ie_tol(ctx, n):
    ctx.app.js('const c = document.querySelector("#ieTol"); c.value = args[0]; c.dispatchEvent(new Event("input"));', n)


@when('I paint from {int}, {int} to {int}, {int}')
@when('I drag in the image editor from {int}, {int} to {int}, {int}')
def ie_stroke(ctx, x1, y1, x2, y2):
    ctx.app.js(f'__t.stroke({IE_CANVAS}, [[args[0], args[1]], [(args[0] + args[2]) / 2, (args[1] + args[3]) / 2], [args[2], args[3]]]);', x1, y1, x2, y2)


@when('I click the image editor at {int}, {int}')
def ie_click(ctx, x, y):
    ctx.app.js(f'__t.stroke({IE_CANVAS}, [[args[0], args[1]]]);', x, y)


@when('I alt-click the image editor at {int}, {int}')
def ie_alt_click(ctx, x, y):
    ctx.app.js(f'__t.stroke({IE_CANVAS}, [[args[0], args[1]]], {{ altKey: true }});', x, y)


@then('the edited image pixel at {int}, {int} is {string}')
def ie_pixel(ctx, x, y, color):
    px = ctx.app.js(f'return [...{IE_CANVAS}.getContext("2d").getImageData(args[0], args[1], 1, 1).data];', x, y)
    check_color(px, color, f'Edited pixel ({x}, {y})')


@then('the edited image pixel at {int}, {int} is unchanged')
def ie_pixel_same(ctx, x, y):
    same = ctx.app.js(f'''
      const a = {IE_CANVAS}.getContext("2d").getImageData(args[0], args[1], 1, 1).data;
      const b = await __t.pixel((0, window.eval)("input.blob"), args[0], args[1]);
      return [...a].slice(0, 3).every((v, i) => Math.abs(v - b[i]) <= 2) || [[...a], b];
    ''', x, y)
    if same is not True:
        raise AssertionError(f'Pixel ({x}, {y}) changed: {same}')


@then('the paint color is {string}')
def ie_color_is(ctx, color):
    got = ctx.app.ev('document.querySelector("#ieColor").value')
    if got.lower() != color.lower():
        raise AssertionError(f'The paint color is {got}')


@then('the recent colors are')
def ie_recent(ctx):
    want = [r[0].lower() for r in rows(ctx, header=False)]
    got = ctx.app.ev('[...document.querySelectorAll("#ieRecent button")].map((b) => b.title)')
    if got != want:
        raise AssertionError(f'Recent colors: {got}')


@when('I click the recent color {string}')
def ie_recent_click(ctx, color):
    ctx.app.js('[...document.querySelectorAll("#ieRecent button")].find((b) => b.title === args[0]).click();', color.lower())


@then('the image editor\'s active tool is {string}')
def ie_tool(ctx, name):
    on = ctx.app.ev('[...document.querySelectorAll("#imageEditor .seg button.on")].map((b) => b.textContent)')
    if on != [name]:
        raise AssertionError(f'Active tool: {on}')


@then('the selection is {int}, {int} of size {size}')
def ie_sel(ctx, x, y, size):
    got = ctx.app.ev('(0, window.eval)("ie.sel")')
    want = {'x': x, 'y': y, 'w': size[0], 'h': size[1]}
    if got != want:
        raise AssertionError(f'Selection: {got}')
    ctx.app.wait('document.querySelector("#ieInfo").textContent === args[0]', 5, None, f'Selection {size[0]}×{size[1]}')


@then('there is no selection')
def ie_no_sel(ctx):
    if ctx.app.ev('(0, window.eval)("ie.sel")'):
        raise AssertionError('There is a selection')
    if not ctx.app.ev('document.querySelector("#ieSel").hidden'):
        raise AssertionError('The selection is shown')


@then('the image editor zoom shows {string}')
def ie_zoom_info(ctx, text):
    got = ctx.app.ev('document.querySelector("#ieZoomInfo").textContent')
    if got != text:
        raise AssertionError(f'Zoom shows {got}')


@when('I remember the image editor zoom')
def ie_remember_zoom(ctx):
    ctx.vars['zoom'] = ctx.app.ev('(0, window.eval)("ie.zoom")')


@then('the image editor is zoomed {word}')
def ie_zoomed(ctx, direction):
    z = ctx.app.ev('(0, window.eval)("ie.zoom")')
    base = ctx.vars.get('zoom', 1)
    if (direction == 'in' and not z > base) or (direction == 'out' and not z < base):
        raise AssertionError(f'Zoom went from {base} to {z}')


@then('the image editor fits the image')
def ie_fit(ctx):
    z = ctx.app.ev('[(0, window.eval)("ie.zoom"), (0, window.eval)("ie.panX"), (0, window.eval)("ie.panY")]')
    if z != [1, 0, 0]:
        raise AssertionError(f'Zoom/pan: {z}')


@when('I scroll the mouse wheel {word} over the image editor at {int}, {int}')
def ie_wheel(ctx, direction, x, y):
    ctx.app.js(f'''const c = {IE_CANVAS}; document.querySelector("#ieStage").dispatchEvent(new WheelEvent("wheel", {{ deltaY: args[0], bubbles: true, cancelable: true, ...__t.client(c, args[1], args[2]) }}));''',
               -300 if direction == 'up' else 300, x, y)


@when('I drag the image editor stage by {int}, {int} screen pixels{any}')
def ie_pan(ctx, dx, dy, how):
    button = 1 if 'middle' in how else 0
    ctx.vars['pan0'] = ctx.app.ev('[(0, window.eval)("ie.panX"), (0, window.eval)("ie.panY")]')
    ctx.app.js('''
      const st = document.querySelector("#ieStage"), r = st.getBoundingClientRect();
      const x = r.left + r.width / 2, y = r.top + r.height / 2, o = { button: args[2] };
      __t.pointer(document.querySelector("#ieWrap canvas") || st, "pointerdown", { clientX: x, clientY: y }, o);
      __t.pointer(st, "pointermove", { clientX: x + args[0], clientY: y + args[1] }, o);
      __t.pointer(st, "pointerup", { clientX: x + args[0], clientY: y + args[1] }, o);
    ''', dx, dy, button)


@then('the image editor is panned by {int}, {int}')
def ie_panned(ctx, dx, dy):
    got = ctx.app.ev('[(0, window.eval)("ie.panX"), (0, window.eval)("ie.panY")]')
    x0, y0 = ctx.vars.get('pan0', [0, 0])
    if abs(got[0] - x0 - dx) > 0.5 or abs(got[1] - y0 - dy) > 0.5:
        raise AssertionError(f'Panned by {got[0] - x0:.1f}, {got[1] - y0:.1f}')


@when('I hold Space')
def hold_space(ctx):
    ctx.app.js('document.dispatchEvent(new KeyboardEvent("keydown", { key: " ", bubbles: true }));')


@when('I release Space')
def release_space(ctx):
    ctx.app.js('document.dispatchEvent(new KeyboardEvent("keyup", { key: " ", bubbles: true }));')


@then('the mask is painted at {int}, {int}')
def mask_painted(ctx, x, y):
    a = ctx.app.js('const m = (0, window.eval)("input.mask"); return m ? m.getContext("2d").getImageData(args[0], args[1], 1, 1).data[3] : -1;', x, y)
    if a <= 0:
        raise AssertionError(f'The mask is not painted at ({x}, {y})' if a == 0 else 'There is no mask')


@then('the mask is not painted at {int}, {int}')
def mask_not_painted(ctx, x, y):
    a = ctx.app.js('const m = (0, window.eval)("input.mask"); return m ? m.getContext("2d").getImageData(args[0], args[1], 1, 1).data[3] : -1;', x, y)
    if a > 0:
        raise AssertionError(f'The mask is painted at ({x}, {y})')


# ---------- Load from PNG ----------
def drop_on_main(ctx, spec):
    ctx.app.js('__t.drop(document.querySelector("#sec-main"), await __t.files([args[0]]));', spec)


@when('I drop a PNG made with that workflow on the Main section')
def drop_wf_png(ctx):
    import base64
    from ainvil_bdd.comfy import png_with_text, tiny_png
    png = png_with_text(tiny_png(), {'prompt': json.dumps(ctx.vars['wf'])})
    drop_on_main(ctx, {'b64': base64.b64encode(png).decode(), 'name': 'ComfyUI_00001_.png', 'type': 'image/png'})


@when('I change the workflow so node {int} {string} is {string}')
def edit_wf(ctx, nid, inp, value):
    ctx.vars['wf'][str(nid)]['inputs'][inp] = value


@when('I drop a PNG without metadata on the Main section')
def drop_plain_png(ctx):
    import base64
    from ainvil_bdd.comfy import tiny_png
    drop_on_main(ctx, {'b64': base64.b64encode(tiny_png()).decode(), 'name': 'plain.png', 'type': 'image/png'})


@when('I drop a JPEG image on the Main section')
def drop_jpeg(ctx):
    drop_on_main(ctx, image_spec('photo.jpg', (32, 32)))


@when('I drop a PNG with a prompt of another workflow on the Main section')
def drop_other_png(ctx):
    import base64
    from ainvil_bdd.comfy import png_with_text, tiny_png
    other = {'1': {'class_type': 'EmptyImage', 'inputs': {'width': 64, 'height': 64, 'batch_size': 1, 'color': 0}},
             '2': {'class_type': 'PreviewImage', 'inputs': {'images': ['1', 0]}}}
    png = png_with_text(tiny_png(), {'prompt': json.dumps(other)})
    drop_on_main(ctx, {'b64': base64.b64encode(png).decode(), 'name': 'other.png', 'type': 'image/png'})


@when('I drop some text on the Main section')
def drop_text_main(ctx):
    ctx.app.js('__t.drop(document.querySelector("#sec-main"), [], { text: "safe, dropped words" });')


@when('I drop the selected gallery image on the Main section')
def drop_gallery_png(ctx):
    ctx.app.js('''
      const it = (0, window.eval)("gallery.items")[(0, window.eval)("gallery.sel")];
      __t.drop(document.querySelector("#sec-main"), [new File([it.blob], it.filename, { type: "image/png" })]);
    ''')


@when('I remember the input image pixel at {int}, {int}')
def remember_pixel(ctx, x, y):
    ctx.vars['pixel'] = ctx.app.js('return await __t.pixel((0, window.eval)("input.blob"), args[0], args[1]);', x, y)


@then('the input image pixel at {int}, {int} is as remembered')
def pixel_as_remembered(ctx, x, y):
    px = ctx.app.js('return await __t.pixel((0, window.eval)("input.blob"), args[0], args[1]);', x, y)
    if any(abs(a - b) > 1 for a, b in zip(px[:3], ctx.vars['pixel'][:3])):
        raise AssertionError(f'Pixel ({x}, {y}) is {px}, was {ctx.vars["pixel"]}')


@when('I clear the input image')
def clear_input(ctx):
    ctx.app.click('Clear', 'the image column')


@when('I move the mouse over {int}, {int} in the mask editor')
def me_hover(ctx, x, y):
    ctx.app.js(f'const c = {ME_CANVAS}; __t.pointer(c, "pointermove", __t.client(c, args[0], args[1]), {{ buttons: 0 }});', x, y)


@then('the mask editor\'s cursor is {string}')
def me_cursor(ctx, cursor):
    got = ctx.app.ev(f'{ME_CANVAS}.style.cursor')
    if got != cursor:
        raise AssertionError(f'The cursor is {got!r}')
