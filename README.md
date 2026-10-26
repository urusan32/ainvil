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
  - Click the image to edit it: **Paint**, **Erase** (paints the original back), **Fill** (flood fill; **Tolerance** sets how similar a pixel must be to the one you clicked) and **Select** (a rectangle; Paint, Erase and Fill stay inside it). Alt+click picks a color. **Done** makes the edited image the input image and adds it to the Image Stash; **Cancel** discards the edits. With a selection, **Crop** crops the edited image (and the mask) to it instead. Keys: `b` Paint, `x` toggles Erase, `f` Fill, `s` Select, Ctrl+D deselects, `[`/`]` brush size, Ctrl+Z undo.
  - Click the mask box to paint a mask, which switches to **inpainting**.
  - In the mask editor: `[` and `]` change the brush size, `x` toggles erase, `w` toggles the Window tool (Manual Select), Ctrl+Z undoes.
  - Masks can also be uploaded or downloaded. They are white-on-black PNGs, where white means "regenerate".
  - If the mask color is hard to see on your image, change it with **Color** in the mask editor (or in *Client Preferences*). This only changes how the mask is displayed.
- **Input Parameters**: denoise is set as a *start step*.
  - With 30 steps, step 12 is denoise 0.60. The value field, step field and slider stay in sync.
  - Moving the slider right increases the denoise.
  - Crop and Noise Mask apply to img2img and inpainting.
  - **Inpaint area**: *Whole Image* resizes the whole image to the generation size and inpaints it. *Focused* (also known as "Only Masked") inpaints just a *context window* around the mask at the full generation size, then scales the result back and pastes it into the image, so small details get the model's full resolution. Pixels outside the mask are left exactly as they were.
  - **Context window** (Focused): *By Size* uses the mask's bounding box plus a border of *Context window size* pixels, widened to the generation aspect ratio. *Manual Select* lets you place it in the mask editor with the **Window** tool: drag inside to move it, drag a corner to resize it, drag outside to draw a new one, or use the mouse wheel. It always keeps the generation aspect ratio. While the Window tool is on, **Crop** crops the image (and the mask) to the window, makes that the input image and adds it to the Image Stash. The window shows as a dashed box on the mask and in the editor.
- **Output Gallery**: shows the latest run.
  - Click the large image for a full-screen view: arrow keys browse and Esc closes. Save with the viewer's **Download** button or by right-clicking.
  - When the page is served over http(s), right-click › *Save Image As* uses the image's real filename. Opened from disk (`file://`), Firefox can only show the image as a nameless blob, so use **Download** or right-click › *Save Link As* to get the real filename.
  - **Download All** downloads the whole run as a ZIP file.
  - **Use Seed** copies the selected image's seed into the Seed field. **Use as Input** loads the image as the input image for img2img. **Send to Extras** adds it to the current Extras workflow's images and switches to Extras. **Clear** empties the gallery (the files stay on the server).
  - **History…** opens the server's recent prompt history (from every client, newest first; ComfyUI keeps it in memory, so it is lost when the server restarts). Each entry shows its output thumbnails, time, run time, status (and error), the matching functional workflow and mode, the prompt, seed and model. Click a thumbnail for the full-screen viewer. **Add to Gallery** copies the entry's images into the Output Gallery, **Add to Stash** puts them in the Image Stash, **Use as Input** loads the image as the input image (with several images, the one you last viewed, which is highlighted), **Download** downloads the image (several as a ZIP), **Load Settings** loads its settings like dropping its PNG on Main, and **Prompt JSON** downloads the API prompt the server ran.
  - **Stash…** opens the *Image Stash*, your own list of images kept in this browser (not on the server), newest first. It survives reloads, so images stay available after the server forgets its history. Each image has the same details and buttons as History, plus **Pin** and **Remove**. **Clear** removes every image that isn't pinned, and **Clear All** removes all of them, after asking. Stashing an image that's already there moves it to the top. *Reset to defaults* in Configuration also empties the stash.
- **LoRA**: add any number of LoRAs from the server, filtered to the workflow's model family, with a weight for each.
  - The search box narrows every LoRA list to names containing the words you type, and **+ Add LoRA** adds the first match.
  - The **On/Off** button keeps a LoRA in the list without using it.
- **Custom Parameters**: extra settings defined by the selected workflow. Anima and MOSS have *Filename prefix*; MOSS also has the Skip Layer Guidance settings (*Skip layer guidance* on/off, off by default, plus its layers and start/end percent).
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
- **Server Preferences › Scaling**: the *Resize method* (default lanczos) and *Upscale model* (default None) used whenever Ainvil resizes an image for you: an img2img/inpainting input image to the generation size, and Focused inpainting's context window and its paste-back. Making an image bigger runs it through the upscale model first (if one is chosen) and then resizes it to the exact size; making it smaller always uses the resize method alone.
- **Client Preferences**: number of gallery thumbnails per row (2, 3 or 4), rows shown before the thumbnails scroll (1 or 2), the mask display color, and whether to show the live preview in the gallery while generating.
- **Functional Workflows**: each one has a name and model/LoRA filters (regular expressions, case-insensitive). It also has three ComfyUI workflows (txt2img, img2img, inpainting) with *mappings* that say which node input receives each Generate-tab value. Workflows can be loaded from ComfyUI's JSON (UI or API format) or from a ComfyUI PNG. **Auto-detect mappings** makes a good first guess for standard graphs.
- **Custom Workflows**: open-ended workflows for the Extras tab. Each has a ComfyUI workflow and a list of parameters, each with a name, a type (int, float, string, text, boolean, combo or image), a default, and the node input(s) it sets. An empty default uses the value in the workflow. Combos can have a regex filter (like the model filter), and any parameter can have help text, shown under it in Extras. **+ Built-in examples** adds back the built-in custom workflows (Upscale with model) if they are missing.

Each workflow can be exported and imported on its own. All exported files carry `"version": 1`.

### Mapping notes

- **LoRA template**: the sample LoRA loader node in your workflow. It is removed when no LoRAs are selected, and otherwise cloned and chained once per LoRA.
- **Batch repeat**: for workflows without an Empty Latent Image (img2img and inpainting), batch size works by inserting a `RepeatLatentBatch` node in front of the mapped latent input.
- **Output image**: Save Image nodes become Preview Image nodes when *Server Preferences › Save Image* is off.
- **CADS**: the CADS node, set from the CADS section. When CADS is off it is removed and its model input is passed straight through. Leave it unmapped for workflows without CADS.
- **Inpainting**: the mask is sent as the input image's alpha channel (via ComfyUI's `/upload/mask`), so the Load Image node's MASK output carries it. Focused inpainting needs nothing extra: Ainvil adds the scale-back and paste-back nodes itself.
- **Resize node**: the node that resizes the input image to Width × Height (`ImageScale`). It gets the *Scaling* resize method, and the upscale model is put in front of it when it enlarges the image.
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
