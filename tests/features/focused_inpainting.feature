Feature: Focused inpainting
  Focused inpainting ("Only Masked") inpaints a context window around the mask at the full generation size,
  then scales the result back and pastes it into the original through the mask. The window is the mask's
  bounds plus a border (By Size) or placed by hand in the mask editor (Manual Select), always at the
  generation aspect ratio.

  Background:
    Given Ainvil is open and connected to the test server
    And test outputs go to the "ainvil-test" folder
    And an input image "photo.png" of 640×480 pixels
    And a mask covering 300, 200 of size 40×40
    And I fill in
      | Prompt | safe, a small blue flower |
      | Width  | 512                       |
      | Height | 512                       |

  Scenario: The inpaint area controls
    Then the "Context window size" field is hidden
    When I click "Focused"
    Then I see "By Size" in Input Parameters
    And "Context window size" shows "32"
    And "Crop" is disabled
    When I click "Manual Select"
    Then the "Context window size" field is hidden
    When I click "Whole Image"
    Then "Crop" is enabled

  Scenario Outline: By Size: the mask's bounds plus the border, widened to the generation aspect ratio
    When I click "Focused"
    And I set "Context window size" to "<border>"
    And I fill in
      | Width  | <width>  |
      | Height | <height> |
    Then the context window is <window>
    And the input parameters hint says "Focused: the <size> context window at (<x>, <y>) is inpainted at <width>×<height>, then scaled back and pasted into the image."
    And the context window is shown on the mask box

    Examples:
      | border | width | height | window                    | size    | x   | y   |
      | 32     | 512   | 512    | 268, 168 of size 104×104 | 104×104 | 268 | 168 |
      | 0      | 512   | 512    | 300, 200 of size 40×40   | 40×40   | 300 | 200 |
      | 32     | 1216  | 832    | 244, 168 of size 152×104 | 152×104 | 244 | 168 |
      | 32     | 832   | 1216   | 268, 144 of size 104×152 | 104×152 | 268 | 144 |

  Scenario: By Size keeps the window inside the image
    Given a mask covering 600, 440 of size 40×40
    When I click "Focused"
    Then the context window is 568, 408 of size 72×72

  Scenario: Manual Select starts from the By Size window and is moved with the Window tool
    When I click "Focused"
    And I click "Manual Select"
    Then the context window is 268, 168 of size 104×104
    When I open the mask editor
    Then the mask editor shows "Context window 104×104 → 512×512"
    When I click "Window" in the mask editor
    And I move the mouse over 320, 220 in the mask editor
    Then the mask editor's cursor is "move"
    When I move the mouse over 268, 168 in the mask editor
    Then the mask editor's cursor is "nwse-resize"
    When I move the mouse over 20, 20 in the mask editor
    Then the mask editor's cursor is "crosshair"
    When I drag the window from 320, 220 to 420, 260
    Then the mask editor shows "Context window 104×104 → 512×512"
    When I click "Done" in the mask editor
    Then the context window is 368, 208 of size 104×104
    And the input parameters hint says "Part of the mask is outside the context window and stays as it is."

  Scenario: The mouse wheel resizes the manual window
    When I click "Focused"
    And I click "Manual Select"
    And I open the mask editor
    And I press w
    Then the mask editor's active tool is "Window"
    When I scroll the mouse wheel up over the mask editor
    Then the mask editor shows "Context window 95×95 → 512×512"
    When I press w
    Then the mask editor's active tool is "Paint"

  Scenario: Dragging outside the window draws a new one at the generation aspect ratio
    When I click "Focused"
    And I click "Manual Select"
    And I open the mask editor
    And I click "Window" in the mask editor
    And I drag the window from 10, 10 to 210, 110
    And I click "Done" in the mask editor
    Then the context window is 10, 10 of size 200×200

  Scenario: The manual window follows the generation aspect ratio
    When I click "Focused"
    And I click "Manual Select"
    And I click "Landscape"
    Then the context window has the aspect ratio of 1216×832
    And the context window is 257, 177 of size 126×86

  Scenario: The window tool's Crop makes the window the input image
    When I click "Focused"
    And I click "Manual Select"
    And I open the mask editor
    And I click "Window" in the mask editor
    And I click "Crop" in the mask editor
    Then a toast says "Cropped to 104×104 and added it to the Image Stash"
    And the input image is "photo_crop_104x104.png" of 104×104 pixels
    And the mask covers 32, 32 of size 40×40
    And the Image Stash holds
      | photo_crop_104x104.png |

  Scenario: The window is only offered for Focused Manual Select
    When I open the mask editor
    Then the "Window" button in the mask editor is hidden
    And the mask editor shows no context window
    When I press w
    Then the mask editor's active tool is "Paint"

  Scenario: The workflow inpaints the window and pastes it back through the mask
    When I check "Crop"
    And I click "Focused"
    And I set "Batch size" to "2"
    And I download the workflow
    Then the workflow loads the input image from "ainvil/ainvil_[0-9a-f]{14}_m[0-9a-f]{14}\.png"
    And the workflow sets
      | node | input  | value      |
      | 53   | width  | 512        |
      | 53   | height | 512        |
      | 53   | crop   | "disabled" |
    And the workflow has a node titled "Ainvil original image" with
      | input | value                                    |
      | image | /^ainvil\/ainvil_[0-9a-f]{14}\.png$/     |
    And the workflow has a node titled "Ainvil repeat original" with
      | input  | value |
      | amount | 2     |
    And the workflow has a node titled "Ainvil scale back" with
      | input          | value     |
      | width          | 104       |
      | height         | 104       |
      | upscale_method | "lanczos" |
    And the workflow has a node titled "Ainvil paste back" with
      | input         | value  |
      | x             | 268    |
      | y             | 168    |
      | resize_source | false  |
      | mask          | ["51", 1] |
    And the "destination" input of the "Ainvil paste back" node is linked to the "Ainvil repeat original" node
    And the "source" input of the "Ainvil paste back" node is linked to the "Ainvil scale back" node
    And the "image" input of the "Ainvil scale back" node is linked to the "VAEDecode" node
    And the workflow node 46 "images" is linked to the "Ainvil paste back" node

  Scenario: Whole Image inpainting adds no paste-back
    When I download the workflow
    Then the workflow has no node titled "Ainvil paste back"
    And the workflow has no node titled "Ainvil original image"

  Scenario: A window without any of the mask can't be generated
    When I click "Focused"
    And I click "Manual Select"
    And I open the mask editor
    And I click "Window" in the mask editor
    And I drag the window from 320, 220 to 50, 50
    And I click "Done" in the mask editor
    And I click "Generate Workflow"
    Then the status is an error saying "The context window contains none of the mask. Move it over the masked area (mask editor › Window)."

  Scenario: The Focused settings are remembered
    When I click "Focused"
    And I click "Manual Select"
    And I reload the page
    Then the saved Generate form has "inpaintMode" = "focused"
    And the saved Generate form has "ctxMode" = "manual"
