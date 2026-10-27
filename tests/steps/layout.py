"""Generate layout steps: columns, dragging sections by their headers, hiding and showing them."""
from ainvil_bdd.registry import then, when
from steps.common import rows

SECTION = '''(() => {
  const s = [...document.querySelectorAll("#genColumns .card, #sectionPool .card")].find((c) => c.dataset.name === args[0]);
  if (!s) throw new Error("No section " + args[0]);
  return s;
})()'''


@then('the Generate columns are')
def columns(ctx):
    want = [[x.strip() for x in r[0].split(',')] for r in rows(ctx, header=False)]
    got = ctx.app.ev('[...document.querySelectorAll("#genColumns > .column")].map((c) => [...c.children].map((s) => s.dataset.name))')
    if got != want:
        raise AssertionError(f'Columns: {got}')


def header_point(ctx, name):
    return ctx.app.js(f'''
      const h = {SECTION}.querySelector(":scope > h2");
      h.scrollIntoView({{ block: "center" }});
      const r = h.getBoundingClientRect();
      return [r.left + 30, r.top + r.height / 2];
    ''', name)


@when('I drag the {string} section above the {string} section')
def drag_above(ctx, name, target):
    a = header_point(ctx, name)
    b = ctx.app.js(f'const r = {SECTION}.getBoundingClientRect(); return [r.left + 40, r.top + 8];', target)
    ctx.app.mouse_drag([a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), b])


@when('I drag the {string} section to the bottom of column {int}')
def drag_bottom(ctx, name, col):
    a = header_point(ctx, name)
    b = ctx.app.js('''
      const c = document.querySelectorAll("#genColumns > .column")[args[0] - 1], last = c.lastElementChild.getBoundingClientRect();
      return [c.getBoundingClientRect().left + 40, Math.min(window.innerHeight - 60, last.bottom - 4)];
    ''', col)
    ctx.app.mouse_drag([a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), b])


@when('I start dragging the {string} section and press Escape')
def drag_escape(ctx, name):
    a = header_point(ctx, name)
    m = ctx.app.m
    m.command('WebDriver:PerformActions', {'actions': [{'type': 'pointer', 'id': 'mouse', 'parameters': {'pointerType': 'mouse'}, 'actions': [
        {'type': 'pointerMove', 'duration': 0, 'x': int(a[0]), 'y': int(a[1]), 'origin': 'viewport'},
        {'type': 'pointerDown', 'button': 0},
        {'type': 'pointerMove', 'duration': 100, 'x': int(a[0]) + 600, 'y': int(a[1]) + 40, 'origin': 'viewport'}]}]})
    ctx.app.js('__t.key("Escape", {}, document.body);')
    m.command('WebDriver:ReleaseActions')


@when('I click {string} on the {string} section')
def click_section_tool(ctx, button, name):
    ctx.app.js(f'''
      const b = {SECTION}.querySelector(":scope > h2 .sec-vis");
      if (!__t.visible(b)) throw new Error("The section tools are not shown");
      if (b.textContent !== args[1]) throw new Error("The button says " + b.textContent);
      b.click();
    ''', name, button)


@then('the {string} section is {word}')
def section_state(ctx, name, state):
    got = ctx.app.js(f'''
      const s = {SECTION};
      return {{ shown: __t.visible(s), marked: s.classList.contains("sec-hidden") && __t.visible(s.querySelector(".sec-tag")) }};
    ''', name)
    ok = {'shown': got['shown'] and not got['marked'], 'hidden': not got['shown'], 'marked': got['shown'] and got['marked']}[state]
    if not ok:
        raise AssertionError(f'The {name} section is not {state}: {got}')


@then('the layout editor is {word}')
def layout_editing(ctx, state):
    on = ctx.app.ev('!document.querySelector("#layoutBar").hidden && document.querySelector("#genColumns").classList.contains("editing")')
    if on != (state == 'open'):
        raise AssertionError(f'The layout editor is {"open" if on else "closed"}')


@then('the {string} section is shown dimmed and marked "Hidden"')
def section_marked(ctx, name):
    section_state(ctx, name, 'marked')
