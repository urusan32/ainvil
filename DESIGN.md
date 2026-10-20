# Ainvil
This is a single page HTML application that makes it easier to do common image generation workflows with ComfyUI.

## Basic Implementation Notes
The final application should be a single HTML page application that people can load and run with no dependencies, but if needed it can use compilation to generate the page, but ideally it's just a HTML page. Before installing any local dependencies please ask the developer user. There is a git repo set up so please set up .gitignore and such. Also make a README.md for human users and a CLAUDE.md with design notes for Claude sessions.

We don't need to implement the AI generation part, which is implemented by ComfyUI which we interact with through its API. Currently the API has no authentication as this is meant to be used locally. The user needs to be able to supply the API location, though we can assume it's at "http://localhost:8188/". There needs to be local configuration which is remembered from session to session and there also needs to be a way to export and import configuration (as JSON) so it can be moved from computer to computer.

Initial support can just be for Anima, which I will supply example workflows for, which will be provided as an initial configuration. The initial configuration can be overwritten by the user but will appear if there is no memory of previous configuration.

## Basic Paradigm
There's three main tabs: Generate, Extras, and Configuration.

Generate executes Functional Workflows which cover txt2img, img2img, and inpainting use cases. These functional workflows are configured from example ComfyUI workflows with mappings that allow the app to know how to edit the files to create the ComfyUI workflows to execute the user requests to generate images.

Extras does something similar but with open ended workflows. It's meant to make it easy to upscale in particular, but anything can be configured in principle.

Configuration contains the configuration pages and import/export functionality. Most of it corresponds to JSON configuration files.

## App Description
The page has several tabs for different use cases.

### Generate Tab
The initial tab is named Generate and supports the main txt2img, img2img, and inpainting functional workflows. It's organized into sections that can be laid out in one or more columns depending on screen real estate.

The Main section starts with the functional configuration selectors, with the first one being the Functional Workflow selector (ex. Anima, SDXL) and the second one being the main model selector (ex. Anima Base). The functional workflow is configured in the Configuration tab, while the model list is requested from ComfyUI. Text boxes for prompt and negative prompt are prominent and take up most of the space in this control cluster to allow for easy authoring of lengthy text (though if needed the negative text box can be smaller). The main control buttons are also here: a larger Generate button and smaller Clear and Generate Workflow buttons. A batch count selector also allows the user to select a number of images to generate at the same time (1 by default up to a maximum of 128). Generate will generate the image via ComfyUI and send it to the Output Gallery section. Clear resets everything on this page to the page defaults and purges any inputs or outputs. Generate Workflow generates the workflow it would have sent to ComfyUI and instead immediately downloads it to the browser (this ignores batch count and just generates the first one).

Another section is Generation Parameters, which contains universal parameters across all diffusion-type models. This includes image resolution (width and height), seed, steps, cfg, sampler name, and scheduler. Batch size is also in this section. Image resolution has tied to the manual entry text fields for width and height a selector for common resolutions. The two main resolution profiles are 1024 and 1536. Each of these have Square, Landscape, and Portrait. Square for 1024 is 1024x1024. Landscape for 1024 is 1216x832 with Portrait being the opposite. There's also a Custom button that deactivates the common resolutions selector until one of the other buttons is pressed again, and it also becomes custom if you type anything else into the text fields. If you select a resolution (ex. 1024) via button, square is the default. If you select a ratio via button the default resolution is 1024.

Another section on this page is Custom Parameters, which contains workflow specific parameters. This part of the control may change when the model type is changed. It's placed so that a dynamic change in size will not impact most of the other sections (it may impact LoRA as it may also dynamically resize). There's not necessarily any contents in this section, if there are no custom parameters for the workflow, but even in this case the section is still present.

The Output Gallery section displays the most recently generated images. It displays one selected image with a prominent thumbnail and smaller thumbnails of up to 9 images in the most recently executed batch. If there are more images due to batch size being used with batch count, only 9 will be displayed at a time but you can scroll to see them all. If an image is clicked on, it opens up a full screen view of the raw image, which can be downloaded at full size by right clicking and saving. An X allows the full screen view of the image to be dismissed and the page to return to normal. There are also download selected and download all buttons, and download all will download all images in the batch (if there were more than 9 in the batch).

Another section is Input Image, which allows an image to be uploaded to activate the img2img and inpainting features. The most prominent control in this section is an initially blank input image box that shows the currently loaded input image and allows the user to upload an image by dragging it into the box. A button to bring up a file picker instead is supplied as well. Another button is used to Clear the image out (to return to txt2img mode). Another box the same size as the input image box is for the mask, it displays the mask if loaded and allows the user to click on it to bring up a canvas that allows them to paint a mask over the image to create a mask. The mask box displays the mask over a copy of the input image. A mask image can be dragged into the mask image box. Three more buttons allow the mask to be downloaded, uploaded, or cleared.

If no image is loaded in Input Image, then the page operates in txt2img mode. If an image is loaded but no mask, it operates in img2img mode. If both an image and a mask are present it operates in inpainting mode.

Another section related to Input Image is the Input Parameters section. Contained within is three linked elements: two text fields to display the current denoise value and denoise step, as well as a slider for denoise step with dynamic step sizes based on the main number of steps. Unlike other examples out there this program mostly measures denoise as the start step not as a denoise percentage. ComfyUI takes a percentage which is calculated automatically from the total number of steps and the denoise step before being passed on to ComfyUI. A denoise step of 0 is 1.00 and $NUM_STEPS is 0.00. As another example, if we have 30 steps then a denoise step of 12 is 0.60 in ComfyUI. That said, a denoise value between 0.00 and 1.00 is displayed and both the denoise step and denoise value (and the denoise step slider) are all kept in sync if any one of them is changed. Another input parameter is Crop, a boolean which controls whether we crop or not on a resize. Another input parameter is Noise Mask, a boolean which controls whether we use the noise mask feature in inpainting, and it defaults to true.

If no input image is selected, then the app operates in txt2img mode with no input image and a denoise of 1.0 (step 0) with an empty latent image supplied at the correct resolution.

One more static section is reserved but not yet implemented: CADS.

Finally a LoRA section allows the addition of LoRAs and for their weights to be set. Each LoRA is just the LoRA name (from the list of LoRAs actually available on the server for the given model type) and the LoRA weight. LoRAs can be added and deleted from a list of currently active LoRAs and the final list is used to generate the workflow. The ComfyUI workflow is given with a single sample LoRA and multiple LoRA loaders are chained together to load all the requested LoRAs. This section has room for 8 LoRAs by default but may expand if more are added. It is placed so it does not interfere with the other static sections but may interfere with the Custom Parameters section, which is also dynamic in size.

### Extras Tab
This tab is meant to provide an easy way to do arbitrary workflows, but in particular it's meant for upscale work. It is currently empty pending further design.

### Configuration Tab
This tab allows the app to be configured, and for configuration to be imported and exported.

At the top of the configuration tab is the Connection section. This allows the ComfyUI instance to be specified and saved. There's a Test Connection button to test the connection. There's an Auto-Configure button that fills out the Server Features section correctly by interrogating the server for features.

Next is the Global Import and Export section. Export will dump the entire current app configuration into a JSON file that is downloaded in the browser immediately. Import allows a valid JSON configuration file to be uploaded either via file picker or dragging the file into the import/export box with a button to execute the import and overwrite the current configuration. Any issues should make an error box with developer information about what happened displayed in the box. Note there are individual imports and exports for Functional/Custom Workflows later.

Next is the Server Features section. This contains toggles for different features that depend on specific server support for them. Currently this just contains the CADS toggle, which depends on the comfyui-cads extension being installed on the ComfyUI server.

Next is the Server Preferences section which contains configuration for specific policy items that may vary from user to user. Current items are:
* Save Image - Whether to save the image on the server or just return the image via the API unsaved. Defaults to true.

Finally, there are two collapsable workflow sections. The first one is for the main Generate Image functional workflows and the second one is for the Extras custom workflows.

Each functional workflow has a name and three ComfyUI workflow files (txt2img, img2img, and inpainting) that are uploaded, and for each workflow the mappings from each functional parameter (ex. seed on the Generate tab) to where it is in the ComfyUI workflow (ex. seed in the ComfyUI workflow), so the workflow text can be altered as needed from the example. Finally there is a section for custom parameters and their mappings which works similar to the custom workflows.

Each custom workflow has a name, a ComfyUI workflow file, and mappings. Unlike functional workflows, which have specific parameters, the parameters here are defined before they are mapped to the workflow. Each one requires a name, type, and mapping.

Both functional and custom workflows can be exported or imported on an individual basis. Each workflow has its own export, which exports the configuration just for that functional/custom workflow for immediate download. There's one import file selector at the top of each section and importing a file successfully adds a new workflow to the end of the list.

All of the import and export JSON files have a version in the JSON object, which starts at 1 for this version. This should be maintained at 1 during the alpha phase of development.

## Other notes
The main target is ordinary laptop and desktop computers, but it would be nice if it would work when loaded onto a smartphone browser. I'll be using Firefox but it should work with at least Chrome/Chromium as well.
