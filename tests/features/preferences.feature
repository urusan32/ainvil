Feature: Server and client preferences
  Server Preferences decide how prompts are built (saving images, how input images are resized). Client
  Preferences only change this browser's display and behavior.

  Background:
    Given Ainvil is open and connected to the test server
    And test outputs go to the "ainvil-test" folder

  Scenario: The scaling choices come from the server
    When I open the "Configuration" tab
    Then "Resize method" lists the server's ImageScale upscale_method options
    And "Resize method" shows "lanczos"
    And "Upscale model" shows ""
    And "Upscale model" lists "None (resize method only)"
    And "Upscale model" lists "4x_foolhardy_Remacri.pth"

  Scenario: With Save Image off, the output is a preview that isn't saved
    Given the "Configuration" tab is open
    When I uncheck "Save Image"
    And I open the "Generate" tab
    And I set "Prompt" to "safe, a cat"
    And I download the workflow
    Then the workflow has node 46 (PreviewImage)
    And the workflow node 46 "images" is linked to node 8
    And the workflow has no SaveImage node

  Scenario: With Save Image on, the output is saved with an expanded filename prefix
    When I set "Prompt" to "safe, a cat"
    And I set "Filename prefix" to "ainvil-test/e2e/%date:yyyyMMdd%_%KSampler.steps%steps"
    And I download the workflow
    Then the workflow has node 46 (SaveImage)
    And the workflow's filename prefix is today's date followed by "ainvil-test/e2e/{date}_30steps"

  Scenario: The input image is resized to the generation size with the chosen method
    Given an input image "small.png" of 256×256 pixels
    And the "Configuration" tab is open
    When I select "bicubic" as "Resize method"
    And I open the "Generate" tab
    And I fill in
      | Prompt | safe, a cat |
      | Width  | 512         |
      | Height | 512         |
    And I download the workflow
    Then the workflow sets
      | node | input          | value     |
      | 53   | upscale_method | "bicubic" |
      | 53   | width          | 512       |
      | 53   | height         | 512       |
    And the workflow node 53 "image" is linked to node 51
    And the workflow has no ImageUpscaleWithModel node

  Scenario: An upscale model enlarges the input image before the resize
    Given an input image "small.png" of 256×256 pixels
    And the "Configuration" tab is open
    When I select "models/OmniSR_X2_DIV2K.safetensors" as "Upscale model"
    And I open the "Generate" tab
    And I fill in
      | Prompt | safe, a cat |
      | Width  | 512         |
      | Height | 768         |
    And I download the workflow
    Then the workflow has a node titled "Ainvil upscale model" with
      | input      | value                                |
      | model_name | "models/OmniSR_X2_DIV2K.safetensors" |
    And the "image" input of the "Ainvil model upscale" node is linked to the "LoadImage" node
    And the "upscale_model" input of the "Ainvil model upscale" node is linked to the "Ainvil upscale model" node
    And the workflow node 53 "image" is linked to the "Ainvil model upscale" node
    And the workflow sets node 53 "upscale_method" to "lanczos"

  Scenario Outline: The upscale model is only used when the image gets bigger
    Given the configuration has "serverPreferences.upscaleModel" set to "models/OmniSR_X2_DIV2K.safetensors"
    And an input image "photo.png" of <input> pixels
    When I fill in
      | Prompt | safe, a cat |
      | Width  | <width>     |
      | Height | <height>    |
    And I download the workflow
    Then the workflow has no ImageUpscaleWithModel node
    And the workflow node 53 "image" is linked to node 51

    Examples:
      | input     | width | height |
      | 512×512   | 512   | 512    |
      | 1024×1024 | 512   | 512    |

  Scenario: Client preferences set the gallery thumbnail grid
    Given the "Configuration" tab is open
    When I select "4" as "Gallery thumbnails per row"
    And I select "1" as "Gallery rows before scrolling"
    Then the gallery thumbnails are laid out 4 per row and 1 rows high
    When I reload the page
    Then the gallery thumbnails are laid out 4 per row and 1 rows high

  Scenario: The mask color can be changed and reset
    Given an input image "photo.png" of 128×128 pixels
    And a mask covering 32, 32 of size 32×32
    And the "Configuration" tab is open
    Then the mask is displayed in "#ff285a"
    When I set "Mask color" to "#00ff00"
    Then the mask is displayed in "#00ff00"
    And the saved configuration has "clientPreferences.maskColor" = "#00ff00"
    When I click "Reset to default"
    Then the mask is displayed in "#ff285a"
    And "Mask color" shows "#ff285a"

  Scenario: "Edit Generate layout" opens the layout editor on the Generate tab
    Given the "Configuration" tab is open
    When I click "Edit Generate layout"
    Then the "Generate" tab is shown
    And I see "Editing layout"
