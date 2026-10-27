Feature: Configuring custom workflows for the Extras tab
  A custom workflow is any ComfyUI workflow with parameters the user defines (name, type, default, help text,
  options or a regex filter for combos, and the node inputs they set). Upscale with model is built in.

  Background:
    Given Ainvil is open and connected to the test server
    And the "Configuration" tab is open
    And "Custom Workflows (Extras)" is expanded

  Scenario: Upscale with model is configured by default
    Then the custom workflows are
      | name               | status              |
      | Upscale with model | 6 nodes · UI format |
    When I click "+ Built-in examples"
    Then a toast says "All built-in custom workflows are already configured."

  Scenario: A deleted built-in workflow can be added back
    When I expand "Upscale with model"
    And I click "Delete" in "Upscale with model"
    Then I was asked "Delete custom workflow \"Upscale with model\"?"
    And I see "No custom workflows configured."
    When I open the "Extras" tab
    Then I see "No custom workflows are configured." in Extras
    When I open the "Configuration" tab
    And I click "+ Built-in examples"
    Then a toast says "Added Upscale with model"
    And the custom workflows are
      | name               | status              |
      | Upscale with model | 6 nodes · UI format |

  Scenario: A new custom workflow with a parameter shows up in Extras
    When I click "+ New custom workflow"
    Then the custom workflows are
      | name                 | status              |
      | Upscale with model   | 6 nodes · UI format |
      | New custom workflow  | no workflow         |
    When I open the "Extras" tab
    And I select "New custom workflow" as "Workflow"
    Then I see "This custom workflow has no ComfyUI workflow loaded yet" in Extras
    And I see "This workflow has no parameters." in Extras
    When I click "Generate Workflow" in Extras
    Then the Extras status is an error saying "\"New custom workflow\" has no ComfyUI workflow loaded."
    When I open the "Configuration" tab
    And I load the workflow file "upscale_with_model.json" into "New custom workflow"
    And I click "+ Add parameter" in "New custom workflow"
    And I set parameter 1 of "New custom workflow" to
      | Name                                   | Target width                 |
      | Type                                   | int                          |
      | Default (empty = value in the workflow) | 640                         |
      | Help text                              | How wide the result will be  |
    And I map parameter 1 of "New custom workflow" to node "11" input "width"
    And I open the "Extras" tab
    Then the Extras parameters are
      | Target width |
    And the Extras hint for "Target width" is "How wide the result will be"
    And "Target width" shows "640"
    When I download the Extras workflow
    Then the workflow sets node 11 "width" to 640

  Scenario: An empty default uses the value in the workflow
    When I click "+ New custom workflow"
    And I load the workflow file "upscale_with_model.json" into "New custom workflow"
    And I click "+ Add parameter" in "New custom workflow"
    And I set parameter 1 of "New custom workflow" to
      | Name | Final height |
      | Type | int          |
    And I map parameter 1 of "New custom workflow" to node "11" input "height"
    And I open the "Extras" tab
    And I select "New custom workflow" as "Workflow"
    Then "Final height" shows "1536"

  Scenario: Parameter types show the matching fields
    When I click "+ New custom workflow"
    And I load the workflow file "upscale_with_model.json" into "New custom workflow"
    And I click "+ Add parameter" in "New custom workflow"
    Then parameter 1 of "New custom workflow" shows the fields
      | Name                                    |
      | Type                                    |
      | Default (empty = value in the workflow) |
      | Help text                               |
    When I set parameter 1 of "New custom workflow" to
      | Type | image |
    Then parameter 1 of "New custom workflow" shows the fields
      | Name      |
      | Type      |
      | Help text |
    When I set parameter 1 of "New custom workflow" to
      | Type | combo |
    Then parameter 1 of "New custom workflow" shows the fields
      | Name                                          |
      | Type                                          |
      | Default (empty = value in the workflow)       |
      | Options (comma separated; empty = from server) |
      | Filter (regex, case-insensitive)              |
      | Help text                                     |

  Scenario: A combo filter narrows the server's options
    When I expand "Upscale with model"
    And I set parameter 2 of "Upscale with model" to
      | Filter (regex, case-insensitive) | OmniSR |
    And I open the "Extras" tab
    Then "Upscale model" lists only
      | 4x_foolhardy_Remacri.pth    |
      | OmniSR_X2_DIV2K.safetensors |
      | OmniSR_X3_DIV2K.safetensors |
      | OmniSR_X4_DIV2K.safetensors |

  Scenario: Renaming a custom workflow keeps its Extras values
    Given the "Extras" tab is open
    When I set "Width" in Extras to "999"
    And I open the "Configuration" tab
    And I expand "Upscale with model"
    And I rename "Upscale with model" to "Upscaler"
    And I open the "Extras" tab
    Then "Workflow" shows "Upscaler"
    And "Width" shows "999"

  Scenario: A custom workflow is exported and imported on its own
    When I expand "Upscale with model"
    And I click "Export" in "Upscale with model"
    Then the downloaded file "ainvil-custom-upscale-with-model.json" has
      | path                        | value                  |
      | version                     | 1                      |
      | type                        | "customWorkflow"       |
      | workflow.name               | "Upscale with model"   |
      | workflow.parameters[0].type | "image"                |
      | workflow.parameters[7].default | "%date:yyyyMMdd%/upscale_%input%" |
    When I import the custom workflow file from the downloaded "ainvil-custom-upscale-with-model.json"
    Then the custom workflows are
      | name                   | status              |
      | Upscale with model     | 6 nodes · UI format |
      | Upscale with model (2) | 6 nodes · UI format |
    When I click "Duplicate" in "Upscale with model"
    Then the custom workflows are
      | name                    | status              |
      | Upscale with model      | 6 nodes · UI format |
      | Upscale with model copy | 6 nodes · UI format |
      | Upscale with model (2)  | 6 nodes · UI format |

  Scenario: A custom workflow file of the wrong kind is refused
    When I import a custom workflow file "fw.json" containing
      """
      {"version": 1, "type": "functionalWorkflow", "workflow": {"name": "X"}}
      """
    Then the custom workflow import error says "fw.json: this file is a \"functionalWorkflow\" export, expected \"customWorkflow\"."

  Scenario: Removing a parameter removes it from Extras
    When I expand "Upscale with model"
    And I remove parameter 8 of "Upscale with model"
    And I remove parameter 7 of "Upscale with model"
    And I open the "Extras" tab
    Then the Extras parameters are
      | Image                |
      | Upscale model        |
      | Model upscale only   |
      | Width                |
      | Height               |
      | Final resize method  |
