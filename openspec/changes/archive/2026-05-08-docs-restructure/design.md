## Context

The project root holds `DEVELOPMENT.md`, `NOTIFICATIONS.md`, and a 284-line
`README.md` that embeds full hardware reference content. No role READMEs link
to the moved files. The only spec path reference is in `github-actions-ci`.

## Goals / Non-Goals

**Goals:**

- Reduce README length by extracting hardware detail into `docs/`
- Move supplementary docs into `docs/` for a cleaner root
- Keep all links working after the move

**Non-Goals:**

- Rewriting or updating the content of moved files (content moves verbatim)
- Adding a docs site or any tooling around `docs/`

## Decisions

**Flat `docs/` with descriptive filenames** rather than nested subdirectories.
Four files don't need hierarchy; flat is easier to navigate and link to.

**README is a thin router** with no hardware prose. A deployment-routes
comparison table links to `docs/raspberry-pi.md` and `docs/esp32.md`.
Readers get enough context to choose a route without duplication.

**Delta spec only for `github-actions-ci`** — it is the only spec with a
literal file-path requirement (`DEVELOPMENT.md` SHALL contain…). Other specs
that mention "hardware" refer to physical hardware, not doc filenames.

**Route doc filenames are `docs/raspberry-pi.md` and `docs/esp32.md`** —
descriptive over generic (`hardware-*.md`). Flat `docs/` with four files
doesn't need the `hardware-` prefix for disambiguation.

## Risks / Trade-offs

External links to the raw GitHub URLs of `DEVELOPMENT.md` or
`NOTIFICATIONS.md` (e.g. from issues, external sites) will break after the
move. Risk is low — these are internal dev docs unlikely to be linked
externally.

## Migration Plan

1. Create `docs/` directory
2. Move files (`git mv`) to preserve history
3. Extract hardware sections from README into new `docs/hardware-*.md` files
4. Update README (replace extracted sections with summaries + links)
5. Update `openspec/specs/github-actions-ci/spec.md` via delta spec
6. Verify no broken links remain (`grep -r DEVELOPMENT\|NOTIFICATIONS .`)
