# PhyloCloud roadmap — from v0.2 to beautiful, defensible native clouds

**North star:** reproduce the stronger cloud-style visual direction **from the original Newick data**, rather than publishing a generated illustration that only resembles a phylogeny. Read [DESIGN_SPEC.md](DESIGN_SPEC.md) and [ARCHITECTURE.md](ARCHITECTURE.md) before developing features.

## Current baseline — v0.2 (merged, not a polished release)

- [x] Standalone public GitHub repository, installable package, CLI (`plot`, `demo`), synthetic example and CI.
- [x] Full-tree original-edge render and exact original-edge selected connecting subtree.
- [x] `publication` and `soft_cloud` existing presets, experimental phylogenetic-spread angles.
- [x] Neutral density haze from **reference-tip** coordinates; SVG/PDF vector tree with optional raster underlay.
- [x] Geometric magnification without second tree layout, nearest-context tip markers, provenance JSON.
- [x] Local validation with archived GETcampy FastTree: **6,436 references + nine MAGs**; source remains private.
- [ ] A native, visually striking *coloured* reference-density cloud matching the design target.
- [ ] Cloud labels, collision engine, proven equal-daylight comparison, and full architecture split.

The remaining items are **planned**, not current features. No generated concept-art illustration is used as a validated phylogenetic figure.

## Phase 1 — refactor without scientific regression (priority: immediate)

Deliver:
- [ ] Immutable scientific tree/edge/selection APIs with stable IDs.
- [ ] LayoutMap and RenderScene/RenderLayer interfaces (same XY map for both layers).
- [ ] Matplotlib backend and compatibility adapters preserving current `plot`/`demo` behaviour.
- [ ] Config schema validation, a stable style registry and provenance model independent of rendering.
- [ ] Unit/integration checks: all edges, unrooted splits, patristic lengths, 0-length branches, benchmark fixture.

**Acceptance:** current v0.2 figure and report can be regenerated from the refactored code, with no new biological differences; equivalent inputs give the same scientific geometry; CI green.

## Phase 2 — true native density-cloud renderer (highest visual priority)

Deliver:
- [ ] Vector reference tip points with exact original XY; optional line-segment samples from actual edges.
- [ ] Deterministic Gaussian-splat/KDE-like layer with configuration for bandwidth, weights, opacity, alpha curve, raster resolution.
- [ ] Separate metadata-coloured fields, **default grouped by species**, with configurable arbitrary metadata column and exact palette/value mapping; transparent blending and neutral fallback for unassigned/mixed groups.
- [ ] Document sampled-tip versus sampled-branch density and **sampling bias**; no interpretation as natural prevalence.
- [ ] Pure-vector `points` / `branches+points` and hybrid `density-wash` / `hybrid` modes.
- [ ] Three style presets: `publication`, `cloud`, `cloud-hero`; retain `soft_cloud` as backward-compatible legacy alias.
- [ ] Aesthetic review of two distinct fields (synthetic non-monophyletic fixture and real GETcampy), with the concept-art target shown strictly as a *style reference*.

**Acceptance:** the cloud appearance is convincingly stronger than v0.2 while every branch, genome coordinate, source count and selected edge remains identical within numerical tolerance; no false boundaries or artificial new tips; high DPI and PDF/SVG are validated.

## Phase 3 — semantic cloud and selected-genome labels

Deliver:
- [ ] Broad cloud labels default to the **same metadata column as cloud colour** (`group_by: species`, `label_by: same`); support custom group/label columns and explicit none/species/lineage modes.
- [ ] Compute anchors from actual selected group XY and density maxima/medoids.
- [ ] Split visibly disconnected components for nonmonophyletic groups; use repeated labels or legend instead of a misleading one-cloud species boundary.
- [ ] Deterministic placement and collision avoidance for direct MAG labels, cloud labels, annotation leaders and legend.
- [ ] Readable overlays in `publication`, `cloud` and `cloud-hero`, with font availability/fallback audit.

**Acceptance:** zero clipped labels and tolerably low collision rates in both full GETcampy and the six closely co-located C. infans MAGs, with all sample labels mapped to the true genome IDs.

## Phase 4 — neighbourhoods and multi-panel composition

Deliver:
- [ ] Configurable *true geometric* zoom panel (already present as a single-plot option; generalise composition).
- [ ] Optional nearest-tree-reference annotations with explicit patristic distance; optional verified ANI data displayed separately.
- [ ] Optional selected-MAG counts by species, lineage and source; optional group statistics.
- [ ] Reproducible 1/2-column figure templates and manuscript/slide/hero canvas sizes.

**Acceptance:** panel geometry reuses full-tree XY; coordinate bounds/crop manifest recorded; labels remain accurate at final target print size.

## Phase 5 — validation and scientific review

Deliver:
- [ ] Real GTDB R226 input tests with documented input hashes and exact tip/reference/MAG counts.
- [ ] Full topology, edge, path and zero-length audits across alternate layouts and all three visual styles.
- [ ] Compare equal-arc, current experimental phylogenetic-spread, and a verified true equal-daylight implementation; avoid incorrect algorithm naming.
- [ ] Re-run on other pathogen MAG data (e.g. E. coli) and mixed/nonmonophyletic categories.
- [ ] Benchmark >25k and 50k tips; evaluate memory/time without using pairwise N² matrices.
- [ ] Accessibility, grayscale, editable text/vector checks; note raster cloud underlays explicitly.
- [ ] Double-check nearest references against tree path lengths and never equate them to ANI.

**Acceptance:** full provenance and methods narrative suitable for a manuscript, including limitations caused by reference sampling and overplotted zero-length edges.

## Phase 6 — open-source pre-release

Deliver:
- [ ] CLI reference docs, example YAML and generated synthetic demo with expected figures.
- [ ] Release notes/migration from old `plot` and `soft_cloud` naming.
- [ ] CI, benchmark smoke test, packaging, licence/citation, cross-platform install instructions.
- [ ] Versioned tagged **pre-release** with tested SVG/PDF/PNG outputs and source.
- [ ] Optional online gallery showing real biological data **only with permission**.

**Acceptance:** new user can recreate synthetic `publication`, `cloud`, `cloud-hero` figures without private data, all tests green, GitHub release explicitly distinguishes synthetic demonstrations from biological results.

## Implementation priorities and constraints

1. **Build a minimal RenderScene first**, then immediately implement the **real cloud engine**. Do not spend weeks reorganising modules without improving the result.
2. Every aesthetic change must be paired with a scientific-fidelity test or explicit no-op claim for XY geometry.
3. Images generated outside the phylogenetic renderer are permitted as *visual design references only*, never as data-preserving final scientific figures.
4. Keep data provenance and core maths independent of font, SVG, PDF or image-output backend.
5. Default to no public commitment of the user's unpublished GETcampy Newick/metadata.

## Implementation issues (created)

These issues are ready to use; each should be implemented in a separate reviewed pull request:

- [#5 — Immutable tree/layout and RenderScene refactor](https://github.com/Benizao1980/PhyloCloud/issues/5) — Phase 1.
- [#6 — Native density-based coloured cloud and styles](https://github.com/Benizao1980/PhyloCloud/issues/6) — Phase 2, highest visual priority.
- [#7 — Semantic cloud labels and collision handling](https://github.com/Benizao1980/PhyloCloud/issues/7) — Phase 3.
- [#8 — True-tree zooms and analytical multi-panels](https://github.com/Benizao1980/PhyloCloud/issues/8) — Phase 4.
- [#9 — Independent equal-daylight implementation/validation](https://github.com/Benizao1980/PhyloCloud/issues/9) — Phase 5 layout evaluation.
- [#10 — Export, provenance, scientific QA](https://github.com/Benizao1980/PhyloCloud/issues/10) — Phase 5 validation.
- [#11 — Reproducible versioned pre-release](https://github.com/Benizao1980/PhyloCloud/issues/11) — Phase 6.

Each implementation PR should reference its issue, include at least one scientific invariant test, and provide a before/after visual preview plus scientific-validation output. These are planned engineering tasks, not features already implemented.
