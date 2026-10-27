Feature: Extras: running custom workflows
  The Extras tab runs a custom workflow with the parameters filled in. Image parameters take one or more
  images, and several images run the workflow once per image. The built-in Upscale with model upscales
  with an upscale model and then resizes to a target size.

  Background:
    Given Ainvil is open and connected to the test server
    And test outputs go to the "ainvil-test" folder
    And the "Extras" tab is open

  Scenario: Upscale with model shows its parameters with their defaults
    Then "Workflow" shows "Upscale with model"
    And the Extras parameters are
      | Image               |
      | Upscale model       |
      | Model upscale only  |
      | Width               |
      | Height              |
      | Final resize method |
      | Crop                |
      | Filename prefix     |
    And the form shows
      | Upscale model       | models/4x_foolhardy_Remacri.pth |
      | Width               | 1536                            |
      | Height              | 1536                            |
      | Final resize method | lanczos                         |
      | Crop                | disabled                        |
    And "Model upscale only" is not checked
    And the Extras hint for "Width" is "0 = follow Height, keeping the aspect ratio"
    And the Extras output info says ""

  Scenario: The upscale model list can be searched
    When I set "Search" in Extras to "omnisr x3"
    Then "Upscale model" lists only
      | 4x_foolhardy_Remacri.pth    |
      | OmniSR_X3_DIV2K.safetensors |

  Scenario: Running without an image explains what's missing
    When I click "Run" in Extras
    Then the Extras status is an error saying "Add an image to \"Image\"."
    When I click "Generate Workflow" in Extras
    Then the Extras status is an error saying "Add an image to \"Image\"."

  Scenario: Images are added by dropping, choosing or pasting, and removed
    When I add these images to "Image" in Extras
      | name  | size  |
      | a.png | 64×48 |
      | b.png | 48×64 |
    And I choose these images for "Image" with "choose files"
      | name  | size  |
      | c.png | 32×32 |
    And I paste an image "d.png" of 40×40 pixels in Extras
    Then "Image" in Extras has the images
      | a.png |
      | b.png |
      | c.png |
      | d.png |
    And "Image" in Extras says "4 images"
    When I remove image 2 from "Image" in Extras
    Then "Image" in Extras has the images
      | a.png |
      | c.png |
      | d.png |
    When I add these images to "Image" in Extras
      | name     | size  |
      | again.png | 64×48 |
    Then "Image" in Extras says "3 images"
    When I click "Clear images" for "Image" in Extras
    Then "Image" in Extras has no images

  Scenario: The workflow file carries the parameters and the image's name
    When I add these images to "Image" in Extras
      | name      | size  |
      | photo.png | 64×48 |
    And I fill in
      | Width               | 512     |
      | Height              | 0       |
      | Final resize method | bicubic |
      | Crop                | center  |
    And I check "Model upscale only"
    And I download the Extras workflow
    Then a file named "ainvil-upscale-with-model-api.json" is downloaded
    And the Extras status says "Downloaded the workflow (ComfyUI API format)."
    And the workflow sets
      | node | input           | value                              |
      | 2    | image           | /^ainvil\/ainvil_[0-9a-f]{14}\.png$/ |
      | 9    | model_name      | "models/4x_foolhardy_Remacri.pth"  |
      | 11   | width           | 512                                |
      | 11   | height          | 0                                  |
      | 11   | upscale_method  | "bicubic"                          |
      | 11   | crop            | "center"                           |
      | 12   | switch          | true                               |
      | 5    | filename_prefix | "ainvil-test/e2e/extras_photo"     |

  Scenario: With Save Image off the result is a preview
    Given the configuration has "serverPreferences.saveImage" set to false
    And the "Extras" tab is open
    When I add these images to "Image" in Extras
      | name      | size  |
      | photo.png | 64×48 |
    And I download the Extras workflow
    Then the workflow has no SaveImage node
    And the workflow has 1 PreviewImage node

  Scenario: The Extras values are remembered, the images are not
    When I add these images to "Image" in Extras
      | name      | size  |
      | photo.png | 64×48 |
    And I set "Width" to "777"
    And I reload the page
    Then "Width" shows "777"
    And "Image" in Extras has no images

  Scenario: Clear resets the parameters and removes the images
    When I add these images to "Image" in Extras
      | name      | size  |
      | photo.png | 64×48 |
    And I set "Width" to "777"
    And I click "Clear" in Extras
    Then "Width" shows "1536"
    And "Image" in Extras has no images

  Scenario: Several image parameters need one image or the same number each
    Given the "Configuration" tab is open
    And "Custom Workflows (Extras)" is expanded
    When I expand "Upscale with model"
    And I click "+ Add parameter" in "Upscale with model"
    And I set parameter 9 of "Upscale with model" to
      | Name | Second image |
      | Type | image        |
    And I map parameter 9 of "Upscale with model" to node "2" input "image"
    And I open the "Extras" tab
    And I add these images to "Image" in Extras
      | name  | size  |
      | a.png | 64×48 |
      | b.png | 48×64 |
    And I add these images to "Second image" in Extras
      | name  | size  |
      | x.png | 32×32 |
      | y.png | 32×48 |
      | z.png | 48×32 |
    And I click "Run" in Extras
    Then the Extras status is an error saying "\"Image\" has 2 images, \"Second image\" has 3 images: give each image parameter either one image or the same number."
    When I remove image 3 from "Second image" in Extras
    And I remove image 2 from "Second image" in Extras
    And I download the Extras workflow
    Then the Extras status says "Downloaded the workflow"

  Scenario: Cancel stops a run
    When I add these images to "Image" in Extras
      | name  | size    |
      | a.png | 256×256 |
      | b.png | 256×192 |
    And I press Run in Extras
    And I click "Cancel" in Extras
    And the Extras run finishes
    Then the Extras status says "Cancelled."
    And the Extras output is empty

  @gpu
  Scenario: A batch upscale runs once per image and keeps each image's name
    When I add these images to "Image" in Extras
      | name  | size  |
      | a.png | 64×48 |
      | b.png | 48×64 |
    And I fill in
      | Upscale model | models/OmniSR_X2_DIV2K.safetensors |
      | Width         | 256                                |
      | Height        | 0                                  |
    And I run the Extras workflow
    Then the Extras status says "Done — 2 image(s)."
    And the Extras output images are
      | input | size    |
      | a     | 256×192 |
      | b     | 256×341 |
    And every Extras output image was saved in the test folder
    And the Extras output info says "1 / 2 · a · extras_a_"
    And the Extras output info says "· 256×192"

  @gpu
  Scenario: Model upscale only keeps the model's size
    When I add these images to "Image" in Extras
      | name  | size  |
      | a.png | 64×48 |
    And I fill in
      | Upscale model | models/OmniSR_X2_DIV2K.safetensors |
    And I check "Model upscale only"
    And I run the Extras workflow
    Then the Extras output images are
      | input | size   |
      | a     | 128×96 |

  @gpu
  Scenario: The Extras output can be viewed, downloaded, stashed and used as the input image
    When I add these images to "Image" in Extras
      | name  | size  |
      | a.png | 64×48 |
      | b.png | 48×64 |
    And I fill in
      | Upscale model | models/OmniSR_X2_DIV2K.safetensors |
    And I check "Model upscale only"
    And I run the Extras workflow
    And I click Extras output thumbnail 2
    Then the Extras output info says "2 / 2 · b"
    When I click the main Extras output image
    Then the viewer is open
    When I press Escape
    And I click "Download Selected" in the Extras output
    Then a file named like "extras_b_*.png" is downloaded
    When I click "Download All" in the Extras output
    Then the downloaded ZIP "ainvil-extras-*.zip" holds 2 PNG images
    When I click "Add to Stash" in the Extras output
    Then the Image Stash holds 2 images
    When I click "Use as Input" in the Extras output
    Then the "Generate" tab is shown
    And the input image is 96×128 pixels
