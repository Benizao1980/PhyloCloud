# Multiscale cloud visual review — v0.3 experiment

**Status:** working alpha renderer; scientific tests passing; **aesthetic acceptance still open**.

## Why the real Campylobacter source is challenging

Local unpublished GTDB R226 + GETcampy data contains 6,445 tips (6,436 GTDB references + nine MAGs), 11,389 original edges (3,060 zero-length) and an exact 72-edge connecting subtree for the MAGs. Species sampling is sharply unequal: 3,410 *Campylobacter_D jejuni*, 1,586 *Campylobacter_D coli*, 159 *Campylobacter_D upsaliensis*, only one *Campylobacter infans* reference (alongside six selected *C. infans* MAGs) and numerous sparse species.

Under an **original-length phylogram** layout, major reference clades occupy tiny regions relative to long evolutionary distances elsewhere. A huge made-up *C. infans* cloud would be scientifically misleading. Likewise, simply expanding dense species groups to fill the page would alter branch-length geometry.

The accepted image-generated atmospheric concepts are **design references**, not validated plots and not representative of literal species position unless proven.

## Current multiscale algorithm

- Colour and label metadata category defaults to `species`; both can be configured.
- Every reference tip contributes one observed point. Optional optical texture is sampled *on original reference-bearing, metadata-homogeneous edges* and downweighted; it is **not** a new reference-tip dataset.
- Species fields are normalised on one shared optical scale. A sparse species does not receive the same optical strength as a large reference collection.
- Rare groups are collected into a neutral display wash when category count exceeds `cloud.max_density_groups`. The underlying tree, source metadata, counts and provenance remain unmodified.
- The resulting density wash is a **raster** overlay. Original edges, exact selected subtree, labels and genome marker XY stay editable/faithful.
- The older tip-only implementation remains selectable using `cloud.density_engine: legacy` for side-by-side comparison.

## Local scientific and aesthetic validation

The multiscale local implementation was tested on the original biological dataset without publishing it: 6,445 tips, 11,389 edges, nine selected MAGs, original connecting subtree 72 edges; every original edge length preserved with maximum numerical error around `6e-17`. Tests on synthetic data check deterministic images, complete reference counts, unchanged tree coordinates, selected edge membership and configurable lineage grouping.

**Not yet achieved:** the atmospheric cloud composition of the approved image-generation concepts. A single full phylogram still looks relatively sparse. The strongest scientifically accurate visual treatment uses a full-tree overview alongside genuine geometric crops of densely sampled *C. jejuni*, *C. coli* and focal *C. infans* neighbourhoods. Different panels have **different display scales**, but within each panel the edges are exact original lengths.

The original private data and biological-result images have not been committed to this public repository.

## Next steps before merge / release

1. Add a reusable automatic **species-neighbourhood panel composer**, not just manually preselected labels: use true full-tree coordinates with panel-specific magnification and scale bars.
2. Visually review print-sized SVG/PDF with species labels at genuine density modes; prevent overlap with selected MAG labels.
3. Benchmark 6,445, 25,000 and 50,000 references for time, peak memory and repeatability.
4. Consider alternative **declared topology-only** plot layouts solely when users opt in; these must never claim proportional phylogenetic branch lengths.
5. Keep both scientific numerical gates and explicit human aesthetic review. Passing GitHub CI alone does not make a publication-quality figure.

Related issues: [#6](https://github.com/Benizao1980/PhyloCloud/issues/6), [#7](https://github.com/Benizao1980/PhyloCloud/issues/7), [#8](https://github.com/Benizao1980/PhyloCloud/issues/8), [#9](https://github.com/Benizao1980/PhyloCloud/issues/9).
