# Changelog

## [Unreleased] — proposed architecture and design direction (2026-10-12)

- Specify native, **data-derived** coloured density clouds and editorial-quality figure modes in `docs/DESIGN_SPEC.md`.
- Plan immutable scientific tree / layout geometry, cloud engine, scene layers, semantic annotation and export separation in `docs/ARCHITECTURE.md`.
- Record staged architecture/cloud/labels/panels/validation/release milestones in `docs/ROADMAP.md`.
- Clarify that existing generated illustration concepts are design references, not scientifically faithful software outputs.
- No new rendering functionality is claimed for this documentation update.

## [0.2.0a0] — 2026-10-12 (pre-release prototype)

- `publication` and `soft_cloud` presets, experimental phylogenetic-spread angles.
- Full-tree-coordinate geometric crop/zoom with selected-neighbour markers and optional scale bar.
- Neutral sampled-reference tip-density underlay (hybrid SVG/PDF); original edges stay vector editable.
- SHA-256 provenance, original edge-retention validation and tests.
- Applied locally to the 6,445-tip GETcampy tree for review; private source data not committed.

## [0.1.0a0] — 2026-10-12

- Newick/metadata/selected-tip command-line interface.
- One unrooted equal-arc coordinate system for all original edges.
- Exact minimal connecting subtree for focal genomes.
- Two-pass semitransparent backgrounds; optional species colours using Ben-style palette.
- Labelled focal genome markers; vector SVG/PDF and high-resolution PNG.
- Synthetic demo generator, CI and draft-release workflow.

Public releases require scientific validation and code review.
