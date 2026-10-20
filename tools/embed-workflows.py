#!/usr/bin/env python3
"""Embed workflows/*-minworkflow.json into index.html as the default Anima workflows.

Usage: python3 tools/embed-workflows.py
"""
import json
import pathlib
import re

root = pathlib.Path(__file__).resolve().parent.parent
wfs = {
    mode: json.loads((root / "workflows" / f"{mode}-minworkflow.json").read_text())
    for mode in ("txt2img", "img2img", "inpainting")
}
blob = json.dumps(wfs, separators=(",", ":")).replace("</", "<\\/")
html_path = root / "index.html"
html = html_path.read_text()
pattern = re.compile(r'(<script type="application/json" id="default-workflows">)(.*?)(</script>)', re.S)
if not pattern.search(html):
    raise SystemExit("default-workflows block not found in index.html")
html = pattern.sub(lambda m: m.group(1) + blob + m.group(3), html, count=1)
html_path.write_text(html)
print(f"Embedded {len(blob):,} bytes of workflows into {html_path.name}")
