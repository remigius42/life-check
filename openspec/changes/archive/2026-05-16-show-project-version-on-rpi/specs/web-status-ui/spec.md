## MODIFIED Requirements

### Requirement: Status page branding and links
The web UI SHALL be titled "Life Check" in both the HTML `<title>` and the primary `<h1>` header. The page footer SHALL contain a link to the source repository (`https://www.github.com/remigius42/life-check`) and the deployed project version string read from the `DETECTOR_VERSION` environment variable (default `"unknown"`).

#### Scenario: Branding verified
- **WHEN** the status page is loaded
- **THEN** the title is "Life Check" and the GitHub link is present in the footer

#### Scenario: Version shown in footer
- **WHEN** the status page is loaded and `DETECTOR_VERSION` is set (e.g. `v2.2.1-3-g543b3e5`)
- **THEN** the footer displays the version string

#### Scenario: Version falls back to unknown
- **WHEN** the status page is loaded and `DETECTOR_VERSION` is not set
- **THEN** the footer displays `"unknown"`
