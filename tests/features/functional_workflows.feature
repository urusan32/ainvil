Feature: Configuring functional workflows
  A functional workflow has a ComfyUI workflow per mode (txt2img, img2img, inpainting) and mappings from the
  Generate tab's parameters to node inputs. Workflows load from UI- or API-format JSON or from a ComfyUI PNG,
  and "Auto-detect mappings" makes a first guess.

  Background:
    Given Ainvil is open and connected to the test server
    And test outputs go to the "ainvil-test" folder
    And the "Configuration" tab is open

  Scenario: The built-in functional workflows are Anima and MOSS
    Then the functional workflows are
      | name  | modes                         |
      | Anima | txt2img · img2img · inpainting |
      | MOSS  | txt2img · img2img · inpainting |
    And "Anima" is expanded
    And "txt2img of Anima" says "11 nodes · UI format · 15 mapped"
    And "img2img of Anima" says "13 nodes · UI format · 18 mapped"
    And "inpainting of Anima" says "13 nodes · UI format · 19 mapped"

  Scenario: Loading a UI workflow into a new functional workflow detects its mappings
    When I click "+ New functional workflow"
    Then the functional workflows are
      | name         | modes                          |
      | Anima        | txt2img · img2img · inpainting |
      | MOSS         | txt2img · img2img · inpainting |
      | New workflow | no workflows                   |
    When I expand "txt2img of New workflow"
    And I load the workflow file "txt2img-minworkflow-cads.json" into "txt2img of New workflow"
    Then a toast says "Loaded txt2img-minworkflow-cads.json"
    And "txt2img of New workflow" says "11 nodes · UI format · 15 mapped"
    And the txt2img mappings of "New workflow" are
      | parameter    | targets          |
      | seed         | 19.seed          |
      | steps        | 19.steps         |
      | cfg          | 19.cfg           |
      | sampler_name | 19.sampler_name  |
      | scheduler    | 19.scheduler     |
      | denoise      | 19.denoise       |
      | prompt       | 11.text          |
      | negative     | 12.text          |
      | model        | 44.unet_name     |
      | lora         | 49               |
      | cads         | 63               |
      | output       | 46               |
      | width        | 28.width         |
      | height       | 28.height        |
      | batch_size   | 28.batch_size    |

  Scenario: Auto-detect finds the image, resize and inpainting inputs
    When I click "+ New functional workflow"
    And I expand "inpainting of New workflow"
    And I load the workflow file "inpainting-minworkflow.json" into "inpainting of New workflow"
    Then the inpainting mappings of "New workflow" are
      | parameter    | targets          |
      | seed         | 19.seed          |
      | steps        | 19.steps         |
      | cfg          | 19.cfg           |
      | sampler_name | 19.sampler_name  |
      | scheduler    | 19.scheduler     |
      | denoise      | 19.denoise       |
      | prompt       | 11.text          |
      | negative     | 12.text          |
      | model        | 44.unet_name     |
      | lora         | 49               |
      | output       | 46               |
      | image        | 51.image         |
      | width        | 53.width         |
      | height       | 53.height        |
      | crop         | 53.crop          |
      | resize       | 53               |
      | noise_mask   | 60.noise_mask    |
      | batch_repeat | 19.latent_image  |

  Scenario: An API-format workflow and a workflow inside a ComfyUI PNG both load
    When I click "+ New functional workflow"
    And I expand "txt2img of New workflow"
    And I load the workflow file "txt2img-api.json" into "txt2img of New workflow"
    Then "txt2img of New workflow" says "10 nodes · API format"
    When I expand "img2img of New workflow"
    And I load a PNG with an embedded copy of "img2img-minworkflow.json" into "img2img of New workflow"
    Then "img2img of New workflow" says "12 nodes · UI format"

  Scenario: Files that aren't workflows are refused with a reason
    When I click "+ New functional workflow"
    And I expand "txt2img of New workflow"
    And I load a PNG without a workflow into "txt2img of New workflow"
    Then "txt2img of New workflow" shows the error "This PNG has no embedded ComfyUI workflow."
    When I load a file "notes.json" into "txt2img of New workflow" containing
      """
      {"hello": "world"}
      """
    Then "txt2img of New workflow" shows the error "notes.json: not a ComfyUI workflow"
    When I load a file "broken.json" into "txt2img of New workflow" containing
      """
      {"nodes": [
      """
    Then "txt2img of New workflow" shows the error "broken.json: invalid JSON"

  Scenario: Workflows with subgraphs are not supported
    When I click "+ New functional workflow"
    And I expand "txt2img of New workflow"
    And I load the workflow file "subgraph-workflow.json" into "txt2img of New workflow"
    Then "txt2img of New workflow" shows the error "Workflows containing subgraphs are not supported; unpack them in ComfyUI first."

  Scenario: Reroutes, primitives, muted, bypassed and note nodes convert like ComfyUI does
    When I click "+ New functional workflow"
    And I expand "txt2img of New workflow"
    And I load the workflow file "txt2img-frontend-nodes.json" into "txt2img of New workflow"
    Then "txt2img of New workflow" says "9 nodes · UI format"
    When I open the "Generate" tab
    And I select "New workflow" as "Functional Workflow"
    And I set "Prompt" to "safe, a cat"
    And I download the workflow
    Then the workflow node 46 "images" is linked to node 8
    And the workflow sets node 19 "steps" to 7
    And the workflow node 19 "model" is linked to node 44
    And the workflow has no node 49
    And the workflow has no node 70
    And the workflow has no node 72
    And the workflow has no node 73
    And the workflow has no node 74

  Scenario: Renaming a functional workflow keeps it selected on the Generate tab
    When I rename "Anima" to "Anima Prime"
    Then the functional workflows are
      | name        | modes                          |
      | Anima Prime | txt2img · img2img · inpainting |
      | MOSS        | txt2img · img2img · inpainting |
    When I open the "Generate" tab
    Then "Functional Workflow" shows "Anima Prime"
    And the custom parameters are
      | Filename prefix |

  Scenario: Duplicate, move up and delete
    When I click "Duplicate" in "Anima"
    Then the functional workflows are
      | name       | modes                          |
      | Anima      | txt2img · img2img · inpainting |
      | Anima copy | txt2img · img2img · inpainting |
      | MOSS       | txt2img · img2img · inpainting |
    When I expand "MOSS"
    And I click "Move up" in "MOSS"
    Then the functional workflows are
      | name       | modes                          |
      | Anima      | txt2img · img2img · inpainting |
      | MOSS       | txt2img · img2img · inpainting |
      | Anima copy | txt2img · img2img · inpainting |
    When I expand "Anima copy"
    And I click "Delete" in "Anima copy"
    Then I was asked "Delete functional workflow \"Anima copy\"?"
    And the functional workflows are
      | name  | modes                          |
      | Anima | txt2img · img2img · inpainting |
      | MOSS  | txt2img · img2img · inpainting |

  Scenario: A functional workflow is exported and imported on its own
    When I click "Export" in "Anima"
    Then a file named "ainvil-functional-anima.json" is downloaded
    And the downloaded file "ainvil-functional-anima.json" has
      | path                          | value                |
      | version                       | 1                    |
      | type                          | "functionalWorkflow" |
      | workflow.name                 | "Anima"              |
      | workflow.modelFilter          | "anima"              |
      | workflow.customParameters[0].name | "Filename prefix" |
    When I import the functional workflow file from the downloaded "ainvil-functional-anima.json"
    Then a toast says "Imported fw.json"
    And the functional workflows are
      | name      | modes                          |
      | Anima     | txt2img · img2img · inpainting |
      | MOSS      | txt2img · img2img · inpainting |
      | Anima (2) | txt2img · img2img · inpainting |

  Scenario Outline: A wrong single-workflow file is refused
    When I import a functional workflow file "<file>" containing
      """
      <content>
      """
    Then the functional workflow import error says "<error>"

    Examples:
      | file     | content                                                   | error                                                         |
      | cw.json  | {"version": 1, "type": "customWorkflow", "workflow": {}}  | cw.json: this file is a \"customWorkflow\" export, expected \"functionalWorkflow\". |
      | nowf.json | {"version": 1, "type": "functionalWorkflow"}             | nowf.json: missing \"workflow\" object.                         |
      | v0.json  | {"version": 0, "workflow": {}}                            | v0.json: unsupported version 0                                |

  Scenario: The model filter narrows the model list
    When I set "Model filter (regex, case-insensitive)" in "Anima" to "anima_(base|aesthetic)"
    And I open the "Generate" tab
    Then the model list is
      | models/anima/anima_aestheticV11.safetensors |
      | models/anima/anima_baseV10.safetensors      |

  Scenario: The LoRA filter narrows the LoRA lists
    When I set "LoRA filter (regex, case-insensitive)" in "Anima" to "galena"
    And I open the "Generate" tab
    And I add a LoRA
    Then the LoRA list is
      | on/off | name                    | weight |
      | On     | galena-AB10-01.safetensors | 1   |

  Scenario: Editing a mapping changes what the Generate tab sets
    When I expand "txt2img of Anima"
    Then the "Seed" mapping in "txt2img of Anima" shows "#19 KSampler / seed"
    When I remove the "Seed" mapping target in "txt2img of Anima"
    And I map "Seed" in "txt2img of Anima" to node "63" input "seed"
    Then the "Seed" mapping in "txt2img of Anima" shows "#63 CADS / seed"
    And "txt2img of Anima" says "15 mapped"
    When I open the "Generate" tab
    And I set "Prompt" to "safe, a cat"
    And I uncheck "Random"
    And I set "Seed" in Generation Parameters to "777"
    And I download the workflow
    Then the workflow sets node 19 "seed" to 1049125633936695

  Scenario: A mapping that points at a missing node is reported when generating
    Given the configuration has "functionalWorkflows.0.workflows.txt2img.mappings.seed" set to [{"node": "999", "input": "seed"}]
    When I expand "txt2img of Anima"
    Then the "Seed" mapping in "txt2img of Anima" shows "#999 (not in workflow) / seed (?)"
    When I open the "Generate" tab
    And I set "Prompt" to "safe, a cat"
    And I click "Generate Workflow"
    Then the status is an error saying "Mapping \"seed\" for txt2img points at node #999, which is not in the workflow."

  Scenario: A mode without a workflow can't be generated
    When I click "+ New functional workflow"
    And I open the "Generate" tab
    And I select "New workflow" as "Functional Workflow"
    And I click "Generate Workflow"
    Then the status is an error saying "\"New workflow\" has no txt2img workflow configured."
    And the CADS section says "CADS is not configured for this workflow (no CADS node mapped), so it is off."
    And the LoRA section says "This workflow has no LoRA template node mapped, so LoRAs are ignored."

  Scenario: A custom parameter maps a value onto a node input
    When I expand "Custom parameters of Anima"
    And I click "+ Add custom parameter" in "Anima"
    And I set parameter 2 of "Custom parameters of Anima" to
      | Name    | Sampler steps |
      | Type    | int           |
      | Default | 7             |
    And I map parameter 2 of "Custom parameters of Anima" for txt2img to node "19" input "steps"
    And I open the "Generate" tab
    Then the custom parameters are
      | Filename prefix |
      | Sampler steps   |
    And "Sampler steps" shows "7"
    When I set "Prompt" to "safe, a cat"
    And I set "Sampler steps" to "11"
    And I download the workflow
    Then the workflow sets node 19 "steps" to 11

  Scenario: Custom parameter types show the matching fields
    When I expand "Custom parameters of Anima"
    Then parameter 1 of "Custom parameters of Anima" shows the fields
      | Name    |
      | Type    |
      | Default |
    When I set parameter 1 of "Custom parameters of Anima" to
      | Type | combo |
    Then parameter 1 of "Custom parameters of Anima" shows the fields
      | Name                                       |
      | Type                                       |
      | Default                                    |
      | Options (comma separated; empty = from server) |
    When I set parameter 1 of "Custom parameters of Anima" to
      | Type | float |
    Then parameter 1 of "Custom parameters of Anima" shows the fields
      | Name    |
      | Type    |
      | Default |
      | min     |
      | max     |
      | step    |

  Scenario: A combo custom parameter offers its options on the Generate tab
    When I expand "Custom parameters of Anima"
    And I set parameter 1 of "Custom parameters of Anima" to
      | Type                                       | combo                          |
      | Options (comma separated; empty = from server) | ainvil-test/e2e/a, ainvil-test/e2e/b |
    And I open the "Generate" tab
    Then "Filename prefix" lists "ainvil-test/e2e/a"
    And "Filename prefix" lists "ainvil-test/e2e/b"
    When I select "ainvil-test/e2e/b" as "Filename prefix"
    And I set "Prompt" to "safe, a cat"
    And I download the workflow
    Then the workflow sets node 46 "filename_prefix" to "ainvil-test/e2e/b"

  Scenario: Removing a custom parameter removes it from the Generate tab
    When I expand "Custom parameters of MOSS"
    And I expand "MOSS"
    And I remove parameter 1 of "Custom parameters of MOSS"
    And I open the "Generate" tab
    And I select "MOSS" as "Functional Workflow"
    Then the custom parameters are
      | Skip layer guidance |
      | SLG single layers   |
      | SLG double layers   |
      | SLG start percent   |
      | SLG end percent     |
