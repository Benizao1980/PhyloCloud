# Changelog

- Extend reference-cloud raster support without changing histogram sampling or
  scientific geometry; include visible wash in overview framing while preserving
  explicit selected-tip crops. Add synthetic boundary/vector export regressions,
  raster and output-hash provenance, and a compact [before/after review](docs/RASTER_BOUNDARY_REVIEW.md).

- Remove 8-bit blur quantization in `soft_cloud`; taper native Cloud/Canopy
  density tails continuously instead of hard contour cutoffs. Add synthetic
  before/after exports, density precision tests and hybrid-wash provenance.

## [0.3.0a0] — native Cloud/Canopy development

- Added native `cloud` and `canopy` species-coloured reference-density styles and simple broad semantic labels.
- Added experimental `constellation` and `river` motifs; all use one original inferred tree, unchanged tip/edge coordinates and selected-edge set.
- Added `--style` and `--cloud-group-by` CLI flags, retained v0.2 `plot`, `demo`, `publication`, `soft_cloud` compatibility.
- Bounded native raster group layers for performance while recording all original species counts and references.
- Added synthetic style previews, public-facing quick start, usage guide, examples and scientific regression tests.
- Not yet a publication-ready automatically collision-free label engine or a full-tree + geometric-neighbourhood composite.

## [Unreleased]

- Added `--length-mode original|graphic`; original-length phylograms are default, graphical spacing is explicitly non-metric, original tree data remain unchanged and mode-specific provenance tests distinguish the two.

- Equal-daylight algorithm benchmarking, line-crossing diagnostics and neighbourhood panels remain future work.

## [0.2.0a0] — 2026-10-12 (pre-release candidate)

- Two presets (`publication`, `soft_cloud`) with different opacity/color treatment, using the same full-tree coordinates within each figure.
- Experimental `phylogenetic_spread` angular-sector weighting (not classical equal-daylight); unchanged original inferred edge lengths.
- Optional display-only blurred reference-tip sampling-density underlay, with SVG/PDF edges and labels retained as vectors.
- True geometric crops of the original full layout; optional original-tree context reference markers and branch-length scale bar.
- Automated SHA-256 provenance JSON and explicit source-tip/edge preservation tests; 13 new and old tests expected in CI.
- Guard against treating unselected MAGs as reference genomes when deriving legend/reference-density counts.
- Public synthetic demonstrations and real-tree local comparison documented; private Box source data not committed.

## [0.1.0a0] — 2026-10-12

- Initial unrooted equal-arc CLI, reference background and selected original-edge subtree.
- Ben-style palette, SVG/PDF/PNG export, generated synthetic example, baseline tests, CI and draft releases.

## Unreleased — public examples and geometric neighbourhood comparison

- Optional `--detail-selected` subset creates a second full-tree-coordinate crop with separate SVG/PDF/PNG plus a labelled overview-detail PNG contact sheet.
- Refined selected-tip leaders and broad label avoidance of highlighted original branches; figure coordinates are never shifted for styling.
- Added fully synthetic, non-Campylobacter (E. coli lineage) input files, and tested example outputs; no private GETcampy data committed.
- Added practical reference-genome / tree acquisition guide, GTDB release-version warning and explicit Kraken2 classification-vs-phylogeny explanation.
- Made the README task-oriented with reference links, reproducible secondary use case and preview gallery.

## CLI entry-point hotfix

- The installed `phylocloud` command now returns exit status 0 after a successful plot/demo; the programmatic `main()` still returns the summary dictionary. This fixes the public gallery workflow and ensures shell scripts can use `set -e`.
- Added a regression test for the console entry point.
