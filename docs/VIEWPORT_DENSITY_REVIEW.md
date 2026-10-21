# Viewport-scale density review (synthetic, awaiting owner acceptance)

This is a focused follow-up stacked on draft #26, not a replacement for its
fixed-selection correction or the 6,500-tip structural benchmark. #24 and #25
merged into feature branches and have not reached main. No merge is authorized.

## Optical method and scientific contract

`cloud.zoom_bandwidth_mode: viewport` is opt-in for publication-composition,
multiscale Cloud/Canopy detail crops. The default `overview` still crops the
full-tree optical field. Ordinary overviews retain identical export bytes with
either setting. Existing plot/demo/publication/soft_cloud interfaces remain.

The new mode derives square histogram cells from the requested camera's longest
extent and configured resolution. Gaussian bandwidth remains in those cells.
A source halo extends at least six widest-kernel sigmas plus one cell beyond the
camera; an additional zero-padded halo protects convolution boundaries. Every
original reference tip and eligible original-edge sample is evaluated against
that domain. A sample outside finite kernel support contributes zero; this is
computational locality, not reference removal or tree pruning. The existing
kernel, reference/edge weights, colour tone curves and full-category counts are
retained. Memory allocation guards run before histogram/layer allocation.

**Normalization is local to the viewport plus its support halo.** Colour/alpha
cannot be compared quantitatively with the overview, or across differently
framed details. The caption discloses local wash normalization; provenance records
the exact camera, grids, physical bandwidth, source and contributing counts,
reference-membership hash, original edge IDs and coordinate hash. The wash is
optical, not prevalence, confidence, a clade boundary or inferred ancestry.

No topology, branch length (including zeros), node coordinate, connecting edge
or scientific foreground selection changes. All 12 focal genomes, 6,488
references, 12,996 original edges and 72 selected original edges remain. All
1,012 zero-length edges remain. Four coincident focal tips share the existing
explicit callout; markers are never jittered. Zoom reveals the nearby distinct
fifth marker at its true coordinate. Focus IDs affect labels/camera only.

## Individual readable comparisons

All files below show individual full-page figures, rather than tiny composites.
Before/after detail cameras and data-to-display transforms are identical.

- [Complete underlying tree, detail](../examples/viewport_density/detail_tree.jpg)
- [Cloud before](../examples/viewport_density/detail_cloud.jpg) and [Cloud after](../examples/viewport_density/viewport_cloud.jpg)
- [Canopy before](../examples/viewport_density/detail_canopy.jpg) and [Canopy after](../examples/viewport_density/viewport_canopy.jpg)
- [Actual 7.1 × 8 inch journal-size Cloud](../examples/viewport_density/journal-cloud.jpg)
- [Review provenance](../examples/viewport_density/review.json), [export checks](../examples/viewport_density/export_checks.json),
  [journal-size checks](../examples/viewport_density/journal-export-checks.json).

Complete-tree, Cloud and Canopy **overviews** are also exported by the review
script; existing committed overview comparisons remain in
[the structural benchmark](STRUCTURE_BENCHMARK.md). Each invocation generates the
same deterministic synthetic inputs (seed 650047), not a new inferred tree.
Original layout rotation is 19 degrees. No empirical input is accessed.

## Critical assessment

The previous wash filled nearly the entire crop with a broad coloured rectangle.
Viewport mode reveals two local reference fans and a sparse terminal continuation,
with white space between them. The exact dark focal connector remains readable.
Cloud is softer; Canopy retains stronger fine branch/tip texture. The local
optical bandwidth is approximately 4.3 times narrower in tree-coordinate units
(0.02526 versus 0.10860 widest sigma on this camera).

**Rectangular camera boundaries remain visible**, particularly where the top-right
cloud crosses the frame. They are intentional clipping of real sampled density,
not finite-raster truncation. No viewport fade or invented silhouette conceals
them. The diffuse, fan-shaped washes are still an optical summary: vector
complete-tree views remain necessary to judge fine local topology. This improves
the synthetic close-up but does not establish realistic empirical performance or
owner aesthetic acceptance. Species colours can recur in different parts of the
same tree and must not be read as monophyletic regions.

Measured annotation checks find no overlapping/clipped text at 12 × 11 inches or
7.1 × 8 inches, with minimum text 7.5 pt. Journal-size review retains the shared
coincident callout and readable focal connector. The narrow camera leaves side
space for callouts; stretching or separately repositioning tree components to fill
it is prohibited. Very dense local topology and coincident markers remain hard
to distinguish; smaller canvases or more labels may fail clearly rather than fit.

SVG contains editable text and all original/selected edge paths; PDF contains
embedded fonts, extractable labels and vector strokes. Cloud/Canopy washes are
embedded rasters in both formats. PNG uses a fixed 300 dpi canvas; all review
backgrounds are explicitly white. Per-file hashes and configuration are retained.

On this machine, full-page viewport preparation/export took 1.42/2.29 seconds
(Cloud) and 1.38/2.12 seconds (Canopy). The complete eight-figure review peaked
at 713.5 MiB RSS; the journal-size review peaked at 544.5 MiB.
Runtime and cumulative process peak RSS are recorded in `review.json`. RSS covers
the entire eight-figure review, including retained Matplotlib scenes, **not** an
isolated per-render benchmark. Timings are machine/environment observations, not
scaling guarantees. Configuration-dependent allocation guards do not guarantee a
fixed process memory bound. See the recorded values rather than extrapolating to
larger trees.

## Reproduce and verify

```sh
python scripts/review_viewport_density.py --outdir outputs/viewport_review_new
python scripts/review_viewport_density.py --journal --outdir outputs/viewport_journal_new
# Optional independent export QA dependency, separate from production requirements:
python -m pip install pypdf==6.20.1
python scripts/check_viewport_exports.py outputs/viewport_review_new
python scripts/check_viewport_exports.py outputs/viewport_journal_new
python -m pytest -q
```

Use fresh directories. Add `--tight` for an intentionally restrictive focal-only
camera; that is a sensitivity experiment, not an accepted default. Large
SVG/PDF/PNG and generated inputs remain ignored under outputs/. Only compact
full-page JPEG previews and small provenance/check summaries are committed.
The finite-support regression compares against an independently enlarged,
aligned grid, including a reference outside the camera. Other tests enforce
unchanged full membership, original coordinates/edges, default overview bytes,
matched cameras, allocation guards and clear unsupported-mode failures.

Next gate: [approved empirical input and visual review](EMPIRICAL_REVIEW_PROTOCOL.md).
