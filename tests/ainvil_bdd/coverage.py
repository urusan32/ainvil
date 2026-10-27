"""Function coverage for index.html.

`instrument()` writes a copy of the page in which every named function (function declarations and the
methods of object literals such as `api`) starts by counting itself in window.__cov. The App harvests
the counts before every navigation, and `report()` lists which functions the suite never ran.
"""
import os
import re

_DECL = re.compile(r'(?m)^(\s*)(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)\s*\(')
_METHOD = re.compile(r'(?m)^(\s+)(?:async\s+)?([A-Za-z_$][\w$]*)\s*\(([^()]|\([^()]*\))*\)\s*\{')
_KEYWORDS = {'if', 'for', 'while', 'switch', 'catch', 'function', 'return', 'else', 'do', 'try', 'with'}


def _body_start(src, i):
    """Index just after the `{` that opens the function whose parameter list starts at src[i] == '('."""
    depth, j = 0, i
    while j < len(src):
        c = src[j]
        if c in '([{':
            depth += 1
        elif c in ')]}':
            depth -= 1
            if depth == 0 and c == ')':
                break
        elif c in '\'"`':
            q = c
            j += 1
            while j < len(src) and src[j] != q:
                j += 2 if src[j] == '\\' else 1
        j += 1
    k = src.index('{', j)
    return k + 1


def instrument(src):
    """Returns (instrumented html, sorted function names)."""
    start = src.index('<script>\n', src.index('id="default-custom-workflows"')) + len('<script>\n')
    end = src.index('</script>', start)
    code = src[start:end]
    inserts = []   # (position, name)
    for m in _DECL.finditer(code):
        name = m.group(2)
        inserts.append((_body_start(code, m.end() - 1), name))
    for m in _METHOD.finditer(code):
        name = m.group(2)
        if name in _KEYWORDS:
            continue
        line_start = code.rfind('\n', 0, m.start()) + 1
        if re.match(r'\s*(?:async\s+)?function\b', code[line_start:m.end()]):
            continue
        # object-literal methods only: the previous non-blank line ends with { or ,  (or }, after a method)
        prev = code[:line_start].rstrip()
        if not prev.endswith(('{', ',', '},')):
            continue
        inserts.append((m.end(), name))
    names, seen = [], {}
    for pos, name in sorted(set(inserts)):
        key = name
        if key in seen:
            seen[key] += 1
            key = f'{name}#{seen[name]}'
        else:
            seen[key] = 1
        names.append((pos, key))
    out, last = [], 0
    for pos, key in names:
        out.append(code[last:pos])
        out.append(f'__cov[{key!r}]=(__cov[{key!r}]||0)+1;')
        last = pos
    out.append(code[last:])
    pre = '<script>window.__cov = {};</script>\n'
    html = src[:start - len('<script>\n')] + pre + '<script>\n' + ''.join(out) + src[end:]
    return html, sorted(k for _, k in names)


class Coverage:
    def __init__(self, page_path, out_dir):
        src = open(page_path, encoding='utf-8').read()
        html, self.names = instrument(src)
        os.makedirs(out_dir, exist_ok=True)
        self.path = os.path.join(out_dir, 'index.html')
        with open(self.path, 'w', encoding='utf-8') as f:
            f.write(html)
        self.hits = {}

    def add(self, hits):
        for k, v in hits.items():
            self.hits[k] = self.hits.get(k, 0) + v

    def report(self, out):
        hit = [n for n in self.names if self.hits.get(n)]
        miss = [n for n in self.names if not self.hits.get(n)]
        pct = 100 * len(hit) / max(1, len(self.names))
        out(f'\nFunction coverage: {len(hit)} / {len(self.names)} ({pct:.1f}%)')
        if miss:
            out('Never called: ' + ', '.join(miss))
        return pct
