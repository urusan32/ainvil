"""A small Gherkin parser: Feature, Background, Rule, Scenario, Scenario Outline/Template with Examples,
Given/When/Then/And/But/* steps, doc strings, data tables, tags and comments.
"""
import re
from dataclasses import dataclass, field


@dataclass
class Step:
    keyword: str          # Given / When / Then (And/But resolved to the previous one)
    raw_keyword: str      # as written
    text: str
    line: int
    doc: str = None
    table: list = None    # list of rows (lists of cells)


@dataclass
class Scenario:
    name: str
    line: int
    tags: list
    steps: list
    feature: 'Feature' = None
    rule: str = ''
    example: dict = None  # the Examples row of an outline


@dataclass
class Feature:
    name: str
    path: str
    tags: list
    description: str = ''
    background: list = field(default_factory=list)
    scenarios: list = field(default_factory=list)


class ParseError(Exception):
    pass


_KW = re.compile(r'^(Given|When|Then|And|But|\*)\s+(.*)$')


def _cells(line):
    s = line.strip()
    if not (s.startswith('|') and s.endswith('|')):
        raise ValueError(line)
    out, cur, i = [], '', 1
    while i < len(s) - 1:
        c = s[i]
        if c == '\\' and i + 1 < len(s) - 1:
            nxt = s[i + 1]
            cur += {'|': '|', 'n': '\n', '\\': '\\'}.get(nxt, '\\' + nxt)
            i += 2
            continue
        if c == '|':
            out.append(cur.strip())
            cur = ''
        else:
            cur += c
        i += 1
    out.append(cur.strip())
    return out


def parse(text, path='<string>'):
    lines = text.splitlines()
    feature = None
    pending_tags = []
    rule_name, rule_bg = '', []
    container = None     # list receiving steps
    outline = None       # (name, line, tags, steps) being collected
    examples_header = None
    examples_tags = []
    last_kw = None
    i = 0

    def finish_outline():
        nonlocal outline
        outline = None

    while i < len(lines):
        raw = lines[i]
        s = raw.strip()
        lineno = i + 1
        i += 1
        if not s or s.startswith('#'):
            continue
        if s.startswith('@'):
            pending_tags += [t for t in s.split() if t.startswith('@')]
            continue
        m = re.match(r'^(Feature|Background|Rule|Scenario Outline|Scenario Template|Scenario|Example|Examples|Scenarios):\s*(.*)$', s)
        if m:
            kw, name = m.group(1), m.group(2).strip()
            if kw == 'Feature':
                feature = Feature(name=name, path=path, tags=pending_tags)
                pending_tags = []
                desc = []
                while i < len(lines) and not re.match(r'^\s*(@|Background:|Scenario|Rule:|Example:|#)', lines[i]):
                    desc.append(lines[i].strip())
                    i += 1
                feature.description = '\n'.join(desc).strip()
                continue
            if feature is None:
                raise ParseError(f'{path}:{lineno}: content before Feature:')
            if kw == 'Background':
                finish_outline()
                container = rule_bg if rule_name else feature.background
                last_kw = None
                continue
            if kw == 'Rule':
                finish_outline()
                rule_name, rule_bg = name, []
                pending_tags = []
                container = None
                continue
            if kw in ('Scenario', 'Example'):
                finish_outline()
                sc = Scenario(name=name, line=lineno, tags=feature.tags + pending_tags, steps=[], feature=feature, rule=rule_name)
                sc.rule_background = list(rule_bg)
                feature.scenarios.append(sc)
                pending_tags = []
                container = sc.steps
                last_kw = None
                continue
            if kw in ('Scenario Outline', 'Scenario Template'):
                outline = {'name': name, 'line': lineno, 'tags': feature.tags + pending_tags, 'steps': [], 'rule': rule_name, 'rule_bg': list(rule_bg)}
                pending_tags = []
                container = outline['steps']
                last_kw = None
                continue
            if kw in ('Examples', 'Scenarios'):
                if outline is None:
                    raise ParseError(f'{path}:{lineno}: Examples outside a Scenario Outline')
                examples_header = None
                examples_tags = pending_tags
                pending_tags = []
                container = None
                # rows follow
                while i < len(lines):
                    t = lines[i].strip()
                    if not t or t.startswith('#'):
                        i += 1
                        continue
                    if not t.startswith('|'):
                        break
                    row = _cells(t)
                    if examples_header is None:
                        examples_header = row
                    else:
                        ex = dict(zip(examples_header, row))
                        steps = [_subst_step(st, ex) for st in outline['steps']]
                        label = ', '.join(f'{k}={v}' for k, v in ex.items())
                        sc = Scenario(name=f"{_subst(outline['name'], ex)} [{label}]", line=i + 1,
                                      tags=outline['tags'] + examples_tags, steps=steps, feature=feature,
                                      rule=outline['rule'], example=ex)
                        sc.rule_background = outline['rule_bg']
                        feature.scenarios.append(sc)
                    i += 1
                continue
        km = _KW.match(s)
        if km:
            if container is None:
                raise ParseError(f'{path}:{lineno}: step outside a scenario')
            raw_kw, body = km.group(1), km.group(2)
            kw = raw_kw if raw_kw in ('Given', 'When', 'Then') else (last_kw or 'Given')
            last_kw = kw
            step = Step(keyword=kw, raw_keyword=raw_kw, text=body, line=lineno)
            container.append(step)
            # doc string or table
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i < len(lines) and lines[i].strip() in ('"""', '```'):
                fence = lines[i].strip()
                indent = len(lines[i]) - len(lines[i].lstrip())
                i += 1
                doc = []
                while i < len(lines) and lines[i].strip() != fence:
                    doc.append(lines[i][indent:] if lines[i][:indent].strip() == '' else lines[i].strip())
                    i += 1
                i += 1
                step.doc = '\n'.join(doc)
            elif i < len(lines) and lines[i].strip().startswith('|'):
                rows = []
                while i < len(lines) and lines[i].strip().startswith('|'):
                    rows.append(_cells(lines[i]))
                    i += 1
                step.table = rows
            continue
        if container is None and feature is not None:
            continue  # free description text
        raise ParseError(f'{path}:{lineno}: cannot parse: {s}')
    if feature is None:
        raise ParseError(f'{path}: no Feature found')
    return feature


def _subst(s, ex):
    if s is None:
        return None
    return re.sub(r'<([^<>]+)>', lambda m: ex.get(m.group(1), m.group(0)), s)


def _subst_step(st, ex):
    return Step(keyword=st.keyword, raw_keyword=st.raw_keyword, text=_subst(st.text, ex), line=st.line,
                doc=_subst(st.doc, ex), table=[[_subst(c, ex) for c in r] for r in st.table] if st.table else None)
