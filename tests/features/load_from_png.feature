Feature: Loading settings from a generated PNG
  ComfyUI stores the API prompt in the PNGs it saves. Dropping such a PNG on the Main section finds the
  matching functional workflow and mode and loads the settings, LoRAs, CADS and custom parameters; for
  img2img and inpainting it also loads the input image and mask from the server's input folder.

  Background:
    Given Ainvil is open and connected to the test server
    And test outputs go to the "ainvil-test" folder

  Scenario: A txt2img PNG fills in the form
    Given CADS is supported by the server
    When I fill in
      | Prompt          | safe, a castle in the clouds |
      | Negative Prompt | lowres                       |
      | Width           | 832                          |
      | Height          | 1216                         |
      | Batch size      | 2                            |
      | Steps           | 14                           |
      | CFG             | 6                            |
      | Sampler         | euler                        |
      | Scheduler       | karras                       |
      | Model           | models/anima/anima_aestheticV11.safetensors |
    And I uncheck "Random"
    And I set "Seed" in Generation Parameters to "31337"
    And I add a LoRA
    And I add a LoRA
    And I set LoRA 1 to "models/anima/bdl-AB10-01.safetensors" with weight "0.7"
    And I set LoRA 2 to "models/anima/galena-AB10-01.safetensors" with weight "0.4"
    And I check "Enable CADS"
    And I set "Noise scale" to "0.2"
    And I uncheck "Automatic"
    And I set "Seed" in CADS to "55"
    And I download the workflow
    And I click "Clear" in Main
    And I drop a PNG made with that workflow on the Main section
    Then the status says "Loaded settings from ComfyUI_00001_.png (Anima, txt2img)."
    And the form shows
      | Prompt          | safe, a castle in the clouds                |
      | Negative Prompt | lowres                                      |
      | Width           | 832                                         |
      | Height          | 1216                                        |
      | Batch size      | 2                                           |
      | Steps           | 14                                          |
      | CFG             | 6                                           |
      | Sampler         | euler                                       |
      | Scheduler       | karras                                      |
      | Model           | models/anima/anima_aestheticV11.safetensors |
      | Seed            | 31337 | Generation Parameters               |
      | Noise scale     | 0.2                                         |
      | Seed            | 55    | CADS                                |
    And "Random" is not checked
    And "Enable CADS" is checked
    And "Automatic" is not checked
    And the resolution buttons "1024" and "Portrait" are selected
    And the LoRA list is
      | on/off | name                       | weight |
      | On     | bdl-AB10-01.safetensors    | 0.7    |
      | On     | galena-AB10-01.safetensors | 0.4    |
    And the mode is txt2img

  Scenario: A CADS seed that follows the image seed loads as Automatic, and no CADS node means CADS off
    Given CADS is supported by the server
    When I set "Prompt" to "safe, a castle"
    And I check "Enable CADS"
    And I download the workflow
    And I uncheck "Enable CADS"
    And I uncheck "Automatic"
    And I drop a PNG made with that workflow on the Main section
    Then "Enable CADS" is checked
    And "Automatic" is checked
    When I uncheck "Enable CADS"
    And I download the workflow
    And I check "Enable CADS"
    And I drop a PNG made with that workflow on the Main section
    Then "Enable CADS" is not checked

  Scenario: A filename prefix template is kept rather than its expanded value
    When I set "Prompt" to "safe, a castle"
    And I download the workflow
    And I set "Prompt" to "something else, safe,"
    And I drop a PNG made with that workflow on the Main section
    Then "Filename prefix" shows "ainvil-test/e2e/Anima_%date:hhmmss%"
    And "Prompt" shows "safe, a castle"

  Scenario: A MOSS PNG switches to MOSS with its custom parameters
    When I select "MOSS" as "Functional Workflow"
    And I set "Prompt" to "safe, a castle"
    And I check "Skip layer guidance"
    And I set "SLG single layers" to "9"
    And I download the workflow
    And I click "Clear" in Main
    And I drop a PNG made with that workflow on the Main section
    Then the status says "(MOSS, txt2img)"
    And "Functional Workflow" shows "MOSS"
    And "Skip layer guidance" is checked
    And "SLG single layers" shows "9"

  Scenario: An img2img PNG loads the input image from the server
    Given an input image "photo.png" of 320×240 pixels
    When I fill in
      | Prompt                    | safe, a castle |
      | Batch size                | 3              |
      | Denoise step (start step) | 9              |
    And I download the workflow
    And I click "Clear" in Main
    Then the mode is txt2img
    When I drop a PNG made with that workflow on the Main section
    Then the status says "(Anima, img2img)"
    And the mode is img2img
    And the input image is named like "ainvil_[0-9a-f]{14}\.png"
    And the input image is 320×240 pixels
    And the form shows
      | Batch size                | 3 |
      | Denoise step (start step) | 9 |

  Scenario: An inpainting PNG loads the original image and the mask
    Given an input image "photo.png" of 320×240 pixels
    And a mask covering 100, 80 of size 60×40
    When I remember the input image pixel at 130, 100
    And I set "Prompt" to "safe, a castle"
    And I download the workflow
    And I click "Clear" in Main
    And I drop a PNG made with that workflow on the Main section
    Then the status says "(Anima, inpainting)"
    And the mode is inpainting
    And the mask covers 100, 80 of size 60×40
    And the input image pixel at 130, 100 is as remembered

  Scenario: A Focused inpainting PNG restores the original, the full mask and a By Size window
    Given an input image "photo.png" of 640×480 pixels
    And a mask covering 300, 200 of size 40×40
    When I fill in
      | Prompt | safe, a castle |
      | Width  | 512            |
      | Height | 512            |
    And I click "Focused"
    And I download the workflow
    And I click "Clear" in Main
    And I drop a PNG made with that workflow on the Main section
    Then the status says "(Anima, inpainting)"
    And the input image is 640×480 pixels
    And the mask covers 300, 200 of size 40×40
    And the saved Generate form has "inpaintMode" = "focused"
    And the saved Generate form has "ctxMode" = "auto"
    And the context window is 268, 168 of size 104×104

  Scenario: A moved Focused window comes back as Manual Select
    Given an input image "photo.png" of 640×480 pixels
    And a mask covering 300, 200 of size 40×40
    When I fill in
      | Prompt | safe, a castle |
      | Width  | 512            |
      | Height | 512            |
    And I click "Focused"
    And I click "Manual Select"
    And I open the mask editor
    And I click "Window" in the mask editor
    And I drag the window from 320, 220 to 340, 230
    And I click "Done" in the mask editor
    And I download the workflow
    And I click "Clear" in Main
    And I drop a PNG made with that workflow on the Main section
    Then the saved Generate form has "ctxMode" = "manual"
    And the context window is 288, 178 of size 104×104

  Scenario: An input image that is gone from the server is reported
    Given an input image "photo.png" of 320×240 pixels
    When I set "Prompt" to "safe, a castle"
    And I download the workflow
    And I change the workflow so node 51 "image" is "ainvil/ainvil_00000000000000.png"
    And I clear the input image
    And I drop a PNG made with that workflow on the Main section
    Then an error toast says "Could not load the input image \"ainvil/ainvil_00000000000000.png\" from the server"
    And the status says "(Anima, img2img)"

  @js-errors
  Scenario Outline: Images that can't be loaded are explained
    When <drop>
    Then an error toast says "<error>"

    Examples:
      | drop                                                          | error                                                      |
      | I drop a PNG without metadata on the Main section             | This image has no ComfyUI prompt metadata.                 |
      | I drop a JPEG image on the Main section                       | Could not read the image metadata: Not a PNG file          |
      | I drop a PNG with a prompt of another workflow on the Main section | other.png does not match any configured functional workflow. |

  Scenario: Dropped text is left alone
    When I drop some text on the Main section
    Then no error toast is shown
    And the status says ""

  @gpu
  Scenario: A PNG generated by Ainvil round-trips
    When I fill in
      | Prompt | safe, a small green pear |
      | Width  | 256                      |
      | Height | 256                      |
      | Steps  | 4                        |
    And I uncheck "Random"
    And I set "Seed" in Generation Parameters to "5150"
    And I generate
    And I set "Prompt" to "safe, something else"
    And I check "Random"
    And I drop the selected gallery image on the Main section
    Then the status says "Loaded settings from"
    And the form shows
      | Prompt | safe, a small green pear |
      | Seed   | 5150 | Generation Parameters |
    And "Random" is not checked
