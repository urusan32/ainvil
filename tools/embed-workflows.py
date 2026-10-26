#!/usr/bin/env python3
"""Embed the default workflows into index.html.

Functional workflows (id="default-workflows"), keyed by functional workflow:
  Anima: workflows/{mode}-minworkflow-cads.json
  MOSS:  workflows/moss-{mode}-minworkflow-cads.json (made by tools/make-moss-workflows.py)

Custom workflows for the Extras tab (id="default-custom-workflows"), keyed by file stem:
  workflows/upscale_with_model.json

The plain *-minworkflow.json files are the Anima workflows without the CADS node.

Usage: python3 tools/embed-workflows.py
"""
import json
import pathlib
import re

root = pathlib.Path(__file__).resolve().parent.parent
sets = {"Anima": "", "MOSS": "moss-"}
custom = ["upscale_with_model"]
blocks = {
    "default-workflows": {
        name: {
            mode: json.loads((root / "workflows" / f"{prefix}{mode}-minworkflow-cads.json").read_text())
            for mode in ("txt2img", "img2img", "inpainting")
        }
        for name, prefix in sets.items()
    },
    "default-custom-workflows": {
        stem: json.loads((root / "workflows" / f"{stem}.json").read_text()) for stem in custom
    },
}
html_path = root / "index.html"
html = html_path.read_text()
for block_id, wfs in blocks.items():
    blob = json.dumps(wfs, separators=(",", ":")).replace("</", "<\\/")
    pattern = re.compile(rf'(<script type="application/json" id="{block_id}">)(.*?)(</script>)', re.S)
    if not pattern.search(html):
        raise SystemExit(f"{block_id} block not found in index.html")
    html = pattern.sub(lambda m: m.group(1) + blob + m.group(3), html, count=1)
    print(f"Embedded {len(blob):,} bytes of workflows into {html_path.name} #{block_id}")
html_path.write_text(html)
