# Ainvil end-to-end tests

Integration tests that drive the real `index.html` in headless Firefox against a real ComfyUI server. The
scenarios are written in Gherkin (`features/*.feature`) so they can be read and audited without reading code;
the step definitions that carry them out are in `steps/`.

There is nothing to install: the Gherkin parser, the runner and the Firefox (Marionette) driver are small
Python standard-library modules in `ainvil_bdd/`.

## Running

```sh
python3 tests/run.py                                   # everything (about 10 minutes)
python3 tests/run.py --tags '~@gpu'                    # skip the scenarios that generate images
python3 tests/run.py tests/features/stash.feature      # one feature
python3 tests/run.py tests/features/stash.feature:61   # one scenario (its line number)
python3 tests/run.py -k "focused"                      # scenarios whose feature or name contains "focused"
python3 tests/run.py --coverage                        # also report which functions of index.html ran
python3 tests/run.py --dry-run                         # list scenarios and check that every step is defined
python3 tests/run.py --headed -x -v                    # watch it, stop at the first failure, print every step
```

Requirements:

- Firefox and Python 3.10+.
- A ComfyUI server started with `--enable-cors-header` (and `--preview-method auto` for the live preview
  scenario). The default is `http://10.0.0.137:8188/`; use `--server URL` or `AINVIL_TEST_SERVER` for another.
- The server needs what the scenarios name: the Anima models (`models/anima/anima_baseV10.safetensors`, …), the
  three Anima LoRAs, the OmniSR and Remacri upscale models and the comfyui-cads extension. MOSS is only used for
  building workflows, never generated.

A failing scenario prints the step that failed and why, and saves a screenshot to
`tests/.out/<feature>-<line>.png`. `tests/.out/` also holds the reused Firefox profile and the coverage copy of
the page; it is git-ignored.

## Safety on the shared server

- Every queued Generate prompt must contain `safe,`, and every Save Image node must save under `ainvil-test/`.
  A guard installed into the page refuses any other prompt before it reaches ComfyUI, so a mistake in a
  scenario fails the test instead of generating. (`Given test outputs go to the "ainvil-test" folder` sets the
  Filename prefix parameters to `ainvil-test/e2e/…`.)
- LoRAs are only used in scenarios that build workflows, never in generations.
- Nothing is ever deleted, on the server or locally. Uploads land in the server's `input/ainvil/` like any
  Ainvil upload.
- Generations are tiny (256×256, 4 steps) except where a scenario needs time to press Skip or Cancel.

## Tags

| Tag          | Meaning |
|--------------|---------|
| `@gpu`       | Runs generations on the server (a few seconds each). |
| `@js-errors` | The scenario expects the page to log uncaught errors; otherwise any uncaught error fails the scenario. |
| `@wip`       | Skipped unless asked for with `--tags @wip`. |

Tag expressions: `@a,@b` is either, `~@a` (or `not @a`) excludes, and `;` separates groups that must all match,
e.g. `--tags '@gpu;~@wip'`.

## How it works

- `ainvil_bdd/marionette.py` starts Firefox with `-marionette` and talks the Marionette protocol over a socket.
- `ainvil_bdd/app.py` wraps the page: `js()` runs code in the page's global scope (so the app's `gen`, `config`,
  `input`, … are visible), `wait()` polls in the page, and `reset()` gives every scenario a fresh Ainvil: empty
  localStorage and Image Stash, the built-in configuration pointed at the test server.
- `ainvil_bdd/page_helpers.js` is installed into the page after every load as `window.__t`. It records toasts,
  downloads (with their content, instead of saving files), confirmation dialogs and uncaught errors, and
  simulates what WebDriver can't do headless: file pickers, drag and drop of files, paste, and canvas strokes.
  It also finds buttons and fields the way a user does, by their visible text or label, optionally inside a
  named section.
- Layout drags use real WebDriver pointer actions; painting on the mask and image editors uses pointer events
  at image-pixel coordinates.
- `ainvil_bdd/comfy.py` talks to ComfyUI directly to check what Ainvil did (queue, uploads, object_info) and
  builds PNGs with ComfyUI-style `prompt`/`workflow` text chunks.
- `--coverage` runs an instrumented copy of the page in which every named function counts its calls, and lists
  the functions no scenario reached.

## Writing scenarios

Steps refer to the page the way the README does: buttons by their text, fields by their label, sections by
their heading.

```gherkin
When I click "Generate Workflow"
When I click "Clear" in the Output Gallery          # "in …" names a section when the text isn't unique
When I set "Seed" in Generation Parameters to "42"
When I fill in
  | Prompt | safe, a cat |
  | Width  | 512         |
  | Seed   | 7           | Generation Parameters |   # optional third column: the section
Then "Steps" shows "30"
Then the "Skip" button is hidden
Then a toast says "Seed set to 3002"
When I expand "txt2img of Anima"                    # "X of Y": section X inside section Y
```

Section names are the headings (`Main`, `Input Parameters`, `Custom Workflows (Extras)`, a functional workflow's
name, …) plus a few fixed ones: `the mask editor`, `the image editor`, `the viewer`, `the History`,
`the Image Stash`, `the jobs dialog`, `the layout bar`, `the image column`, `the mask column`, `Extras`,
`the Extras output`.

Workflow checks read the API prompt from the last "Generate Workflow" download:

```gherkin
When I download the workflow
Then the workflow sets
  | node | input | value   |
  | 19   | steps | 12      |
  | 11   | text  | "safe," |                 # values are JSON; /regex/ matches strings
And the sampler's model comes from "CADS ← LoRA bdl-AB10-01.safetensors ×0.8 ← UNETLoader"
```

Step patterns use `{string}`, `{int}`, `{float}`, `{word}`, `{size}` (`320×240`), `{any}` and `{where}`
(`in …`); see `ainvil_bdd/registry.py`. Test images are made in the page (a gradient, or flat colors with
rectangles) from their name and size, e.g. `Given an input image "photo.png" of 320×240 pixels`.

`fixtures/` holds workflow files used by the scenarios; `fixtures/make_fixtures.py` rebuilds the derived ones
from `workflows/txt2img-minworkflow.json`.
