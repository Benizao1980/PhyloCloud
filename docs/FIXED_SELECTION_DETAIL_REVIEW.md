# Detail views preserve the complete focal selection

`--detail-selected` now selects **which focal IDs to frame and label**, not a
new highlighted subtree. Every detail uses the same original graph, node
coordinates, reference sampling and selected connecting edges as its overview.
Edges outside the viewport remain in the scene and are geometrically clipped.
This deliberately corrects the previous behaviour, which recalculated the
foreground from only the detail subset.

Full-page review images: [previous subset behaviour](../examples/structure_benchmark/detail-before.jpg),
[complete-tree detail](../examples/structure_benchmark/detail-tree.jpg),
[Cloud](../examples/structure_benchmark/detail-cloud.jpg) and
[Canopy](../examples/structure_benchmark/detail-canopy.jpg).
[Scientific provenance](../examples/structure_benchmark/detail-review.json) and
[independent export checks](../examples/structure_benchmark/detail-export-checks.json)
are retained alongside them. Full exports remain in the new output directory.

## Why this matters

On the 6,500-tip synthetic benchmark, the old six-tip detail highlighted 23
original edges, whereas the complete 12-tip selection spans 72. The new detail
retains all 72 exactly. In metadata without a `source` column, using only the
detail subset also previously reclassified other focal genomes as references.
The complete selection now determines reference classification in every view.

The renderer accepts a validated `focus_ids` subset separately from its scientific
`selected_ids`. All selected markers remain at their original positions. Only
focus labels are drawn; the crop encloses focus and explicitly requested context
reference tips. Coincident tips retain their disclosed shared callout. The
publication crop has a vector frame and explicitly states that counts are global.
The frame is a camera boundary, not a phylogenetic or taxonomic boundary.

## Reproduce the full-size comparison

```sh
python scripts/review_fixed_selection_detail.py --outdir outputs/detail_review_new
python -m pytest -q
```

Choose a new directory. The script uses one newly generated, deterministic,
wholly synthetic benchmark graph and one original-length equal-arc layout.
It produces separate 12 × 11 inch, 300 dpi overview, old-subset comparison,
complete-tree detail, Cloud detail and Canopy detail exports. Detail cameras and
data-to-display transforms are matched. Original edges, coordinates and the full
foreground are independently audited. Large SVG/PDF/PNG stay ignored in `outputs/`.
Compact full-page JPEGs and review provenance are committed separately.
Add `--tight` to omit those context references and reproduce the tighter wash
failure case in another new output directory.

The old-subset comparison intentionally reproduces the previous *selection*
behaviour using the current renderer; it is not a byte-for-byte archived renderer.
The review's context tips are geometric extrema of two named synthetic input
populations (P01/P02), not inferred nearest relatives. Their exact IDs are recorded.
No empirical data, private inputs, sequence analysis or inference is involved.

## Provenance and compatibility

Each CLI detail now has its own `.provenance.json` containing:

- Full highlighted IDs, labelled IDs and crop IDs, recorded separately.
- Stable original-edge identities and a hash of every original node coordinate.
- Full-tree validation, exact configuration, input hashes including the detail-ID
  file, crop bounds and actual SVG/PDF/PNG hashes.

The overview links that report and asserts exact foreground and coordinate-hash
agreement. Existing `plot`, `demo` and `--detail-selected` syntax is retained.
`detail_panel.selected_tip_ids` remains the requested detail subset;
`selected_subtree_edges` now counts the preserved **complete** foreground.
Invalid detail-ID requests are rejected before any figure export.

## Critical visual assessment

The complete-tree detail exposes local reference branches and separates the
nearby noncoincident focal marker from the four coincident ones. The preserved
solid foreground is traceable; dotted annotation leaders stay distinct. No true
node is moved, and coincident branches are not artificially expanded.

**The Cloud/Canopy close-ups still have an obvious rectangular camera boundary.**
Unlike an unpadded raster artefact, this is the intentional crop of the unchanged
full-scene wash. At tight zoom, the overview-scale blur becomes a broad, nearly
uniform coloured rectangle and obscures fine reference structure. Wider actual
reference context helps, but these wash close-ups do **not** pass final aesthetic
acceptance. The vector crop frame and caption make the window explicit; no
viewport fade or invented cloud silhouette hides the failure.

The complete-tree detail is currently the more useful structural inspection
view. Scale-aware density treatment at high magnification remains a separate P1
renderer task, requiring explicit bandwidth provenance and comparison against
this unchanged graph. The overall synthetic benchmark is not empirical biological
validation. No claim of a final publication-ready cloud follows from passing tests.
