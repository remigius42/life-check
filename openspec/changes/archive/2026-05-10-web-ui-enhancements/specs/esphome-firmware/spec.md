## ADDED Requirements

### Requirement: Manual count reset button
The firmware SHALL provide a manual mechanism to reset today's break count to zero. This SHALL be implemented as a `button` component in the ESPHome web interface. When pressed, the `today_count` global variable SHALL be immediately set to 0.

#### Scenario: Count reset triggered
- **WHEN** the "Reset Today's Count" button is pressed in the web UI
- **THEN** today's break count is set to 0
