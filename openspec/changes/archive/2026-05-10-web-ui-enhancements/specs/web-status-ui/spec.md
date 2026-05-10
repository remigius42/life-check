## ADDED Requirements

### Requirement: Status page branding and links
The web UI SHALL be titled "Life Check" in both the HTML `<title>` and the primary `<h1>` header. The page footer SHALL contain a link to the source repository: `https://www.github.com/remigius42/life-check`.

#### Scenario: Branding verified
- **WHEN** the status page is loaded
- **THEN** the title is "Life Check" and the GitHub link is present in the footer

### Requirement: Improved layout, styling, and accessibility
The web UI SHALL use the Pico CSS `.container` class to provide centered, responsive layout with appropriate padding, remaining usable down to a 320px viewport width. All submit buttons SHALL be styled with `width: auto`.

The UI SHALL be accessible:
- All interactive elements (buttons, links) SHALL have descriptive text or ARIA labels.
- Visible focus states SHALL be maintained for keyboard navigation.
- The status indicator SHALL use both color and text (e.g., "🔴 BROKEN") to remain usable for color-blind users.

#### Scenario: Layout and accessibility verified
- **WHEN** the status page is viewed on mobile and desktop browsers
- **THEN** content is centered, buttons are not stretched, and keyboard navigation (Tab key) correctly highlights interactive elements

### Requirement: Status page shows historical data
The status page SHALL display up to the last 14 days of break-beam history as read from `counts.json`.
- Entries SHALL be sorted by date descending (newest first).
- Dates SHALL be formatted as "YYYY-MM-DD".
- History SHALL be rendered as a two-column table with headers "Date" and "Count".
- If `counts.json` is missing or malformed, the history section SHALL display "History unavailable" and the error SHALL be logged.
- If fewer than 14 days of data exist, only existing entries SHALL be shown (no synthesized data).

#### Scenario: History displayed correctly
- **WHEN** the status page is loaded and `counts.json` contains valid history
- **THEN** a table titled "History" shows recent daily totals in descending date order

### Requirement: Count reset via HTML form
The status page SHALL include a form with a "Reset Today's Count" button. When submitted, this form SHALL `POST /reset-count`. The server SHALL create the reset sentinel file and then respond with HTTP 303 See Other redirecting to `GET /`.

#### Scenario: Reset count button clicked
- **WHEN** the user clicks "Reset Today's Count"
- **THEN** `POST /reset-count` is called, the reset sentinel is created, and the page reloads

### Requirement: Testability of new UI elements
The new UI elements (History section, Reset button, GitHub link) SHALL be easily targetable by automated tests via stable HTML `id` attributes:
- The history section/table SHALL have `id="history"`.
- The reset button SHALL have `id="reset-count"`.
- The GitHub link SHALL have `id="github-link"`.

#### Scenario: Elements targetable by tests
- **WHEN** a test runner inspects the status page
- **THEN** it can find the history, reset, and github-link elements by their respective IDs
