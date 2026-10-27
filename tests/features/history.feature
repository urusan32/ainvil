@gpu
Feature: Server history
  History… lists the prompts the server ran recently, from every client, with their images. An entry's images
  can go to the gallery, the stash or the input image, and its settings can be loaded into the form.

  Background:
    Given Ainvil is open and connected to the test server
    And test outputs go to the "ainvil-test" folder

  Scenario: A prompt from this tab is listed with its details
    When I fill in
      | Prompt | safe, a blue teapot on a shelf |
      | Width  | 256                            |
      | Height | 256                            |
      | Steps  | 4                              |
    And I uncheck "Random"
    And I set "Seed" in Generation Parameters to "4100"
    And I generate
    And I open the History
    Then the History lists my prompt with
      | success                              |
      | Anima · txt2img · this tab           |
      | safe, a blue teapot on a shelf       |
      | seed 4100                            |
      | models/anima/anima_baseV10.safetensors |
      | 1 image(s)                           |
    And the History entries are newest first

  Scenario: The History's Show selector and Refresh
    When I open the History
    And I select "25" as "Show"
    Then the History shows at most 25 entries
    When I click "Refresh" in the History
    Then the History shows at most 25 entries

  Scenario: Escape and × close the History
    When I open the History
    And I press Escape
    Then the History is closed
    When I open the History
    And I click "×" in the History
    Then the History is closed

  Scenario: An entry's images go to the gallery and the stash
    Given the Output Gallery holds 3 images generated with seeds from 3000
    When I click "Clear" in the Output Gallery
    And I open the History
    Then the History lists my prompt with
      | success   |
      | seed 3002 |
    When I click "Add to Gallery" for my prompt in the History
    Then a toast says "Added 1 image(s) from #"
    And the Output Gallery shows 1 image
    And the gallery info says "seed 3002"
    When I click "Add to Stash" for my prompt in the History
    Then a toast says "to the Image Stash"
    And the Image Stash holds 1 image

  Scenario: An entry's image becomes the input image
    Given the Output Gallery holds 3 images generated with seeds from 3000
    When I open the History
    And I click "Use as Input" for my prompt in the History
    Then the History is closed
    And the mode is img2img
    And the input image is 256×256 pixels

  Scenario: An entry's image opens in the viewer over the History
    Given the Output Gallery holds 3 images generated with seeds from 3000
    When I open the History
    And I click the thumbnail of my prompt in the History
    Then the viewer is open
    When I press Escape
    Then the viewer is closed
    And the History is open

  Scenario: An entry's image and API prompt can be downloaded
    Given the Output Gallery holds 3 images generated with seeds from 3000
    When I open the History
    And I click "Download" for my prompt in the History
    Then a file named like "*.png" is downloaded
    When I click "Prompt JSON" for my prompt in the History
    Then a file named like "prompt-*.json" is downloaded
    And the downloaded file "prompt-*.json" has
      | path         | value                                       |
      | 19.inputs.seed | 3002                                      |
      | 11.inputs.text | "safe, a small red apple on a plain table" |

  Scenario: Load Settings fills the form like dropping the image's PNG
    Given the Output Gallery holds 3 images generated with seeds from 3000
    When I click "Clear" in Main
    And I open the History
    And I click "Load Settings" for my prompt in the History
    Then the History is closed
    And the status says "Loaded settings from history #"
    And the form shows
      | Prompt | safe, a small red apple on a plain table |
      | Width  | 256                                      |
      | Steps  | 4                                        |
      | Seed   | 3002 | Generation Parameters             |
    And "Random" is not checked
