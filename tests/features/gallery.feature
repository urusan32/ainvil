@gpu
Feature: Output Gallery and the full-screen viewer
  The Output Gallery shows the latest run: a large selected image and thumbnails. Images open in a
  full-screen viewer and can be downloaded, stashed, reused as the input image or sent to Extras.

  Background:
    Given Ainvil is open and connected to the test server
    And test outputs go to the "ainvil-test" folder
    And the Output Gallery holds 3 images generated with seeds from 3000

  Scenario: Thumbnails select the image shown large
    Then the Output Gallery shows 3 images
    And gallery thumbnail 1 is selected
    And the gallery info says "1 / 3 · seed 3000"
    When I click gallery thumbnail 3
    Then gallery thumbnail 3 is selected
    And the gallery info says "3 / 3 · seed 3002"

  Scenario: The viewer shows the full image and browses with the arrow keys
    When I click gallery thumbnail 2
    And I click the main gallery image
    Then the viewer is open
    And the viewer shows image 2
    And the viewer loads the image from the server with its filename
    When I press ArrowRight
    Then the viewer shows image 3
    When I press ArrowRight
    Then the viewer shows image 1
    When I press ArrowLeft
    Then the viewer shows image 3
    When I click "›" in the viewer
    Then the viewer shows image 1
    When I click "‹" in the viewer
    Then the viewer shows image 3
    And gallery thumbnail 3 is selected
    When I press Escape
    Then the viewer is closed

  Scenario: The viewer closes with × or a click beside the image
    When I click the main gallery image
    And I click "×" in the viewer
    Then the viewer is closed
    When I click the main gallery image
    And I click the viewer background
    Then the viewer is closed

  Scenario: The viewer's Download saves the image under its own name
    When I click the main gallery image
    And I click "Download" in the viewer
    Then the downloaded image is gallery image 1

  Scenario: Download Selected and Download All
    When I click gallery thumbnail 2
    And I click "Download Selected"
    Then the downloaded image is gallery image 2
    When I click "Download All"
    Then a toast says "Packing 3 images…"
    And a file named like "ainvil-batch-*.zip" is downloaded
    And the downloaded ZIP "ainvil-batch-*.zip" holds 3 PNG images
    And the ZIP entries are named like the gallery images

  Scenario: Use Seed copies the selected image's seed and turns Random off
    Given "Random" is checked
    When I click gallery thumbnail 3
    And I click "Use Seed"
    Then a toast says "Seed set to 3002"
    And "Seed" in Generation Parameters shows "3002"
    And "Random" is not checked

  Scenario: Use as Input loads the selected image for img2img
    When I click gallery thumbnail 2
    And I click "Use as Input" in the Output Gallery
    Then the mode is img2img
    And the input image is 256×256 pixels

  Scenario: Send to Extras adds the image to the Extras workflow's images
    When I click "Send to Extras"
    Then the "Extras" tab is shown
    And "Image" in Extras says "1 image"

  Scenario: Add to Stash stashes every image in the gallery, and so does the viewer for one
    When I click "Add to Stash" in the Output Gallery
    Then a toast says "Added 3 image(s) to the Image Stash"
    And the Image Stash holds 3 images
    When I click "Clear" in the Output Gallery
    Then the Output Gallery is empty
    And the Image Stash holds 3 images

  Scenario: The viewer's Add to Stash
    When I click the main gallery image
    And I click "Add to Stash" in the viewer
    Then a toast says "Added the image to the Image Stash"
    And the Image Stash holds 1 image

  Scenario: "On all clears" stashes the images when the gallery is cleared by hand
    Given the configuration has "clientPreferences.autoStash" set to "all"
    And the Output Gallery holds 3 images generated with seeds from 3000
    When I click "Clear" in the Output Gallery
    Then a toast says "Added 3 image(s) from the Output Gallery to the Image Stash"
    And the Image Stash holds 3 images

  Scenario: An empty gallery says so
    When I click "Clear" in the Output Gallery
    And I click "Download All"
    Then a toast says "No images to download"
    When I click "Download Selected"
    Then a toast says "No image selected"
    When I click "Add to Stash" in the Output Gallery
    Then a toast says "No images to stash"
    And nothing is downloaded
