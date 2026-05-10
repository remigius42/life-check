## ADDED Requirements

### Requirement: Count reset via sentinel file
The daemon SHALL support resetting today's break count to zero. A reset is triggered when a regular file exists at `/run/beam_detector/reset_count` (configurable via `detector_reset_count_sentinel`).

Upon detection of the sentinel, the daemon SHALL:
1. Reset `today_count` to 0.
2. Log the reset event with a timestamp.
3. Attempt to delete the sentinel file.

The daemon SHALL NOT perform another reset until the sentinel file has been successfully deleted. If deletion fails, the daemon SHALL log an error and retry the deletion on every subsequent polling iteration until it succeeds. The daemon SHALL ignore any beam-break events that occur in the same polling iteration that performs the reset.

#### Scenario: Count reset triggered and cleaned up
- **WHEN** a regular file at the reset sentinel path is detected during a polling iteration
- **THEN** today's count is set to 0, a log entry is created, and the sentinel file is deleted within one poll interval
