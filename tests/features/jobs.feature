@gpu
Feature: Generate jobs: skip, cancel and queueing
  Each press of Generate is a job with the settings of that moment. Jobs run one after another; Skip skips
  the image being generated and Cancel cancels the running job. Manage Jobs lists them.

  Background:
    Given Ainvil is open and connected to the test server
    And test outputs go to the "ainvil-test" folder
    And I fill in
      | Prompt | safe, a lighthouse on a cliff |
      | Width  | 512                           |
      | Height | 512                           |
      | Steps  | 30                            |
    And I uncheck "Random"
    And I set "Seed" in Generation Parameters to "2000"

  Scenario: Skip skips the image being generated and the job goes on
    When I fill in
      | Width       | 1024 |
      | Height      | 1024 |
      | Batch count | 3    |
    And I start generating
    And the first image is being generated
    And I click "Skip"
    And the generation finishes
    Then the status says "Done — 2 image(s), txt2img (1 skipped)."
    And the gallery images have the seeds 2001, 2002

  Scenario: Cancel cancels the whole running job
    When I fill in
      | Width       | 1024 |
      | Height      | 1024 |
      | Batch count | 3    |
    And I start generating
    And the first image is being generated
    And I click "Cancel" in Main
    And the generation finishes
    Then the status says "Cancelled."
    And the server has none of the job's prompts queued
    And the "Generate" button in Main is enabled
    And the "Skip" button is hidden

  Scenario: A second Generate press queues a job with the settings of that moment
    When I set "Batch count" to "2"
    And I start generating
    And I set "Prompt" to "safe, a sailboat at sea"
    And I set "Batch count" to "1"
    And I start generating again
    Then the Manage Jobs button says "Manage Jobs (2)"
    When I click "Manage Jobs (2)"
    Then the jobs dialog says "2 jobs"
    And the jobs dialog says "safe, a sailboat at sea"
    And the jobs dialog says "txt2img · Anima · models/anima/anima_baseV10.safetensors · 2 images · 512×512 · 30 steps · seeds 2000, 2001"
    And the jobs dialog lists
      | job | state   |
      | #1  | Running |
      | #2  | Queued  |
    When the generation finishes
    Then the status says "Job #2: Done — 1 image(s), txt2img."
    And the gallery images have the prompts
      | safe, a lighthouse on a cliff |
      | safe, a lighthouse on a cliff |
      | safe, a sailboat at sea       |
    And the jobs dialog says "No jobs are queued or running."
    And the Manage Jobs button says "Manage Jobs"

  Scenario: A queued job can be cancelled from Manage Jobs
    When I start generating
    And I set "Prompt" to "safe, a sailboat at sea"
    And I start generating again
    And I click "Manage Jobs (2)"
    And I cancel job "#2" in the jobs dialog
    Then the jobs dialog lists
      | job | state   |
      | #1  | Running |
    When the generation finishes
    Then the Output Gallery shows 1 image
    And the gallery images have the prompts
      | safe, a lighthouse on a cliff |

  Scenario: Cancel All Jobs cancels the running and the queued jobs
    When I fill in
      | Width       | 1024 |
      | Height      | 1024 |
      | Batch count | 2    |
    And I start generating
    And I start generating again
    And the first image is being generated
    And I click "Manage Jobs (2)"
    And I click "Cancel All Jobs"
    And the generation finishes
    Then the status says "Cancelled."
    And the server has none of the job's prompts queued
    When I press Escape
    Then the "Cancel All Jobs" button is hidden

  Scenario: Without multiple jobs, Generate waits for the running job
    Given the configuration has "clientPreferences.multipleJobs" set to false
    When I start generating
    Then the "Generate" button in Main is disabled
    And the "Manage Jobs" button is hidden
    When the generation finishes
    Then the "Generate" button in Main is enabled
    And the status says "Done — 1 image(s), txt2img."

  Scenario Outline: When the Output Gallery is cleared
    Given the configuration has "clientPreferences.galleryClear" set to "<clear>"
    When I fill in
      | Prompt | safe, a lighthouse on a cliff |
      | Width  | 256                           |
      | Height | 256                           |
      | Steps  | 4                             |
    And I generate
    And I generate
    Then the Output Gallery shows <images> images

    Examples:
      | clear    | images |
      | generate | 1      |
      | jobStart | 1      |
      | never    | 2      |

  Scenario: With "When each job starts", a queued job clears the previous job's images
    Given the configuration has "clientPreferences.galleryClear" set to "jobStart"
    When I fill in
      | Prompt | safe, a lighthouse on a cliff |
      | Width  | 256                           |
      | Height | 256                           |
      | Steps  | 4                             |
    And I start generating
    And I start generating again
    And the generation finishes
    Then the Output Gallery shows 1 image

  Scenario: Automatic clears can add the images to the Image Stash
    Given the configuration has "clientPreferences.autoStash" set to "auto"
    When I fill in
      | Prompt | safe, a lighthouse on a cliff |
      | Width  | 256                           |
      | Height | 256                           |
      | Steps  | 4                             |
    And I generate
    Then the Image Stash is empty
    When I generate
    Then a toast says "Added 1 image(s) from the Output Gallery to the Image Stash"
    And the Image Stash holds 1 image
    When I click "Clear" in the Output Gallery
    Then the Image Stash holds 1 image

  Scenario: Generate and Extras runs exclude each other
    When I start generating
    And I open the "Extras" tab
    And I click "Run" in Extras
    Then the Extras status is an error saying "A Generate run is in progress; wait for it or cancel it first."
    When the generation finishes
