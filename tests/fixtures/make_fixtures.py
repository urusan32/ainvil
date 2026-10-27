#!/usr/bin/env python3
"""Builds the test workflow fixtures from workflows/txt2img-minworkflow.json (run after changing that file).

txt2img-frontend-nodes.json: the plain Anima txt2img graph with the frontend-only constructs toApi() must resolve:
  - #70 Reroute between #8 VAEDecode and #46 SaveImage
  - #71 PrimitiveNode (7) driving KSampler #19's "steps" widget
  - #49 LoraLoaderModelOnly bypassed (mode 4): its MODEL passes #44's straight through
  - #72 PreviewImage muted (mode 2): left out
  - #73 Note: left out
  - #74 an unknown node type that feeds nothing: dropped as frontend-only
txt2img-api.json: the same graph as an API-format prompt (what ComfyUI's "Export (API)" writes).
"""
import copy
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', '..', 'workflows', 'txt2img-minworkflow.json')


def main():
    wf = json.load(open(SRC))
    nodes = {n['id']: n for n in wf['nodes']}
    links = wf['links']
    nl = max(l[0] for l in links)

    def new_link(o, os_, t, ts, typ):
        nonlocal nl
        nl += 1
        links.append([nl, o, os_, t, ts, typ])
        return nl

    # Reroute #70: 8 -> 70 -> 46
    old = next(l for l in links if l[1] == 8 and l[3] == 46)
    links.remove(old)
    a = new_link(8, 0, 70, 0, 'IMAGE')
    b = new_link(70, 0, 46, 0, 'IMAGE')
    nodes[8]['outputs'][0]['links'] = [a]
    next(i for i in nodes[46]['inputs'] if i['name'] == 'images')['link'] = b
    wf['nodes'].append({'id': 70, 'type': 'Reroute', 'pos': [1300, 700], 'size': [75, 26], 'flags': {}, 'order': 10, 'mode': 0,
                        'inputs': [{'name': '', 'type': '*', 'link': a}], 'outputs': [{'name': '', 'type': 'IMAGE', 'links': [b]}],
                        'properties': {'showOutputText': False, 'horizontal': False}})
    # PrimitiveNode #71 -> KSampler.steps
    c = new_link(71, 0, 19, 5, 'INT')
    next(i for i in nodes[19]['inputs'] if i['name'] == 'steps')['link'] = c
    wf['nodes'].append({'id': 71, 'type': 'PrimitiveNode', 'pos': [700, 900], 'size': [210, 82], 'flags': {}, 'order': 0, 'mode': 0,
                        'inputs': [], 'outputs': [{'name': 'INT', 'type': 'INT', 'links': [c], 'widget': {'name': 'steps'}}],
                        'title': 'Steps', 'properties': {'Run widget replace on values': False}, 'widgets_values': [7, 'fixed']})
    # Bypass the LoRA #49
    nodes[49]['mode'] = 4
    # Muted PreviewImage #72 on the decoded image
    d = new_link(8, 0, 72, 0, 'IMAGE')
    nodes[8]['outputs'][0]['links'].append(d)
    wf['nodes'].append({'id': 72, 'type': 'PreviewImage', 'pos': [1300, 900], 'size': [210, 246], 'flags': {}, 'order': 11, 'mode': 2,
                        'inputs': [{'name': 'images', 'type': 'IMAGE', 'link': d}], 'outputs': [], 'properties': {}})
    wf['nodes'].append({'id': 73, 'type': 'Note', 'pos': [0, 0], 'size': [200, 60], 'flags': {}, 'order': 12, 'mode': 0,
                        'inputs': [], 'outputs': [], 'properties': {}, 'widgets_values': ['A note for humans']})
    wf['nodes'].append({'id': 74, 'type': 'SomeFrontendWidget', 'pos': [0, 100], 'size': [200, 60], 'flags': {}, 'order': 13, 'mode': 0,
                        'inputs': [], 'outputs': [{'name': 'X', 'type': 'X', 'links': []}], 'properties': {}, 'widgets_values': []})
    wf['last_node_id'] = 74
    wf['last_link_id'] = nl
    with open(os.path.join(HERE, 'txt2img-frontend-nodes.json'), 'w') as f:
        json.dump(wf, f, indent=1)

    # API format of the plain graph.
    plain = json.load(open(SRC))
    nodes = {n['id']: n for n in plain['nodes']}
    lk = {l[0]: l for l in plain['links']}
    api = {}
    for n in plain['nodes']:
        inputs = dict(n.get('widgets_values_named') or {})
        inputs.pop('control_after_generate', None)
        for i in n.get('inputs', []):
            if i.get('link') is not None:
                l = lk[i['link']]
                inputs[i['name']] = [str(l[1]), l[2]]
        api[str(n['id'])] = {'class_type': n['type'], 'inputs': inputs, '_meta': {'title': n.get('title') or n['type']}}
    with open(os.path.join(HERE, 'txt2img-api.json'), 'w') as f:
        json.dump(api, f, indent=1)


if __name__ == '__main__':
    main()
