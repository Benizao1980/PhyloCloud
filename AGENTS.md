# Agent instructions for PhyloCloud

This is an **engineering research-visualization project**, not a prompt to generate aesthetically plausible images.

Read these documents before major implementation:
1. `docs/SCIENTIFIC_INVARIANTS.md` — no topology/branch-length alteration.
2. `docs/DESIGN_SPEC.md` — intended native cloud appearance; concept illustrations are not scientific source.
3. `docs/ARCHITECTURE.md` — immutable scientific/layout contracts and ordered renderer.
4. `docs/ROADMAP.md` — sequencing and acceptance gates.
5. `docs/V02_LAYOUT_REVIEW.md` — actual v0.2 baseline, experimental spread is **not** true equal-daylight.

## Operating constraints

- Do not overwrite private GETcampy HPC/Box inputs or commit unpublished trees, sample metadata or the hand-drawn photograph.
- Do not infer new phylogeny or independently position a pruned MAG-only tree. Preserve every original tip, edge and branch length including zeros, selected edge set, and population sampling density.
- Optical cloud density is a **derived overlay** using actual reference tip/branch positions. It does not imply prevalence, inferred ancestry, confidence boundaries or monophyletic grouping.
- Keep branches and labels vector-editable where possible; disclose an embedded raster wash in hybrid SVG/PDF.
- Add regression tests for new scientific/layout features and side-by-side visual previews for style changes. Test nonmonophyletic groups, zero-length edges, sparse/outlier lineages and label collisions.
- Existing public `plot`/`demo` CLI and `publication`/`soft_cloud` presets must continue working during refactoring.
- Treat `cloud`, `cloud-hero`, `render` and new package directories in the design documents as **planned**, not implemented.
- Only declare a new algorithm (e.g. equal-daylight) implemented after validated independent comparison. Write truthful methods/captions.
- Save a new output path; record input hashes, configuration, density parameters, topology/edge validation and render method.
- Design target: gorgeous atmospheric, overlapping and soft colours **without inventing evolutionary structure**.
