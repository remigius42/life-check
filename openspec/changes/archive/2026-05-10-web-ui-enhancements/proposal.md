<!-- spellchecker: ignore unpadded -->

## Why

The current "Beam Detector" web UI is basic and lacks essential features for a "Life Check" system. It missing branding (generic title), lacks context (no source link), has layout issues (unpadded container, full-width buttons), and provides no visibility into historical data. Additionally, there is no mechanism to manually reset the daily count if it was triggered incorrectly during maintenance or setup.

## What Changes

- **UI Branding**: Rename the application to "Life Check" across the web interface and page title.
- **Source Link**: Add a link to the GitHub repository (`https://www.github.com/remigius42/life-check`) in the footer.
- **Improved Layout**: Center and pad the web content using Pico CSS `.container` and ensure buttons use `width: auto` to prevent unnatural stretching.
- **History Display**: Add a section to the UI showing the last 14 days of break-beam events from the persisted history.
- **Count Reset**: Add a "Reset Today's Count" button to both the Raspberry Pi and ESP32 web interfaces that triggers an immediate reset of the daily counter.

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- `beam-detector-daemon`: Add requirement for handling a count reset sentinel file.
- `web-status-ui`: Update visual requirements (branding, layout) and add history and reset functional requirements.
- `esphome-firmware`: Add requirement for a manual count reset button.

## Impact

- `roles/detector/files/detector.py`: Updated to watch for and react to the reset sentinel.
- `roles/detector/files/web.py`: Comprehensive UI overhaul and new reset endpoint.
- `openspec/specs/`: Updated specifications for both daemon and web UI.
