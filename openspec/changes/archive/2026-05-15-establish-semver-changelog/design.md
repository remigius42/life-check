## Context

No versioning or changelog exists. HEAD (tagged `initial`) represents a stable, deployed state for both routes. The next change (substitutions-config-refactor) is breaking for ESP32 deployers, so a baseline version must be established first.

## Goals / Non-Goals

**Goals:**
- Establish semver as the versioning scheme
- Document current state as 1.0.0 in a keepachangelog-compliant CHANGELOG.md
- Tag HEAD as `v1.0.0`

**Non-Goals:**
- Backfilling per-commit history into the changelog (1.0.0 is a summary, not a log)
- Setting up automated release tooling

## Decisions

**Semver over calendar versioning**: MAJOR.MINOR.PATCH directly encodes the nature of a change. Breaking changes → MAJOR bump is an immediately legible signal. Calendar versioning would require day-level granularity given commit frequency, producing unwieldy identifiers with no semantic meaning.

**1.0.0 as baseline, not 0.x**: Both routes are deployed and functional. `0.x` implies pre-release instability; `1.0.0` correctly reflects the current state.

**Single CHANGELOG.md at repo root**: Both routes live in the same repo; a single file is simpler. Route-specific breaking changes are noted inline (e.g., "ESP32 only").

**keepachangelog 1.1.0 format**: Widely recognized, human-readable, tooling-friendly. Sections: Added, Changed, Deprecated, Removed, Fixed, Security. Breaking changes noted with **BREAKING** marker under Changed.

## Risks / Trade-offs

- **1.0.0 summary is lossy** — individual features aren't attributed to commits. Acceptable: git log preserves that history; the changelog is for deployers, not archaeologists.
