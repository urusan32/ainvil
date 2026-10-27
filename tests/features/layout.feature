Feature: Arranging the Generate tab
  The Generate tab uses 3, 2 or 1 columns depending on the window width. In Edit layout mode, sections can
  be dragged by their header to another place and hidden. Each column count keeps its own arrangement;
  hidden sections apply to all of them.

  Background:
    Given Ainvil is open and connected to the test server

  Scenario: Three columns on a wide window
    Then the Generate columns are
      | Main, Generation Parameters, Custom Parameters |
      | Output Gallery, LoRA                           |
      | Input Image, Input Parameters, CADS            |

  Scenario: Two columns on a medium window
    When I resize the window to 1100 × 1000 pixels
    Then the Generate columns are
      | Main, Output Gallery, Custom Parameters                    |
      | Generation Parameters, Input Image, Input Parameters, CADS, LoRA |

  Scenario: One column on a narrow window
    When I resize the window to 800 × 1000 pixels
    Then the Generate columns are
      | Main, Output Gallery, Input Image, Input Parameters, Generation Parameters, Custom Parameters, LoRA, CADS |

  Scenario: Edit layout is offered on the Generate tab only
    When I click "Edit layout"
    Then the layout editor is open
    And I see "3 columns (window 1400 px or wider)" in the layout bar
    When I open the "Extras" tab
    Then the "Edit layout" button is hidden
    When I open the "Generate" tab
    Then the layout editor is closed

  Scenario: Dragging a section by its header moves it and saves the layout
    When I click "Edit layout"
    And I drag the "LoRA" section above the "Generation Parameters" section
    Then the Generate columns are
      | Main, LoRA, Generation Parameters, Custom Parameters |
      | Output Gallery                                       |
      | Input Image, Input Parameters, CADS                  |
    When I drag the "Main" section to the bottom of column 2
    Then the Generate columns are
      | LoRA, Generation Parameters, Custom Parameters |
      | Output Gallery, Main                           |
      | Input Image, Input Parameters, CADS            |
    When I click "Done" in the layout bar
    And I reload the page
    Then the Generate columns are
      | LoRA, Generation Parameters, Custom Parameters |
      | Output Gallery, Main                           |
      | Input Image, Input Parameters, CADS            |

  Scenario: Sections can't be dragged outside Edit layout
    When I drag the "LoRA" section above the "Generation Parameters" section
    Then the Generate columns are
      | Main, Generation Parameters, Custom Parameters |
      | Output Gallery, LoRA                           |
      | Input Image, Input Parameters, CADS            |

  Scenario: Escape during a drag leaves the section where it was
    When I click "Edit layout"
    And I start dragging the "LoRA" section and press Escape
    Then the Generate columns are
      | Main, Generation Parameters, Custom Parameters |
      | Output Gallery, LoRA                           |
      | Input Image, Input Parameters, CADS            |
    And the layout editor is open
    When I press Escape
    Then the layout editor is closed

  Scenario: Hidden sections are only shown, marked, while editing
    When I click "Edit layout"
    And I click "Hide" on the "CADS" section
    Then the "CADS" section is shown dimmed and marked "Hidden"
    When I click "Done" in the layout bar
    Then the "CADS" section is hidden
    When I resize the window to 1100 × 1000 pixels
    Then the "CADS" section is hidden
    When I click "Edit layout"
    And I click "Show" on the "CADS" section
    And I click "Done" in the layout bar
    Then the "CADS" section is shown

  Scenario: Each width has its own arrangement, and Reset restores the default for this width
    When I click "Edit layout"
    And I drag the "LoRA" section above the "Generation Parameters" section
    And I click "Hide" on the "CADS" section
    And I resize the window to 1100 × 1000 pixels
    Then the Generate columns are
      | Main, Output Gallery, Custom Parameters                    |
      | Generation Parameters, Input Image, Input Parameters, CADS, LoRA |
    When I resize the window to 1600 × 1000 pixels
    Then the Generate columns are
      | Main, LoRA, Generation Parameters, Custom Parameters |
      | Output Gallery                                       |
      | Input Image, Input Parameters, CADS                  |
    When I click "Reset to default" in the layout bar
    Then the Generate columns are
      | Main, Generation Parameters, Custom Parameters |
      | Output Gallery, LoRA                           |
      | Input Image, Input Parameters, CADS            |
    And the "CADS" section is shown
    And the configuration has "clientPreferences.layouts" = {}
