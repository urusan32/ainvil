Feature: Saving, exporting and importing the configuration
  The configuration lives in the browser's localStorage. It can be exported as one JSON file and imported
  on another computer; a bad file shows an error with developer details and changes nothing.

  Background:
    Given Ainvil is open and connected to the test server
    And the "Configuration" tab is open

  Scenario: Export downloads the whole configuration as version 1 JSON
    When I click "Export configuration"
    Then a file named "ainvil-config.json" is downloaded
    And the downloaded file "ainvil-config.json" has
      | path                                  | value                    |
      | version                               | 1                        |
      | connection.apiUrl                     | "http://10.0.0.137:8188/" |
      | functionalWorkflows[0].name           | "Anima"                  |
      | functionalWorkflows[1].name           | "MOSS"                   |
      | functionalWorkflows[0].workflows.txt2img.workflow | <object>     |
      | customWorkflows[0].name               | "Upscale with model"     |
      | serverPreferences.saveImage           | true                     |
      | serverPreferences.scaleMethod         | "lanczos"                |
      | serverPreferences.upscaleModel        | ""                       |
      | clientPreferences.galleryColumns      | 3                        |
      | clientPreferences.galleryRows         | 2                        |
      | clientPreferences.maskColor           | "#ff285a"                |
      | clientPreferences.multipleJobs        | true                     |
      | clientPreferences.galleryClear        | "generate"               |
      | clientPreferences.autoStash           | "no"                     |
      | clientPreferences.showLivePreview     | true                     |

  Scenario: A configuration survives export, reset and import
    When I select "4" as "Gallery thumbnails per row"
    And I uncheck "Save Image"
    And I click "Export configuration"
    And I click "Reset to defaults"
    Then I was asked "Replace the whole configuration with the built-in defaults?"
    And a toast says "Configuration reset (connection kept)"
    And "Gallery thumbnails per row" shows "3"
    And "Save Image" is checked
    And the import error box is hidden
    When I drop the downloaded "ainvil-config.json" on the import box
    Then the import box shows "Selected: ainvil-config.json"
    When I click "Import (overwrites current configuration)"
    Then a toast says "Configuration imported"
    And "Gallery thumbnails per row" shows "4"
    And "Save Image" is not checked
    And the "Import (overwrites current configuration)" button is disabled

  Scenario: The import file can also be chosen with the file picker
    When I click "Export configuration"
    And I choose the downloaded "ainvil-config.json" with "choose a file"
    Then the import box shows "Selected: ainvil-config.json"
    And the "Import (overwrites current configuration)" button is enabled

  Scenario: Import is disabled until a file is chosen
    Then the "Import (overwrites current configuration)" button is disabled

  Scenario: Answering Cancel keeps the configuration
    Given I will answer "Cancel" to the confirmation
    When I select "1" as "Gallery rows before scrolling"
    And I click "Reset to defaults"
    Then "Gallery rows before scrolling" shows "1"

  Scenario Outline: A bad import file shows why and changes nothing
    When I select "2" as "Gallery thumbnails per row"
    And I drop a file "<file>" on the import box containing
      """
      <content>
      """
    And I click "Import (overwrites current configuration)"
    Then the import error says "<error>"
    And the import error says "the current configuration was not changed"
    And "Gallery thumbnails per row" shows "2"

    Examples:
      | file          | content                                   | error                                                         |
      | broken.json   | {"version": 1,                            | Invalid JSON in broken.json                                   |
      | old.json      | {"functionalWorkflows": []}               | Configuration: missing \"version\" field.                       |
      | future.json   | {"version": 2}                            | Configuration: unsupported version 2 (this build understands version 1). |
      | list.json     | [1, 2, 3]                                 | Configuration: expected a JSON object, got an array.          |
      | single.json   | {"version": 1, "type": "functionalWorkflow", "workflow": {}} | This is a single-workflow export                |
      | badfw.json    | {"version": 1, "functionalWorkflows": [{"name": "X", "workflows": {"txt2img": {"workflow": {"a": 1}}}}]} | functionalWorkflows[0] txt2img workflow: not a ComfyUI workflow |
      | badmap.json   | {"version": 1, "functionalWorkflows": [{"name": "X", "workflows": {"txt2img": {"mappings": {"seed": [{"input": "seed"}]}}}}]} | functionalWorkflows[0].workflows.txt2img.mappings.seed[0]: each target needs a \"node\". |

  Scenario: A ComfyUI workflow dropped on the import box is explained
    When I drop the workflow file "txt2img-minworkflow.json" on the import box
    And I click "Import (overwrites current configuration)"
    Then the import error says "This is a ComfyUI workflow, not an Ainvil configuration."

  Scenario: Imported preferences are cleaned up
    When I drop a file "partial.json" on the import box containing
      """
      {"version": 1, "connection": {"apiUrl": "http://10.0.0.137:8188/"},
       "clientPreferences": {"galleryColumns": 9, "maskColor": "#ABCDEF", "galleryClear": "sometimes",
                             "recentColors": ["#FF0000", "red", "#00ff00"],
                             "layouts": {"3": [["sec-main", "nope"], ["sec-gallery"], ["sec-input", "sec-main"]]},
                             "hiddenSections": ["sec-cads", "sec-cads", "bogus"]},
       "functionalWorkflows": [], "customWorkflows": []}
      """
    And I click "Import (overwrites current configuration)"
    Then a toast says "Configuration imported"
    And the configuration has "clientPreferences.galleryColumns" = 3
    And the configuration has "clientPreferences.maskColor" = "#abcdef"
    And the configuration has "clientPreferences.galleryClear" = "generate"
    And the configuration has "clientPreferences.recentColors" = ["#ff0000", "#00ff00"]
    And the configuration has "clientPreferences.hiddenSections" = ["sec-cads"]
    And the configuration has "clientPreferences.layouts.3" = [["sec-main"], ["sec-gallery"], ["sec-input", "sec-inparams", "sec-params", "sec-custom", "sec-lora", "sec-cads"]]
    And the configuration has "serverPreferences.saveImage" = true
    And I see "No functional workflows configured."
    When I open the "Generate" tab
    Then "Functional Workflow" lists "(none configured)"

  @js-errors
  Scenario: An invalid stored configuration is replaced by the defaults
    Given the stored configuration is
      """
      {"version": 7}
      """
    Then an error toast says "Stored configuration was invalid and has been replaced by defaults"
    And "ComfyUI API URL" shows "http://localhost:8188/"

  Scenario: The configuration is kept between visits
    When I uncheck "Allow multiple jobs"
    And I select "never" as "Clear the Output Gallery"
    And I reload the page
    Then "Allow multiple jobs" is not checked
    And "Clear the Output Gallery" shows "never"
    And the saved configuration has "clientPreferences.galleryClear" = "never"
