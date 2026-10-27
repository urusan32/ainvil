"""Step definition registry.

Patterns use a small subset of Cucumber expressions:
  {string}  a "double-quoted" string (str)       {int}    an integer (int)
  {float}   a number (float)                     {word}   one word without spaces (str)
  {size}    WxH or W×H (tuple of ints)           {any}    any text (str)
  {where}   "in …" / "on …": a section of the page (str)
  (s)       an optional "s" (image/images)
A pattern starting with ^ is taken as a plain regular expression instead. When a step matches several
definitions, one without {any}/{where} wins over the generic ones; otherwise it is ambiguous.
"""
import re

STEPS = []      # (keyword, compiled regex, converters, func, pattern)
HOOKS = {'before_all': [], 'after_all': [], 'before_scenario': [], 'after_scenario': []}

_PARAMS = {
    'string': (r'"((?:[^"\\]|\\.)*)"', lambda s: re.sub(r'\\(.)', r'\1', s)),
    'int': (r'(-?\d+)', int),
    'float': (r'(-?\d+(?:\.\d+)?)', float),
    'word': (r'(\S+)', str),
    'size': (r'(\d+\s*[x×]\s*\d+)', lambda s: tuple(int(v) for v in re.split(r'\s*[x×]\s*', s))),
    'any': (r'(.*?)', str),
    'where': (r'((?:in|on) .+?)', str),
}


def _compile(pattern):
    if pattern.startswith('^'):
        return re.compile(pattern), None
    out, conv, i = '^', [], 0
    for m in re.finditer(r'\{(\w+)\}|\(s\)', pattern):
        out += re.escape(pattern[i:m.start()])
        if m.group(0) == '(s)':
            out += '(?:s)?'
        else:
            rx, fn = _PARAMS[m.group(1)]
            out += rx
            conv.append(fn)
        i = m.end()
    out += re.escape(pattern[i:]) + '$'
    return re.compile(out), conv


def _register(keyword):
    def deco(*patterns):
        def wrap(fn):
            for p in patterns:
                rx, conv = _compile(p)
                STEPS.append((keyword, rx, conv, fn, p))
            return fn
        return wrap
    return deco


given = _register('Given')
when = _register('When')
then = _register('Then')
step = _register('*')


def hook(name):
    def wrap(fn):
        HOOKS[name].append(fn)
        return fn
    return wrap


class Undefined(Exception):
    pass


class Ambiguous(Exception):
    pass


def find(keyword, text):
    """Returns (func, args). Steps registered for a keyword also match And/But after it; '*' matches any."""
    hits = []
    for kw, rx, conv, fn, pat in STEPS:
        if kw not in (keyword, '*'):
            continue
        m = rx.match(text)
        if not m:
            continue
        groups = m.groups()
        args = [c(g) for c, g in zip(conv, groups)] if conv is not None else list(groups)
        hits.append((fn, args, pat))
    if not hits:
        # Fall back to the other keywords: "Then" steps are sometimes useful as "Given" preconditions.
        for kw, rx, conv, fn, pat in STEPS:
            m = rx.match(text)
            if m:
                groups = m.groups()
                args = [c(g) for c, g in zip(conv, groups)] if conv is not None else list(groups)
                hits.append((fn, args, pat))
    if not hits:
        raise Undefined(f'{keyword} {text}')
    fns = {id(h[0]) for h in hits}
    if len(fns) > 1:
        # A specific step wins over the generic "… {where}" / "{any}" ones.
        specific = [h for h in hits if '{any}' not in h[2] and '{where}' not in h[2]]
        if len({id(h[0]) for h in specific}) == 1:
            return specific[0][0], specific[0][1]
        raise Ambiguous(f'{keyword} {text}\n  matches: ' + '\n           '.join(h[2] for h in hits))
    return hits[0][0], hits[0][1]
