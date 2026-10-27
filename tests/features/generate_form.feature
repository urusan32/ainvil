Feature: The Generate form
  The Generate tab's Main, Generation Parameters, Input Parameters and Custom Parameters sections hold the
  settings of the next generation. Their defaults come from the functional workflow, and they are remembered
  between visits.

  Background:
    Given Ainvil is open and connected to the test server

  Scenario: The form starts from the Anima workflow's values
    Then the form shows
      | Functional Workflow | Anima                                  |
      | Model               | models/anima/anima_baseV10.safetensors |
      | Prompt              |                                        |
      | Batch count         | 1                                      |
      | Width               | 1024                                   |
      | Height              | 1024                                   |
      | Batch size          | 1                                      |
      | Steps               | 30                                     |
      | CFG                 | 4                                      |
      | Sampler             | euler_ancestral                        |
      | Scheduler           | simple                                 |
      | Denoise step (start step) | 12                               |
      | Denoise             | 0.60                                   |
    And "Random" is checked
    And "Noise Mask" is checked
    And "Crop" is not checked
    And the mode is txt2img
    And the resolution buttons "1024" and "Square" are selected
    And the input parameters hint says "No input image: txt2img mode uses an empty latent and denoise 1.00 (step 0)."

  Scenario Outline: Resolution presets set the width and height
    When I click "<profile>"
    And I click "<ratio>"
    Then "Width" shows "<width>"
    And "Height" shows "<height>"
    And the resolution buttons "<profile>" and "<ratio>" are selected

    Examples:
      | profile | ratio        | width | height |
      | 1024    | Square       | 1024  | 1024   |
      | 1024    | Landscape    | 1216  | 832    |
      | 1024    | Portrait     | 832   | 1216   |
      | 1024    | WS Landscape | 1344  | 768    |
      | 1024    | WS Portrait  | 768   | 1344   |
      | 1536    | Square       | 1536  | 1536   |
      | 1536    | Landscape    | 1824  | 1248   |
      | 1536    | Portrait     | 1248  | 1824   |
      | 1536    | WS Landscape | 2048  | 1152   |
      | 1536    | WS Portrait  | 1152  | 2048   |

  Scenario: A resolution keeps its ratio when the size profile changes
    When I click "Landscape"
    And I click "1536"
    Then "Width" shows "1824"
    And "Height" shows "1248"

  Scenario: Typing another size makes the resolution custom
    When I set "Width" to "1000"
    Then only the resolution button "Custom" is selected
    When I click "Portrait"
    Then "Width" shows "832"
    And "Height" shows "1216"
    And the resolution buttons "1024" and "Portrait" are selected

  Scenario: The Custom button deselects the presets until one is chosen again
    When I click "Custom"
    Then only the resolution button "Custom" is selected
    And "Width" shows "1024"
    When I click "1536"
    Then "Width" shows "1536"
    And the resolution buttons "1536" and "Square" are selected

  Scenario: Denoise is set as a start step, and the value, step and slider stay in sync
    Then the denoise slider is at 18 of 30
    When I set "Denoise step (start step)" to "6"
    Then "Denoise" shows "0.80"
    And the denoise slider is at 24 of 30
    When I set "Denoise" to "0.25"
    Then "Denoise step (start step)" shows "23"
    And "Denoise" shows "0.23"
    When I move the denoise slider to 20
    Then "Denoise step (start step)" shows "10"
    And "Denoise" shows "0.67"

  Scenario: Changing the steps keeps the denoise value
    When I set "Steps" to "60"
    Then "Denoise step (start step)" shows "24"
    And "Denoise" shows "0.60"
    And the denoise slider is at 36 of 60

  Scenario Outline: The batch count stays between 1 and 128
    When I set "Batch count" to "<typed>"
    Then "Batch count" shows "<kept>"

    Examples:
      | typed | kept |
      | 5     | 5    |
      | 0     | 1    |
      | 500   | 128  |

  Scenario: The model search shows only models with every typed word
    When I type "anima other armada" into the model search
    Then the model list is
      | models/anima/anima_baseV10.safetensors |
      | models/anima/other_peoples_data/armada-AB10-full-01.safetensors |
    When I type "no such model" into the model search
    Then "Model" lists "(no matches)"
    When I type "" into the model search
    Then "Model" does not list "moss_image"
    And "Model" lists "anima_aestheticV11.safetensors"

  Scenario: Switching the functional workflow loads its defaults and custom parameters
    Then the custom parameters are
      | Filename prefix |
    When I select "MOSS" as "Functional Workflow"
    Then the form shows
      | Model     | models/MOSS/moss_image_sft_int8_convrot.safetensors |
      | Steps     | 25                                                 |
      | CFG       | 2.5                                                |
      | Sampler   | er_sde                                             |
      | Scheduler | simple                                             |
    And the custom parameters are
      | Filename prefix     |
      | Skip layer guidance |
      | SLG single layers   |
      | SLG double layers |
      | SLG start percent |
      | SLG end percent   |
    And "Model" does not list "anima_aestheticV11"

  Scenario: The form is remembered between visits
    When I fill in
      | Prompt          | safe, a lighthouse at dusk |
      | Negative Prompt | blurry                     |
      | Steps           | 12                         |
      | CFG             | 5.5                        |
      | Sampler         | euler                      |
      | Batch count     | 3                          |
    And I click "Landscape"
    And I uncheck "Random"
    And I set "Seed" in Generation Parameters to "4242"
    And I reload the page
    Then the form shows
      | Prompt          | safe, a lighthouse at dusk |
      | Negative Prompt | blurry                     |
      | Steps           | 12                         |
      | CFG             | 5.5                        |
      | Sampler         | euler                      |
      | Batch count     | 3                          |
      | Width           | 1216                       |
      | Height          | 832                        |
      | Seed            | 4242 | Generation Parameters |
    And "Random" is not checked

  Scenario: Clear resets the page to its defaults
    Given an input image "photo.png" of 320×240 pixels
    When I fill in
      | Prompt | safe, a teapot |
      | Steps  | 9              |
    And I click "Clear" in Main
    Then the form shows
      | Prompt | |
      | Steps  | 30 |
    And the mode is txt2img
    And the Output Gallery is empty
