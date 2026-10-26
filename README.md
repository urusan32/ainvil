# Ainvil

Ainvil is a single-page web app for common image generation workflows with ComfyUI: txt2img, img2img, and inpainting, plus LoRAs, batches, a mask painter, and an Extras tab for other workflows such as upscaling. Everything is in one `index.html` file. There's nothing to install or build.

## Quick start

1. Start ComfyUI with CORS enabled, so the page can talk to it:

   ```sh
   python main.py --listen --enable-cors-header
   ```

   You can also pass a specific origin instead of `*`, e.g. `--enable-cors-header http://myhost:8080`.
2. Open `index.html` in Firefox or Chrome/Chromium. Opening it from disk (`file://`) works, and so does any static web server.
3. Go to **Configuration › Connection**, enter the ComfyUI URL (default `http://localhost:8188/`), then click **Save** and **Test Connection**. **Auto-Configure** detects optional server features such as CADS and live preview (start ComfyUI with `--preview-method auto` to get live previews).
4. Go back to **Generate**, write a prompt and press **Generate** (or Ctrl+Enter in the prompt box).

## Generate tab

- **Main**: choose the functional workflow and model, write the prompt and negative prompt, and set the batch count (1–128 separate queue entries).
  - The **Search** box next to the model list shows only models whose names contain all the words you type.
  - **Clear** resets the page.
  - **Generate Workflow** downloads the ComfyUI API-format workflow for the first image instead of running it.
  - Drop a PNG made by Ainvil (or ComfyUI with the same workflow) onto the Main section to use it as a template. This loads its prompts, model, generation parameters, LoRAs and custom parameters. For img2img and inpainting it also loads the input image and mask, if they are still in the server's `input/` folder. The seed is loaded with Random turned off. A `%date:…%` filename prefix is kept as the template, not replaced by its expanded value.
- **Generation Parameters**: resolution presets (1024 / 1536 × Square / Landscape / Portrait / WS Landscape / WS Portrait, or Custom; the widescreen (WS) sizes are about 16:9, in multiples of 64), seed (with a Random toggle), batch size, steps, CFG, sampler and scheduler.
- **Input Image**: drop, choose or paste an image to switch to **img2img**.
  - Click the mask box to paint a mask, which switches to **inpainting**.
  - In the mask editor: `[` and `]` change the brush size, `x` toggles erase, Ctrl+Z undoes.
  - Masks can also be uploaded or downloaded. They are white-on-black PNGs, where white means "regenerate".
  - If the mask color is hard to see on your image, change it with **Color** in the mask editor (or in *Client Preferences*). This only changes how the mask is displayed.
- **Input Parameters**: denoise is set as a *start step*.
  - With 30 steps, step 12 is denoise 0.60. The value field, step field and slider stay in sync.
  - Moving the slider right increases the denoise.
  - Crop and Noise Mask apply to img2img and inpainting.
- **Output Gallery**: shows the latest run.
  - Click the large image for a full-screen view: arrow keys browse and Esc closes. Save with the viewer's **Download** button or by right-clicking.
  - When the page is served over http(s), right-click › *Save Image As* uses the image's real filename. Opened from disk (`file://`), Firefox can only show the image as a nameless blob, so use **Download** or right-click › *Save Link As* to get the real filename.
  - **Download All** downloads the whole run as a ZIP file.
  - **Use Seed** copies the selected image's seed into the Seed field. **Use as Input** loads the image as the input image for img2img. **Send to Extras** adds it to the current Extras workflow's images and switches to Extras. **Clear** empties the gallery (the files stay on the server).
- **LoRA**: add any number of LoRAs from the server, filtered to the workflow's model family, with a weight for each.
  - The search box narrows every LoRA list to names containing the words you type, and **+ Add LoRA** adds the first match.
  - The **On/Off** button keeps a LoRA in the list without using it.
- **Custom Parameters**: extra settings defined by the selected workflow. Anima and MOSS have *Resize method* and *Filename prefix*; MOSS also has the Skip Layer Guidance settings (*Skip layer guidance* on/off, off by default, plus its layers and start/end percent).
- **CADS** (Condition-Annealed Diffusion Sampler): adds scheduled noise to the conditioning for more varied images. It needs the [comfyui-cads](https://github.com/asagi4/ComfyUI-CADS) extension on the server and a workflow with a CADS node (the built-in Anima and MOSS workflows have one).
  - **Enable CADS** turns it on or off (off by default). When it's off, unsupported by the server (*Server Features › CADS*), or not configured for the workflow, the CADS node is bypassed and the section says why.
  - The settings start at the workflow's CADS node values. **Total steps** follows the main Steps whenever Steps changes, but changing it doesn't change Steps. With **Automatic** checked (the default), the CADS seed follows the image seed; uncheck it to use the CADS Seed field as is.

The page remembers your Generate settings (not images) between visits.

## Extras tab

Runs a *custom workflow*: any ComfyUI workflow with parameters you define in *Configuration › Custom Workflows*. Pick the workflow, fill in its parameters and press **Run**. **Generate Workflow** downloads the API-format workflow for the first image instead, and **Clear** resets the parameters and removes the images.

- **Image** parameters take one or more images: drop them, choose them, or paste one. With several images the workflow runs once per image (a batch conversion), each as its own queue entry. Remove an image with its ✕.
- Combo parameters list the options from the server. Lists of files, such as models, also get a **Search** box.
- **Output** shows the results like the Output Gallery, with the input image name and output size. Click for the full-screen viewer, or use **Download Selected** / **Download All** (ZIP). **Use as Input** loads the selected result as the Generate tab's input image.

The built-in **Upscale with model** workflow upscales with an upscale model, then resizes to a target size:

- **Upscale model**: the model's fixed factor (2x, 4x, …; the model name usually says which) is applied first.
- **Model upscale only**: skip the final resize and keep the model's output size (e.g. 4× the input). Width, Height, Final resize method and Crop are then ignored.
- **Width** / **Height**: the final size. Set one of them to 0 to keep the image's aspect ratio, which is what you want for a batch of differently shaped images.
- **Final resize method** and **Crop** (`center` crops to the target aspect ratio instead of stretching).
- **Filename prefix**: `%input%` is replaced by the input image name, so batch outputs keep their names.

The Extras settings are remembered between visits, the images are not.

## Configuration

Configuration is stored in the browser's `localStorage` and can be moved between computers:

- **Global Import & Export**: export everything as one JSON file, or import a file to replace the current configuration.
- **Client Preferences**: number of gallery thumbnails per row (2, 3 or 4), rows shown before the thumbnails scroll (1 or 2), the mask display color, and whether to show the live preview in the gallery while generating.
- **Functional Workflows**: each one has a name and model/LoRA filters (regular expressions, case-insensitive). It also has three ComfyUI workflows (txt2img, img2img, inpainting) with *mappings* that say which node input receives each Generate-tab value. Workflows can be loaded from ComfyUI's JSON (UI or API format) or from a ComfyUI PNG. **Auto-detect mappings** makes a good first guess for standard graphs.
- **Custom Workflows**: open-ended workflows for the Extras tab. Each has a ComfyUI workflow and a list of parameters, each with a name, a type (int, float, string, text, boolean, combo or image), a default, and the node input(s) it sets. An empty default uses the value in the workflow. Combos can have a regex filter (like the model filter), and any parameter can have help text, shown under it in Extras. **+ Built-in examples** adds back the built-in custom workflows (Upscale with model) if they are missing.

Each workflow can be exported and imported on its own. All exported files carry `"version": 1`.

### Mapping notes

- **LoRA template**: the sample LoRA loader node in your workflow. It is removed when no LoRAs are selected, and otherwise cloned and chained once per LoRA.
- **Batch repeat**: for workflows without an Empty Latent Image (img2img and inpainting), batch size works by inserting a `RepeatLatentBatch` node in front of the mapped latent input.
- **Output image**: Save Image nodes become Preview Image nodes when *Server Preferences › Save Image* is off.
- **CADS**: the CADS node, set from the CADS section. When CADS is off it is removed and its model input is passed straight through. Leave it unmapped for workflows without CADS.
- **Inpainting**: the mask is sent as the input image's alpha channel (via ComfyUI's `/upload/mask`), so the Load Image node's MASK output carries it.
- **Filename prefixes**: `%date:yyyyMMdd%` and `%Node title.widget%` are expanded by Ainvil, the same way the ComfyUI frontend does it. In custom workflows, `%input%` is the input image name.

## Troubleshooting

- **"Could not reach ComfyUI"**: check the URL and that ComfyUI is running with `--enable-cors-header`.
- **Images or uploads fail only in the browser**: this is almost always CORS. The page fetches images through the API, so they need CORS too.
- **"Mapping … points at node #N"**: the workflow was replaced and the mapping is stale. Re-map it in Configuration.

## Development

The default Anima workflows live in `workflows/` (`*-minworkflow-cads.json`; the plain `*-minworkflow.json` files are the same graphs without CADS) and are embedded into `index.html`. The MOSS workflows (`moss-*-minworkflow-cads.json`) are derived from the Anima ones. The Upscale with model custom workflow is `workflows/upscale_with_model.json`. After editing them, run:

```sh
python3 tools/make-moss-workflows.py   # after changing the Anima workflows
python3 tools/embed-workflows.py
```
