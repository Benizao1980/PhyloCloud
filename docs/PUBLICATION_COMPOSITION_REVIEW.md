# Publication composition on the structural benchmark

This is a focused follow-up to the [6,500-tip structural benchmark](STRUCTURE_BENCHMARK.md),
stacked on its draft PR and PR #23. It adds opt-in `style.composition: publication`.
The existing `plot`/`demo` commands and default legacy composition remain available
while the new visual treatment is reviewed. No layout/selection algorithm or
cloud density formula changes are included.

## Inspect individual full-size figures

- [Complete underlying tree](../examples/structure_benchmark/publication-tree.jpg)
- [Cloud](../examples/structure_benchmark/publication-cloud.jpg)
- [Canopy](../examples/structure_benchmark/publication-canopy.jpg)
- [Matched scientific audit](../examples/structure_benchmark/publication-review.json)
- [Independent export checks](../examples/structure_benchmark/export-checks.json)

Each JPEG is a separate 2,400-pixel full-page view. The reproducible full exports
are 12 × 11 inches: 3,600 × 3,300 pixels at 300 dpi and 864 × 792 points in
**both** SVG and PDF. Unlike the legacy tight-bounding-box export, the new mode
retains the exact configured canvas dimensions across formats. SVG/PDF tree
branches and text stay vector/editable; Cloud/Canopy washes and reference dots
are embedded rasters. The complete-tree PDF has no embedded raster.

The same generated inputs, all node coordinates, 12,996 original edge identities
and lengths, all 72 selected edges and 1,012 zero-length edges match the preserved
baseline. All three revised views use one layout object, the same view bounds,
the same axes rectangle and an explicitly compared data-to-display transform.

## What changed and why

- Focal text moves into measured left/right callout margins, with order-preserving
  vertical packing in display units. Dotted annotation leaders are distinct from
  solid original phylogenetic edges. No true tip or branch moves.
- Four coincident focal tips share `F01 / F02 / F03 / F04 (coincident tips)`.
  Their original four zero-length terminal edges and actual markers remain; the
  figure does not invent separation to make them visible.
- Nonmonophyletic species use a separate, counted metadata key instead of a
  single broad species caption that could suggest a contiguous clade.
- Headers, semantic key, taxonomy key and methods/disclaimer occupy separate
  typographic bands. Text dimensions are measured; overlaps or clipping cause a
  clear error requesting a larger canvas rather than silently exporting them.
- The camera retains every outlier and visible wash but removes the previous
  generous proportional margins. The reference-only comparison explicitly uses
  stronger neutral branch contrast; native preset colours remain unchanged.

Text-box QA covers focal/context labels, titles, keys and footer. It is not a
proof that no leader can cross an original branch. Coincident markers necessarily
overprint; very close noncoincident markers may also overprint at overview scale. Arbitrarily large selections or long category lists may require a
larger page or a separate panel/table; this mode reports insufficient space.
Minimum reviewed text is 7.5 points **at the configured print dimensions**.
Shrinking these 12-inch figures to a journal column also shrinks their text.

## Critical visual assessment

**Rectangular artefacts:** no visible rectangular wash edge was found in the
full-page Cloud/Canopy review; measured outer raster alpha is zero for both.
Internal discrete-bin or tone artefacts are not ruled out for every setting.
The density engine itself is unchanged from PR #23.

**Foreground:** the nine callouts (covering 12 actual focal tips) can be followed
without colliding text. The dark connecting structure remains dominant and its
72 exact original edges are unchanged. The long focal branch stays long. Dotted
leaders cross parts of the background and are less ideal than direct labels for
an uncrowded tree, but avoid the baseline's ambiguous overlapping captions.

**Population structure:** Cloud is more diffuse; Canopy exposes the original
fine tips/branches more strongly. Both retain separated wisps, irregular outlines,
sparse lineages and genuine empty regions present in the complete-tree view.
They do not turn the eight scattered metadata categories into eight clades.
Very dense local topology cannot be read edge-by-edge at overview size: use the
vector tree or a true shared-coordinate detail panel for that purpose. The long
outlier and asymmetric structure impose real whitespace that must not be removed
by moving branches. The atmospheric treatment remains modest, not a continuous
painted silhouette. No decorative fill was added between unsupported regions.

**Acceptance status:** this is a visibly improved, scientifically auditable
composition candidate for human review, not a declaration that the desired final
PhyloCloud aesthetic or empirical validity has been achieved. The fixture is
synthetic, not a fitted evolutionary model. An approved precomputed real tree
remains necessary for empirical visual validation; unpublished GETcampy data
were not accessed. Neither green tests nor an absence of rectangles establishes
the final aesthetic acceptance criterion.

Grayscale exports are also generated by the independent QA script. Foreground
structure must be read from edges/markers/callouts, not wash colour alone; the
current eight-category palette has not been certified for every colour-vision
deficiency. Dense wash categories cannot all be identified reliably in grayscale.

## Reproduce and use

```sh
python scripts/review_structure_benchmark.py --outdir outputs/structure_review_new
# Optional independent PDF/font QA; needs pypdf==6.20.1 in the test environment:
python scripts/check_structure_exports.py outputs/structure_review_new
python -m pytest -q
```

For the historical composition use `--composition legacy`; choose a new output
directory each time. Repeated full-benchmark SVG/PDF/PNG exports were byte-identical
within the recorded environment. Small synthetic regression tests also verify
repeat export bytes, exact vector path counts, page size and coordinate anchors.
Large generated figures and inputs stay ignored under `outputs/`; separate JPEGs
and compact provenance remain reviewable in Git.

To apply the new composition through the existing CLI, add to a YAML file:

```yaml
style:
  preset: cloud                 # also publication, canopy or soft_cloud
  composition: publication
export:
  width_inches: 12
  height_inches: 11
  dpi: 300
```

The selected metadata label is retained (wrapped if needed). This is a composition
option, independent of the `publication` visual preset. Taxonomy uses the configured
`cloud.group_by` column in its key; the new mode replaces broad in-cloud captions
with that key. It does not imply monophyly or natural abundance.
