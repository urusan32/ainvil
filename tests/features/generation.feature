@gpu
Feature: Generating images on the server
  Generate queues the prompts on ComfyUI, waits for them and shows the results in the Output Gallery.
  These scenarios run real (small and quick) generations, saved under ainvil-test/ on the server.

  Background:
    Given Ainvil is open and connected to the test server
    And test outputs go to the "ainvil-test" folder
    And I fill in
      | Prompt | safe, a red apple on a wooden table |
      | Width  | 256                                 |
      | Height | 256                                 |
      | Steps  | 4                                   |
    And I uncheck "Random"
    And I set "Seed" in Generation Parameters to "1000"

  Scenario: txt2img makes an image in the test folder
    When I generate
    Then the generation succeeds with 1 image
    And the status says "Done — 1 image(s), txt2img."
    And the gallery info says "1 / 1 · seed 1000 · "
    And every gallery image was saved in the test folder
    And every gallery image is 256×256 pixels
    And the "Skip" button is hidden
    And the "Cancel" button in Main is hidden

  Scenario: The batch count queues one prompt per seed
    When I set "Batch count" to "3"
    And I generate
    Then the generation succeeds with 3 images
    And the gallery images have the seeds 1000, 1001, 1002
    And the gallery info says "1 / 3 · seed 1000"

  Scenario: The batch size makes several images in one prompt
    When I set "Batch size" to "2"
    And I generate
    Then the generation succeeds with 2 images
    And the gallery images have the seeds 1000, 1000
    When I click gallery thumbnail 2
    Then the gallery info says "2 / 2 · seed 1000 (batch #1)"

  Scenario: img2img makes an image of the generation size from the input image
    Given an input image "photo.png" of 320×240 pixels
    When I set "Denoise step (start step)" to "2"
    And I generate
    Then the generation succeeds with 1 image
    And the status says "img2img"
    And every gallery image is 256×256 pixels

  Scenario: img2img with an upscale model enlarges the input image first
    Given the configuration has "serverPreferences.upscaleModel" set to "models/OmniSR_X2_DIV2K.safetensors"
    And an input image "small.png" of 96×96 pixels
    When I fill in
      | Prompt | safe, a red apple on a wooden table |
      | Width  | 256                                 |
      | Height | 256                                 |
      | Steps  | 4                                   |
    And I generate
    Then the generation succeeds with 1 image
    And every gallery image is 256×256 pixels

  Scenario: Whole Image inpainting
    Given an input image "photo.png" of 320×240 pixels
    And a mask covering 100, 80 of size 60×60
    When I generate
    Then the generation succeeds with 1 image
    And the status says "inpainting"
    And every gallery image is 256×256 pixels

  Scenario: Focused inpainting keeps the image size and every pixel outside the mask
    Given an input image "photo.png" of 640×480 pixels
    And a mask covering 300, 200 of size 40×40
    When I click "Focused"
    And I set "Batch size" to "2"
    And I generate
    Then the generation succeeds with 2 images
    And every gallery image is 640×480 pixels
    And every gallery image matches the input image outside 300, 200 of size 40×40
    And every gallery image differs from the input image inside 300, 200 of size 40×40

  Scenario: With Save Image off the images are temporary previews
    Given the configuration has "serverPreferences.saveImage" set to false
    When I fill in
      | Prompt | safe, a red apple on a wooden table |
      | Width  | 256                                 |
      | Height | 256                                 |
      | Steps  | 4                                   |
    And I generate
    Then the generation succeeds with 1 image
    And every gallery image is a temporary preview

  Scenario: CADS runs on the server when it's enabled
    Given CADS is supported by the server
    When I check "Enable CADS"
    And I generate
    Then the generation succeeds with 1 image

  Scenario: Ctrl+Enter in the prompt generates
    When I press Ctrl+Enter in the prompt
    Then Generate is running
    When the generation finishes
    Then the generation succeeds with 1 image

  Scenario: The server's validation errors are shown
    Given the saved Generate form has the model "models/anima/no-such-model.safetensors"
    Then "Model" lists "models/anima/no-such-model.safetensors (not on server)"
    When I start generating
    And the generation finishes
    Then the status is an error saying "node #44 (UNETLoader)"
    And the Output Gallery is empty

  Scenario: The live preview is shown in the gallery while generating
    Given live preview is enabled
    When I fill in
      | Width  | 512 |
      | Height | 512 |
      | Steps  | 12  |
    And I watch the gallery info
    And I generate
    Then the gallery showed a live preview while generating
    And the generation succeeds with 1 image
    And the gallery info says "1 / 1 · seed 1000"
