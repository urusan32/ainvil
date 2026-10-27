Feature: Connecting to ComfyUI
  Ainvil talks to a ComfyUI server through its HTTP API. The address is set in Configuration › Connection,
  saved in the browser, and can be tested. Auto-Configure detects the server's optional features.

  Scenario: A first visit uses the default local address
    Given Ainvil is opened for the first time
    When I open the "Configuration" tab
    Then "ComfyUI API URL" shows "http://localhost:8188/"

  Scenario: Saving the address connects to the server
    Given Ainvil is opened for the first time
    And the "Configuration" tab is open
    When I set "ComfyUI API URL" to the test server address
    And I click "Save"
    Then the connection result says "Connected to ComfyUI"
    And the header shows the server version and host
    When I reload the page
    Then Ainvil connects to the server
    And "ComfyUI API URL" shows the test server address

  Scenario: An address without http:// still works
    Given Ainvil is opened for the first time
    And the "Configuration" tab is open
    When I set "ComfyUI API URL" to the test server address without "http://"
    And I click "Test Connection"
    Then the connection result says "Connected to ComfyUI"

  Scenario: An unreachable server explains what to check
    Given Ainvil is open and connected to the test server
    And the "Configuration" tab is open
    When I set "ComfyUI API URL" to "http://127.0.0.1:9/"
    And I click "Test Connection"
    Then the connection result is an error saying "Could not reach ComfyUI at http://127.0.0.1:9/"
    And the connection result is an error saying "--enable-cors-header"

  Scenario: The header shows the connection and opens the Configuration tab
    Given Ainvil is open and connected to the test server
    Then the header shows the server version and host
    When I click the connection status in the header
    Then the "Configuration" tab is shown

  Scenario: Auto-Configure detects CADS and live preview
    Given Ainvil is open and connected to the test server
    And the "Configuration" tab is open
    Then "CADS" is not checked
    And "Live preview" is not checked
    When I click "Auto-Configure"
    Then the connection result says "Auto-configured from"
    And the connection result says "CADS: available"
    And the connection result says "Live preview: available (auto)"
    And "CADS" is checked
    And "Live preview" is checked
    When I reload the page
    Then "CADS" is checked

  Scenario: "Use page origin" is only offered when the page is served over http(s)
    Given Ainvil is open and connected to the test server
    When I open the "Configuration" tab
    Then the "Use page origin" button is hidden

  Scenario: The last tab is remembered
    Given Ainvil is open and connected to the test server
    When I open the "Extras" tab
    And I reload the page
    Then the "Extras" tab is shown
    And the "Edit layout" button is hidden
