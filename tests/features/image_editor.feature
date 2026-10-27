Feature: Image editor
  Clicking the input image opens a simple editor that paints real colors onto a copy of it. Nothing changes
  until Done, which makes the edit the input image and adds it to the Image Stash.

  Background:
    Given Ainvil is open and connected to the test server
    And an input image "photo.png" of 320×240 pixels split into a #cc0000 left half and a #0000cc right half
    And I remember the input image

  Scenario: Painting and Done replace the input image and stash it
    When I open the image editor
    Then the image editor's active tool is "Paint"
    When I set the paint color to "#ffff00"
    And I paint from 50, 60 to 150, 60
    Then the edited image pixel at 100, 60 is "#ffff00"
    And the edited image pixel at 100, 150 is "#cc0000"
    When I click "Done" in the image editor
    Then the image editor is closed
    And a toast says "Edited the input image and added it to the Image Stash"
    And the input image has changed
    And the input image is "photo_edit.png" of 320×240 pixels
    And the input image pixel at 100, 60 is "#ffff00"
    And the Image Stash holds
      | photo_edit.png |

  Scenario: Editing an edit keeps one "_edit" in the name
    When I open the image editor
    And I paint from 50, 60 to 150, 60
    And I click "Done" in the image editor
    Then the input image is named like "photo_edit.png"
    When I open the image editor
    And I paint from 50, 100 to 150, 100
    And I click "Done" in the image editor
    Then the input image is named like "photo_edit.png"
    And the Image Stash holds 2 images

  Scenario: Cancel, Escape and Done without edits leave the image alone
    When I open the image editor
    And I paint from 50, 60 to 150, 60
    And I click "Cancel" in the image editor
    Then the image editor is closed
    And the input image is unchanged
    When I open the image editor
    And I paint from 50, 60 to 150, 60
    And I press Escape
    Then the image editor is closed
    And the input image is unchanged
    When I open the image editor
    And I click "Done" in the image editor
    Then the image editor is closed
    And the input image is unchanged
    And the Image Stash is empty

  Scenario: Erase paints the original image back
    When I open the image editor
    And I set the paint color to "#00ff00"
    And I paint from 50, 60 to 150, 60
    And I click "Erase" in the image editor
    And I paint from 40, 60 to 160, 60
    Then the edited image pixel at 100, 60 is "#cc0000"

  Scenario: Undo and Clear
    When I open the image editor
    And I set the paint color to "#00ff00"
    And I paint from 50, 60 to 150, 60
    And I paint from 50, 100 to 150, 100
    And I click "Undo" in the image editor
    Then the edited image pixel at 100, 60 is "#00ff00"
    And the edited image pixel at 100, 100 is "#cc0000"
    When I press Ctrl+Z
    Then the edited image pixel at 100, 60 is "#cc0000"
    When I paint from 50, 60 to 150, 60
    And I click "Clear" in the image editor
    Then the edited image pixel at 100, 60 is "#cc0000"

  Scenario: Flood fill fills the clicked area within the tolerance
    Given an input image "grey.png" of 200×100 pixels split into a #808080 left half and a #848484 right half
    When I open the image editor
    And I click "Fill" in the image editor
    Then I see "Tolerance" in the image editor
    When I set the paint color to "#00ff00"
    And I set the tolerance to 2
    And I click the image editor at 20, 50
    Then the edited image pixel at 50, 50 is "#00ff00"
    And the edited image pixel at 150, 50 is "#848484"
    When I click "Undo" in the image editor
    And I set the tolerance to 10
    And I click the image editor at 20, 50
    Then the edited image pixel at 150, 50 is "#00ff00"

  Scenario: A selection keeps painting and filling inside it
    When I open the image editor
    And I click "Select" in the image editor
    And I drag in the image editor from 0, 0 to 160, 120
    Then the selection is 0, 0 of size 160×120
    And the "Deselect" button is visible
    And the "Crop" button in the image editor is visible
    When I click "Paint" in the image editor
    And I set the paint color to "#ffff00"
    And I paint from 100, 60 to 250, 60
    Then the edited image pixel at 120, 60 is "#ffff00"
    And the edited image pixel at 200, 60 is "#0000cc"
    When I click "Fill" in the image editor
    And I set the paint color to "#00ff00"
    And I click the image editor at 20, 20
    Then the edited image pixel at 20, 100 is "#00ff00"
    And the edited image pixel at 20, 200 is "#cc0000"
    When I click "Deselect" in the image editor
    Then there is no selection

  Scenario: A selection can be moved, and a click outside it deselects
    When I open the image editor
    And I click "Select" in the image editor
    And I drag in the image editor from 10, 10 to 110, 60
    And I drag in the image editor from 50, 30 to 150, 130
    Then the selection is 110, 110 of size 100×50
    When I drag in the image editor from 300, 20 to 300, 20
    Then there is no selection

  Scenario: Crop makes the selection the input image and crops the mask with it
    Given a mask covering 100, 50 of size 100×100
    When I open the image editor
    And I click "Select" in the image editor
    And I drag in the image editor from 80, 40 to 240, 160
    And I click "Crop" in the image editor
    Then a toast says "Cropped to 160×120 and added it to the Image Stash"
    And the input image is "photo_crop_160x120.png" of 160×120 pixels
    And the mask covers 20, 10 of size 100×100
    And the Image Stash holds
      | photo_crop_160x120.png |

  Scenario: The eyedropper and Alt+click pick the paint color
    When I open the image editor
    And I click "Pick" in the image editor
    And I click the image editor at 250, 100
    Then the paint color is "#0000cc"
    When I click "Paint" in the image editor
    And I alt-click the image editor at 50, 100
    Then the paint color is "#cc0000"
    And the edited image pixel at 50, 100 is "#cc0000"

  Scenario: Used paint colors become swatches
    When I open the image editor
    And I set the paint color to "#ff0000"
    And I paint from 10, 10 to 20, 10
    And I set the paint color to "#00ff00"
    And I paint from 10, 30 to 20, 30
    And I set the paint color to "#ff0000"
    And I paint from 10, 50 to 20, 50
    Then the recent colors are
      | #ff0000 |
      | #00ff00 |
    When I click the recent color "#00ff00"
    Then the paint color is "#00ff00"
    And the saved configuration has "clientPreferences.recentColors" = ["#ff0000", "#00ff00"]

  Scenario: Only the 6 most recent paint colors are kept
    When I open the image editor
    And I set the paint color to "#000001"
    And I paint from 10, 10 to 20, 10
    And I set the paint color to "#000002"
    And I paint from 10, 10 to 20, 10
    And I set the paint color to "#000003"
    And I paint from 10, 10 to 20, 10
    And I set the paint color to "#000004"
    And I paint from 10, 10 to 20, 10
    And I set the paint color to "#000005"
    And I paint from 10, 10 to 20, 10
    And I set the paint color to "#000006"
    And I paint from 10, 10 to 20, 10
    And I set the paint color to "#000007"
    And I paint from 10, 10 to 20, 10
    Then the recent colors are
      | #000007 |
      | #000006 |
      | #000005 |
      | #000004 |
      | #000003 |
      | #000002 |

  Scenario: Keyboard shortcuts pick the tools
    When I open the image editor
    And I press f
    Then the image editor's active tool is "Fill"
    When I press s
    Then the image editor's active tool is "Select"
    When I press i
    Then the image editor's active tool is "Pick"
    When I press h
    Then the image editor's active tool is "Pan"
    When I press b
    Then the image editor's active tool is "Paint"
    When I press x
    Then the image editor's active tool is "Erase"
    When I press x
    Then the image editor's active tool is "Paint"

  Scenario: Ctrl+D deselects
    When I open the image editor
    And I press s
    And I drag in the image editor from 10, 10 to 110, 60
    And I press Ctrl+D
    Then there is no selection

  Scenario: The mouse wheel and +/- zoom, and Reset Zoom fits the image again
    When I open the image editor
    Then the "Reset Zoom" button is disabled
    When I remember the image editor zoom
    And I scroll the mouse wheel up over the image editor at 80, 60
    Then the image editor is zoomed in
    And the "Reset Zoom" button is enabled
    When I click "Reset Zoom"
    Then the image editor fits the image
    When I press +
    Then the image editor is zoomed in
    When I remember the image editor zoom
    And I press -
    Then the image editor is zoomed out
    When I press 0
    Then the image editor fits the image

  Scenario Outline: Panning a zoomed image
    When I open the image editor
    And I press +
    And I press +
    And <how to pan>
    And I drag the image editor stage by 30, 20 screen pixels<with>
    Then the image editor is panned by 30, 20

    Examples:
      | how to pan                         | with                    |
      | I click "Pan" in the image editor  |                         |
      | I hold Space                       |                         |
      | I press b                          | with the middle button  |
