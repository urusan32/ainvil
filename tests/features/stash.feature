Feature: Image Stash
  The Image Stash is a list of images kept in this browser (IndexedDB), newest first. Images can be pinned
  so Clear keeps them, reused as the input image, downloaded, added to the gallery or removed.

  Background:
    Given Ainvil is open and connected to the test server

  Scenario: An empty stash says how to fill it
    When I open the Image Stash
    Then the Image Stash dialog says "The stash is empty."
    And the "Clear All" button is disabled

  Scenario: Images dropped on the stash are listed newest first
    When I open the Image Stash
    And I drop these images on the Image Stash
      | name    | size    |
      | one.png | 64×64   |
      | two.png | 80×60   |
    Then the Image Stash dialog lists
      | name    |
      | two.png |
      | one.png |
    And the Image Stash dialog says "2 image(s)"

  Scenario: The drop box also opens a file picker
    When I open the Image Stash
    And I click the Image Stash drop box and choose these images
      | name       | size  |
      | chosen.png | 40×40 |
    Then the Image Stash dialog lists
      | name       |
      | chosen.png |

  Scenario: A file that isn't an image is refused
    When I open the Image Stash
    And I drop a text file "notes.txt" on the Image Stash
    Then an error toast says "notes.txt is not an image."
    And the Image Stash is empty

  Scenario: Stashing an image again moves it to the top
    Given the Image Stash holds the images
      | name    | size  |
      | one.png | 64×64 |
      | two.png | 80×60 |
    When I open the Image Stash
    And I drop these images on the Image Stash
      | name    | size  |
      | one.png | 64×64 |
    Then the Image Stash dialog lists
      | name    |
      | one.png |
      | two.png |

  Scenario: Clear keeps the pinned images, Clear All removes everything after asking
    Given the Image Stash holds the images
      | name      | size  |
      | one.png   | 64×64 |
      | two.png   | 80×60 |
      | three.png | 32×32 |
    When I open the Image Stash
    And I click "Pin" for "two.png" in the Image Stash
    Then the Image Stash dialog lists
      | name      | pin    |
      | three.png | Pin    |
      | two.png   | Pinned |
      | one.png   | Pin    |
    And the Image Stash dialog says "3 image(s), 1 pinned"
    When I click "Clear" in the Image Stash
    Then the Image Stash dialog lists
      | name    | pin    |
      | two.png | Pinned |
    And the "Clear" button in the Image Stash is disabled
    Given I will answer "Cancel" to the confirmation
    When I click "Clear All" in the Image Stash
    Then I was asked "Remove every image from the Image Stash, including the pinned ones?"
    And the Image Stash holds 1 image

  Scenario: Clear All empties the stash
    Given the Image Stash holds the images
      | name    | size  |
      | one.png | 64×64 |
    When I open the Image Stash
    And I click "Pin" for "one.png" in the Image Stash
    And I click "Clear All" in the Image Stash
    Then the Image Stash is empty

  Scenario: The stash is kept between visits, pins included
    Given the Image Stash holds the images
      | name    | size  |
      | one.png | 64×64 |
      | two.png | 80×60 |
    When I open the Image Stash
    And I click "Pin" for "one.png" in the Image Stash
    And I reload the page
    And I open the Image Stash
    Then the Image Stash dialog lists
      | name    | pin    |
      | two.png | Pin    |
      | one.png | Pinned |

  Scenario: A stashed image becomes the input image
    Given the Image Stash holds the images
      | name    | size  |
      | one.png | 64×48 |
    When I open the Image Stash
    And I click "Use as Input" for "one.png" in the Image Stash
    Then the Image Stash dialog is closed
    And the input image is "one.png" of 64×48 pixels

  Scenario: A stashed image goes to the gallery, downloads and can be removed
    Given the Image Stash holds the images
      | name    | size  |
      | one.png | 64×48 |
    When I open the Image Stash
    And I click "Add to Gallery" for "one.png" in the Image Stash
    Then a toast says "Added one.png to the Output Gallery"
    And the gallery image 1 is "one.png"
    When I click "Download" for "one.png" in the Image Stash
    Then a file named "one.png" is downloaded
    And the "Load Settings" button in the Image Stash is disabled
    And the "Prompt JSON" button in the Image Stash is disabled
    When I click "Remove" for "one.png" in the Image Stash
    Then the Image Stash is empty

  Scenario: Stashed images open in the viewer without "Add to Stash"
    Given the Image Stash holds the images
      | name    | size  |
      | one.png | 64×48 |
      | two.png | 48×64 |
    When I open the Image Stash
    And I click the thumbnail of "two.png" in the Image Stash
    Then the viewer is open
    And the viewer shows "two.png"
    And the "Add to Stash" button in the viewer is hidden
    When I press ArrowRight
    Then the viewer shows "one.png"
    When I press Escape
    And I press Escape
    Then the Image Stash dialog is closed

  Scenario: Reset to defaults also empties the stash
    Given the Image Stash holds the images
      | name    | size  |
      | one.png | 64×48 |
    When I open the "Configuration" tab
    And I click "Reset to defaults"
    Then I was asked "This also empties the Image Stash, including the pinned images."
    And the Image Stash is empty
