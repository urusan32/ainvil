Feature: The ComfyUI workflow Ainvil builds
  Generate Workflow downloads the API-format prompt Generate would queue (for the first image of the batch
  count). These scenarios check how the form, the input image, LoRAs and CADS end up in it.

  Background:
    Given Ainvil is open and connected to the test server
    And test outputs go to the "ainvil-test" folder

  Scenario: A txt2img workflow carries the form's values
    When I fill in
      | Prompt          | safe, a red apple on a table |
      | Negative Prompt | blurry, lowres               |
      | Width           | 640                          |
      | Height          | 448                          |
      | Batch size      | 2                            |
      | Steps           | 12                           |
      | CFG             | 3.5                          |
      | Sampler         | euler                        |
      | Scheduler       | karras                       |
      | Model           | models/anima/anima_aestheticV11.safetensors |
    And I uncheck "Random"
    And I set "Seed" in Generation Parameters to "123456789"
    And I download the workflow
    Then a file named "ainvil-anima-txt2img-api.json" is downloaded
    And the status says "Downloaded the txt2img workflow (ComfyUI API format)."
    And the workflow sets
      | node | input        | value                                         |
      | 11   | text         | "safe, a red apple on a table"                |
      | 12   | text         | "blurry, lowres"                              |
      | 28   | width        | 640                                           |
      | 28   | height       | 448                                           |
      | 28   | batch_size   | 2                                             |
      | 19   | seed         | 123456789                                     |
      | 19   | steps        | 12                                            |
      | 19   | cfg          | 3.5                                           |
      | 19   | sampler_name | "euler"                                       |
      | 19   | scheduler    | "karras"                                      |
      | 19   | denoise      | 1                                             |
      | 44   | unet_name    | "models/anima/anima_aestheticV11.safetensors" |
    And the workflow's filename prefix starts with "ainvil-test/e2e/Anima_"

  Scenario: A %date% filename prefix is expanded with today's date
    When I set "Filename prefix" to "ainvil-test/e2e/%date:yyyyMMdd%/Anima_%date:yyyyMMdd%"
    And I set "Prompt" to "safe, a cat"
    And I download the workflow
    Then the workflow's filename prefix is today's date followed by "ainvil-test/e2e/{date}/Anima_{date}"

  Scenario: The denoise step only applies with an input image
    When I set "Prompt" to "safe, a cat"
    And I set "Denoise step (start step)" to "9"
    And I download the workflow
    Then the workflow sets node 19 "denoise" to 1
    Given an input image "photo.png" of 320×240 pixels
    When I download the workflow
    Then a file named "ainvil-anima-img2img-api.json" is downloaded
    And the workflow sets node 19 "denoise" to 0.7

  Scenario: An img2img workflow uploads the input image and resizes it to the generation size
    Given an input image "photo.png" of 320×240 pixels
    When I fill in
      | Prompt | safe, a cat |
      | Width  | 512         |
      | Height | 384         |
    And I check "Crop"
    And I download the workflow
    Then the mode is img2img
    And the workflow loads the input image from "ainvil/ainvil_[0-9a-f]{14}\.png"
    And the uploaded input image is on the server
    And the workflow sets
      | node | input | value    |
      | 53   | width  | 512      |
      | 53   | height | 384      |
      | 53   | crop   | "center" |
    And the workflow node 52 "pixels" is linked to node 53
    And the workflow has no RepeatLatentBatch node

  Scenario: Batch size in img2img repeats the encoded latent
    Given an input image "photo.png" of 320×240 pixels
    When I set "Prompt" to "safe, a cat"
    And I set "Batch size" to "3"
    And I download the workflow
    Then the workflow has a node titled "Repeat Latent Batch" with
      | input   | value |
      | amount  | 3     |
    And the workflow node 19 "latent_image" is linked to the "Repeat Latent Batch" node
    And the "samples" input of the "Repeat Latent Batch" node is linked to the "VAEEncode" node

  Scenario: An inpainting workflow sends the mask as the image's alpha channel
    Given an input image "photo.png" of 320×240 pixels
    And a mask covering 100, 80 of size 60×40
    When I set "Prompt" to "safe, a cat"
    And I uncheck "Noise Mask"
    And I download the workflow
    Then a file named "ainvil-anima-inpainting-api.json" is downloaded
    And the mode is inpainting
    And the workflow loads the input image from "ainvil/ainvil_[0-9a-f]{14}_m[0-9a-f]{14}\.png"
    And the uploaded input image is on the server
    And the workflow sets node 60 "noise_mask" to false
    And the workflow node 60 "mask" is linked to node 51

  Scenario: The same image and mask are uploaded only once, whatever the mask's display color
    Given an input image "photo.png" of 320×240 pixels
    And a mask covering 100, 80 of size 60×40
    When I set "Prompt" to "safe, a cat"
    And I download the workflow
    And I remember the uploaded image name
    And I open the mask editor
    And I change the mask color in the mask editor to "#00ffff"
    And I click "Done" in the mask editor
    And I download the workflow
    Then the workflow uses the same uploaded image

  Scenario: Active LoRAs are chained in order and inactive ones are left out
    When I set "Prompt" to "safe, a cat"
    And I add a LoRA
    And I add a LoRA
    And I add a LoRA
    And I set LoRA 1 to "models/anima/bdl-AB10-01.safetensors" with weight "0.8"
    And I set LoRA 2 to "models/anima/oatd-AB10-01.safetensors" with weight "0.3"
    And I set LoRA 3 to "models/anima/galena-AB10-01.safetensors" with weight "0.5"
    And I switch LoRA 2 off
    Then the LoRA list is
      | on/off | name                       | weight |
      | On     | bdl-AB10-01.safetensors    | 0.8    |
      | Off    | oatd-AB10-01.safetensors   | 0.3    |
      | On     | galena-AB10-01.safetensors | 0.5    |
    When I download the workflow
    Then the workflow has no node 49
    And the workflow has 2 LoraLoaderModelOnly nodes
    And the sampler's model comes from "LoRA galena-AB10-01.safetensors ×0.5 ← LoRA bdl-AB10-01.safetensors ×0.8 ← UNETLoader"

  Scenario: Without LoRAs the template LoRA node is removed
    When I set "Prompt" to "safe, a cat"
    And I download the workflow
    Then the workflow has no LoraLoaderModelOnly node
    And the sampler's model comes from "UNETLoader"

  Scenario: The LoRA list can be searched, toggled and trimmed
    When I type "gal" into the LoRA search
    And I add a LoRA
    Then the LoRA list is
      | on/off | name                       | weight |
      | On     | galena-AB10-01.safetensors | 1      |
    When I type "nothing like this" into the LoRA search
    Then the LoRA list is
      | on/off | name                                   | weight |
      | On     | galena-AB10-01.safetensors             | 1      |
    And LoRA 1 lists "(no matches)"
    When I switch LoRA 1 off
    And I switch LoRA 1 on
    And I remove LoRA 1
    Then the LoRA section says "No LoRAs added."

  Scenario: CADS is off until the server supports it
    Then the CADS section says "CADS is not supported on the server (needs the comfyui-cads extension; Auto-Configure detects it), so it is off."
    And "Enable CADS" is disabled
    When I set "Prompt" to "safe, a cat"
    And I download the workflow
    Then the workflow has no CADS node

  Scenario: With CADS on, its node gets the CADS settings and follows the image seed
    Given CADS is supported by the server
    Then the CADS section has no message
    When I check "Enable CADS"
    And I fill in
      | Prompt      | safe, a cat |
      | Steps       | 20          |
      | Noise scale | 0.3         |
      | t1          | 0.5         |
      | Apply to    | cond        |
      | Noise type  | uniform     |
    And I uncheck "Random"
    And I set "Seed" in Generation Parameters to "4294967301"
    And I download the workflow
    Then the sampler's model comes from "CADS ← UNETLoader"
    And the workflow sets
      | node | input       | value     |
      | 63   | noise_scale | 0.3       |
      | 63   | t1          | 0.5       |
      | 63   | t2          | 0.9       |
      | 63   | total_steps | 20        |
      | 63   | apply_to    | "cond"    |
      | 63   | noise_type  | "uniform" |
      | 63   | seed        | 5         |

  Scenario: CADS total steps follow the main steps, but not the other way round
    Given CADS is supported by the server
    When I set "Steps" to "18"
    Then "Total steps" shows "18"
    When I set "Total steps" to "10"
    Then "Steps" shows "18"
    When I set "Steps" to "22"
    Then "Total steps" shows "22"

  Scenario: A manual CADS seed is used as it is
    Given CADS is supported by the server
    When I check "Enable CADS"
    And I uncheck "Automatic"
    And I set "Seed" in CADS to "99"
    And I set "Prompt" to "safe, a cat"
    And I download the workflow
    Then the workflow sets node 63 "seed" to 99

  Scenario: CADS is off for a mode without a mapped CADS node
    Given the configuration has "functionalWorkflows.0.workflows.inpainting.mappings.cads" set to []
    And CADS is supported by the server
    And an input image "photo.png" of 320×240 pixels
    And a mask covering 10, 10 of size 50×50
    Then the CADS section says "CADS is not configured for inpainting in this workflow, so it is off."

  Scenario: CADS is off when the server has no CADS node
    Given CADS is supported by the server
    And the server reports no CADS node type
    Then the CADS section says "CADS is not supported on the server: it has no CADS node (is comfyui-cads installed?), so it is off."
    When I set "Prompt" to "safe, a cat"
    And I download the workflow
    Then the workflow has no CADS node
    And the sampler's model comes from "UNETLoader"

  Scenario: Switching to MOSS keeps CADS on
    Given CADS is supported by the server
    When I check "Enable CADS"
    And I select "MOSS" as "Functional Workflow"
    Then "Enable CADS" is checked

  Scenario: MOSS's Skip Layer Guidance switch routes the model through the SLG node
    When I select "MOSS" as "Functional Workflow"
    And I set "Prompt" to "safe, a cat"
    And I download the workflow
    Then a file named "ainvil-moss-txt2img-api.json" is downloaded
    And the sampler's model comes from "ComfySwitchNode ← UNETLoader"
    And the workflow sets node 65 "switch" to false
    When I check "Skip layer guidance"
    And I set "SLG single layers" to "7, 8"
    And I set "SLG end percent" to "0.25"
    And I download the workflow
    Then the workflow sets
      | node | input         | value  |
      | 65   | switch        | true   |
      | 64   | single_layers | "7, 8" |
      | 64   | end_percent   | 0.25   |
    And the sampler's model comes from "ComfySwitchNode ← SkipLayerGuidanceDiTSimple ← UNETLoader"

  Scenario: Only the first image of the batch count goes into the workflow file
    When I set "Prompt" to "safe, a cat"
    And I set "Batch count" to "4"
    And I uncheck "Random"
    And I set "Seed" in Generation Parameters to "50"
    And I download the workflow
    Then the workflow sets node 19 "seed" to 50
    And 1 file was downloaded
