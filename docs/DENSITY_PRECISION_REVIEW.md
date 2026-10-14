# Density precision audit — 2026-10-14

Scope: public code and deterministic synthetic data only. No private data,
HPC access or biological inference. Baseline: `cc5beb4`.

## Audit and improvement

The current v0.3 alpha implements `plot`/`demo`, Cloud/Canopy multiscale washes,
prototype Constellation/River, original-length and explicit non-metric modes,
and optional geometric panels. Architecture/design/roadmap documents describe
an older v0.2 baseline and a future architecture; they are not an inventory of
the current implementation. Immutable scene interfaces and true independently
validated equal-daylight remain planned.

`soft_cloud` converted log-count histograms to uint8 before Pillow blur.
That quantized weak tails into terraces and could erase sparse haze. It now
uses the existing padded float FFT Gaussian, retaining log-count compression,
the same tip samples, grid, bandwidth, opacity and alpha exponent.

Native multiscale Cloud/Canopy used hard density and alpha cutoffs. Nonlinear
alpha amplification turned these into visible silhouettes. Both thresholds now
use a cubic smoothstep taper: `v * t² * (3 - 2t)`, where
`t = clip(v / threshold, 0, 1)`. Full strength is retained above the threshold;
weak tails fade continuously. No points, edges, lengths or selections change.

Provenance now identifies the float kernel and hybrid vector/raster method.
Legacy wash parameters include bounds, reference-tip source, unit sample
weight, log compression, resolution, bandwidth, opacity and alpha exponent.
Native parameters retain their existing reporting; a complete source/weight/
compositing manifest remains outstanding (#10).

## Reproducible visual review

Run from the repository root in an environment with the project installed:

```sh
python scripts/density_review.py
python -m pytest -q
```

The script loads the committed baseline renderer and creates identical
900-reference + nine-selected synthetic inputs (seed 47), original lengths,
matched configuration and before/after SVG/PDF/PNG. It checks equal input
hashes, edge/reference counts and length validation, and records output hashes.
Exports are in `examples/outputs/density_review/`; comparisons are
`cloud_comparison.jpg` and `soft_cloud_comparison.jpg`.

Cloud review shows noticeably softer coloured boundaries, with the original
reference filaments and dark foreground still visible. The legacy improvement
is subtler at overview size. The fixture's six synthetic groups are illustrative,
not evidence of real species monophyly. The wash is sampling-density styling,
not prevalence, confidence, ancestry or a taxonomic boundary.

## Remaining limitations and issue audit

- #6: the finite raster extent can still crop broad Gaussian tails; bandwidth
  remains pixel-based and varies in data units with resolution. No density
  field should be mistaken for a biological boundary. Atmospheric visual
  acceptance remains open.
- #7/#19: broad labels can touch selected markers/leaders; the placement
  heuristic does not measure text boxes or split nonmonophyletic categories.
  Long focal labels and caption/legend spacing need print-size review.
- #8/#19: optional automatic species panels are PNG; standalone vector panel
  exports and coherent publication composition remain outstanding. Cropping
  reuses full-tree geometry, but automatic clipping QA is absent.
- #10: export timestamps and SVG IDs are controlled; regression checks compare
  repeated PNG/SVG/PDF bytes in one environment. Cross-version fonts/renderers
  are not guaranteed byte-identical. Complete dependency/output manifests and
  large-tree benchmarks remain open.
- #5/#9/#11: immutable architecture, independent equal-daylight comparison
  and documented prerelease quality gates remain open.

Scientific review is required before changing density sample weights, layout
algorithms or interpreting metadata groups as clades. This patch changes only
optical numerical precision/tapering and needs human visual acceptance.
