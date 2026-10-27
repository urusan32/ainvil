Feature: Input image and mask
  An input image switches Generate to img2img, and a mask on it to inpainting. Images can be dropped,
  chosen or pasted; masks can be painted in the mask editor, dropped or uploaded, and downloaded.

  Background:
    Given Ainvil is open and connected to the test server

  Scenario: Dropping an image switches to img2img and clearing it goes back to txt2img
    Then the mode is txt2img
    When I drop an image "photo.png" of 320×240 pixels on the input image
    Then the mode is img2img
    And the input image is "photo.png" of 320×240 pixels
    And the input parameters hint says "Input image loaded: img2img mode."
    When I click "Clear" in the image column
    Then the mode is txt2img
    And there is no input image

  Scenario: An image can be chosen with the file picker
    When I choose an image "chosen.jpg" of 200×300 pixels with "Choose…" in Input Image
    Then the input image is "chosen.jpg" of 200×300 pixels

  Scenario: Clicking the empty image box opens the file picker
    When I click the empty input image box and choose "boxed.png" of 64×64 pixels
    Then the input image is "boxed.png" of 64×64 pixels

  Scenario: An image can be pasted onto the Generate tab
    When I paste an image "pasted.png" of 128×96 pixels
    Then the input image is "pasted.png" of 128×96 pixels

  Scenario: A file that isn't an image is refused
    When I drop a text file "notes.txt" on the input image
    Then an error toast says "That file is not an image."
    And the mode is txt2img

  Scenario: A mask can't be added before an image
    When I click "Upload" in Input Image
    Then a toast says "Load an input image first."
    When I click "Download" in Input Image
    Then a toast says "No mask to download."

  Scenario: Painting a mask switches to inpainting
    Given an input image "photo.png" of 320×240 pixels
    When I click the mask box
    Then the mask editor is open
    When I paint a mask stroke from 100, 120 to 220, 120
    Then the mask being edited has painted pixels around 160, 120
    When I click "Done" in the mask editor
    Then the mask editor is closed
    And the mode is inpainting
    And the mask is painted at 100, 120
    And the mask is painted at 220, 120
    And the mask is not painted at 160, 60
    And the input parameters hint says "Image and mask loaded: inpainting mode. Painted areas are regenerated."

  Scenario: Cancel and Escape leave the mask as it was
    Given an input image "photo.png" of 320×240 pixels
    When I open the mask editor
    And I paint a mask stroke from 100, 120 to 220, 120
    And I click "Cancel" in the mask editor
    Then the mode is img2img
    When I open the mask editor
    And I paint a mask stroke from 100, 120 to 220, 120
    And I press Escape
    Then the mask editor is closed
    And the mode is img2img

  Scenario: The mask editor's Fill, Invert, Clear and Undo
    Given an input image "photo.png" of 320×240 pixels
    When I open the mask editor
    And I click "Fill" in the mask editor
    Then the mask being edited covers the whole image
    When I click "Invert" in the mask editor
    Then the mask being edited is empty
    When I click "Undo" in the mask editor
    Then the mask being edited covers the whole image
    When I click "Clear" in the mask editor
    Then the mask being edited is empty
    When I press Ctrl+Z
    Then the mask being edited covers the whole image
    When I click "Clear" in the mask editor
    And I click "Done" in the mask editor
    Then the mode is img2img

  Scenario: Erasing part of the mask
    Given an input image "photo.png" of 320×240 pixels
    And a mask covering 0, 0 of size 320×240
    When I open the mask editor
    And I click "Erase" in the mask editor
    Then the mask editor's active tool is "Erase"
    When I paint a mask stroke from 0, 0 to 0, 239
    And I paint a mask stroke from 0, 0 to 319, 0
    And I click "Done" in the mask editor
    Then the mask is not painted at 0, 0
    And the mask is not painted at 0, 200
    And the mask is not painted at 300, 0
    And the mask is painted at 160, 120
    And the mask is painted at 319, 239

  Scenario: Mask editor keyboard shortcuts
    Given an input image "photo.png" of 320×240 pixels
    When I open the mask editor
    Then the mask editor's active tool is "Paint"
    And the brush size of the mask editor is 40
    When I press x
    Then the mask editor's active tool is "Erase"
    When I press x
    Then the mask editor's active tool is "Paint"
    When I press ]
    Then the brush size of the mask editor is 45
    When I press [
    And I press [
    Then the brush size of the mask editor is 35
    And the "Window" button in the mask editor is hidden

  Scenario: A mask image is white where the image is regenerated
    Given an input image "photo.png" of 320×240 pixels
    When I drop a mask covering 40, 50 of size 100×60 on the mask box
    Then the mode is inpainting
    And the mask covers 40, 50 of size 100×60
    When I click "Download" in Input Image
    Then a file named "photo-mask.png" is downloaded
    And the downloaded mask is white in 40, 50 of size 100×60 and black elsewhere

  Scenario: A mask can be uploaded with the file picker and cleared
    Given an input image "photo.png" of 320×240 pixels
    When I upload a mask covering 10, 20 of size 30×40
    Then the mask covers 10, 20 of size 30×40
    When I click "Clear" in the mask column
    Then the mode is img2img
    And there is no mask

  Scenario: An all-black mask counts as no mask
    Given an input image "photo.png" of 320×240 pixels
    When I drop an all-black mask on the mask box
    Then the mode is img2img
    And there is no mask

  Scenario: A new image of the same size keeps the mask, another size drops it
    Given an input image "first.png" of 320×240 pixels
    And a mask covering 10, 20 of size 30×40
    When I drop an image "second.png" of 320×240 pixels on the input image
    Then the mode is inpainting
    And the mask covers 10, 20 of size 30×40
    When I drop an image "third.png" of 200×200 pixels on the input image
    Then the mode is img2img

  Scenario: The mask color only changes the display
    Given an input image "photo.png" of 320×240 pixels
    And a mask covering 10, 20 of size 30×40
    When I open the mask editor
    And I change the mask color in the mask editor to "#3366ff"
    And I click "Done" in the mask editor
    Then the mask is displayed in "#3366ff"
    And the saved configuration has "clientPreferences.maskColor" = "#3366ff"
    And the mask covers 10, 20 of size 30×40

  Scenario: The input image can be added to the Image Stash
    Given an input image "photo.png" of 320×240 pixels
    When I click "Add to Stash" in Input Image
    Then a toast says "Added the input image to the Image Stash"
    And the Image Stash holds
      | photo.png |
