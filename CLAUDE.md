# Ainvil — notes for Claude sessions

The spec is `DESIGN.md`. The user-facing docs are `README.md`.

## Shape
- Everything is in `index.html`: CSS, markup, and one inline `<script>`. There's no build step and no dependencies. Ask the user before adding any.
- The default Anima workflows (ComfyUI **UI format**) sit in `<script type="application/json" id="default-workflows">`. They're generated from `workflows/*-minworkflow.json` by `tools/embed-workflows.py`, so don't hand-edit that blob.
- The app default is `http://localhost:8188/`.

## Key design decisions
- **Workflows are stored as provided** (UI or API format). `toApi()` converts UI→API at use time:
  - It handles links, Reroute, PrimitiveNode, muted (mode 2) and bypassed (mode 4) nodes.
  - For widget values it prefers `widgets_values_named`, then `/object_info` input order, skipping `control_after_generate` values.
  - Subgraphs are rejected.
- **Mappings** are `{node, input}` targets keyed by functional parameter, one set per mode. Node ids are the same in UI and API format. The parameter list is `FPARAMS`. Structural parameters:
  - `lora` clones and chains the template node; zero LoRAs remove it.
  - `batch_repeat` inserts `RepeatLatentBatch`.
  - `output` swaps SaveImage→PreviewImage when saveImage is off.
- **Denoise** is shown as a start step: `denoise = 1 - step/steps`. In txt2img it is always 1.
- **Inpainting**: the image is uploaded with `/upload/image`. The mask is then uploaded with `/upload/mask` and `original_ref`, which writes alpha = 255 - mask into a server-side copy. This keeps the original RGB under the mask; client-side alpha compositing would lose it to premultiplication. Uploads go to `input/ainvil/` with content-hash names and are cached per server.
- **Images** are fetched with CORS into blob URLs. Firefox blocks `<img src="http://…">` from `file://` pages.
- `%date:…%` / `%Title.widget%` in `filename_prefix` are expanded client-side, because the ComfyUI server doesn't do it.
- Completion is detected by polling `/history/{id}`. The WebSocket is only used for progress and queue display.
- Combo options (models, samplers, LoRAs, custom combos) come from `/object_info` for the mapped node's class/input. Models and LoRAs are then filtered by the workflow's regex.
- `clientPreferences` in the config holds gallery columns/rows and the mask display color. The mask canvas's RGB is only for display (`recolorMask()`): only alpha is the mask, so changing the color doesn't change upload hashes.
- The full-screen viewer tries the direct `/view` URL first, because ComfyUI's `Content-Disposition` filename then names "Save Image As". From `file://`, Firefox refuses it, so the viewer falls back to the blob URL inside an `<a download>` link.
- **Load from PNG** (drop on `#sec-main`, `loadSettingsFromPng`): reads the API `prompt` chunk, then `matchPrompt()` picks the fw/mode whose template nodes match by id + class. LoRA clones, RepeatLatentBatch and SaveImage↔PreviewImage don't count against the match. Values are read back through the mappings. For our inpainting uploads (`ainvil_<hash>_m<mh>.png`), the RGB comes from the original `ainvil_<hash>.*` (alpha premultiplication again), and the mask is `255 - alpha` of the `_m` file. Custom values that are just the expansion of a `%…%` template are not loaded.
- Model/LoRA **search** (`searchList`, plain words, AND) runs on top of the workflow's regex filter (`filterList`).
- Config schema version is `CONFIG_VERSION = 1`; keep it at 1 during alpha. localStorage keys: `ainvil.config`, `ainvil.generate` (form state), `ainvil.tab`.
- The Generate layout is 3, 2 or 1 columns. `LAYOUTS` moves the section elements between columns, and the dynamic-height sections (Custom Parameters, LoRA) sit at the bottom of their columns.

## Not done yet
- Extras tab UI (custom workflows can be configured but not run).
- CADS (only a placeholder section plus the server feature toggle).

## Testing
Headless Firefox driven over Marionette (raw socket, Python stdlib) works well for end-to-end checks against the test server.
- Start Firefox with `-remote-allow-system-access` if you need the chrome context (e.g. to inspect `gContextMenu`).
- Top-level `let`/`const` (`gen`, `config`, `gallery`) aren't on `window`; read them with an indirect `(0, window.eval)(…)`.
- Include `safe,` in every test prompt.
- Set the Filename prefix custom parameter to `ainvil-test/...` so test outputs land in one folder.
- Never delete outputs or other files while testing; the user cleans up.
