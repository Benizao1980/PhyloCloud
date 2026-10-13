# Usage and configuration

Start with [the README quick start](../README.md). The following commands and YAML keys are implemented in the current development branch.

## Commands

```bash
phylocloud --help
phylocloud demo --outdir outputs/demo --seed 47 --references 900 --style cloud
phylocloud plot --tree tree.nwk --metadata metadata.tsv --selected selected.txt --style canopy --out outputs/canopy
```

`phylocloud plot` supports `--tree`, `--metadata`, `--selected`, `--out` (required), and optional `--config`, `--style`, `--cloud-group-by`. The CLI still supports the previous `publication` and `soft_cloud` styles. `--style` overrides the named style preset from YAML and preserves other config keys; use distinct output stems for side-by-side comparisons.

## Input contract

- Newick tips must be unique with all branch lengths specified, finite and non-negative.
- CSV/TSV metadata must include `genome_id` and `species`; each tree tip needs a matching metadata row. `source` values `GTDB` or containing `reference` mark the reference background; without source values, all non-selected tips count as references.
- Selected tips: one matching exact tree ID per line (ignore empty lines and comment lines starting with `#`).
- Optional metadata categories may be used for colour/label grouping via `--cloud-group-by lineage`, etc. Unknown or blank values are neutral/Unassigned.
- The display centre is not phylogenetic rooting; `phylogenetic_spread` is experimental and is **not classical equal-daylight**.

## Configurable native visual options

See [the Cloud YAML](../examples/presets/cloud.yml) and [the Canopy YAML](../examples/presets/canopy.yml).

```yaml
style:
  preset: canopy
  title: 'My phylogenetic diversity'
  subtitle: 'Reference context and focal genomes'
cloud:
  group_by: species
  label_by: same       # or none; custom label grouping not yet supported
  colours:             # explicit colour-name or hex-code overrides
    'Campylobacter infans': sage
    'Campylobacter_D jejuni': powder_blue
  opacity: 0.5
  bandwidth_px: 16
  resolution: 480      # 128..900
  max_density_groups: 12
  max_labels: 7
  min_label_references: 15
```

The colour and label grouping defaults to species. Small categories beyond `max_density_groups` are pooled **only in a neutral visual-density layer** to cap rendering costs; their genomes, original branch edges, metadata categories, actual tip dots, and full input counts are still preserved. `reference_group_counts` in provenance retains the full counts.

Cloud/Canopy combine a transparent **raster** gaussian wash with fine **vector** original branches, tip markers and text. More opacity increases colour weight, not biological abundance. River is a visual treatment of existing branches, not gene flow. Constellation reverses canvas/text colours, without changing coordinates.

## Output formats

For `--out outputs/myplot`: `myplot.svg`, `myplot.pdf`, `myplot.png`, `myplot.provenance.json`.

The provenance report includes input hashes, precise original edge-retention and drawn edge-length checks, zero-length counts, rendered style, group and per-category reference counts, cloud bandwidth/opacity/resolution and broad label anchors.

## Display caveats

Very large reference collections often contain overrepresented lineages and many extremely short or zero-length branches. A full-tree overview will **not** resemble a uniformly filled or radial reference field, and it would be scientifically misleading to move those tips to improve the design. Use explicit geometric crops/zoom panels (current YAML supports `style.zoom_to_selected` for an exact selected-tip crop), or separate neighbourhood figures. Disjoint occurrences of the same species must never be merged into a fictitious monophyletic cluster.

This is a research software prototype. For manuscript submission, inspect the SVG/PDF and provenance at final print size, review genus/species labels against actual metadata, and compare to another trusted tree viewer.

## Two-panel neighbourhood overview (`--detail-selected`)

The v0.3 development CLI can optionally create a true-geometry view of **a subset of the original selected tips**. Supply a second text file (at least two distinct tip IDs, all present in `--selected`):

```bash
phylocloud plot \
  --tree tree.nwk --metadata metadata.tsv --selected selected.txt \
  --style cloud --cloud-group-by species \
  --detail-selected selected_neighbourhood.txt \
  --out outputs/my_phylogeny
```

Outputs include the ordinary `my_phylogeny.svg/.pdf/.png` and `my_phylogeny.provenance.json`, plus the independently editable `my_phylogeny_detail.svg/.pdf/.png` and a labelled `my_phylogeny_overview_detail.png`. The last file is a **raster contact sheet**, not fully editable SVG/PDF; use the underlying vector panels for manuscripts.

The neighbourhood panel is **not a re-inferred or independently laid-out tree**: it plots the original full-tree coordinates with a crop centred on the selected subset, and may show the surrounding original reference edges. It suppresses broad cloud labels outside the crop to avoid an artificially huge export canvas. Zero-length coincident tips can remain indistinguishable and may require an appropriate additional annotation/inset.

A complete second-species walkthrough with input files and real outputs from the renderer is in [the synthetic E. coli example](../examples/other_pathogen/README.md). For genuine GTDB reference accessions or Kraken2 input distinctions, see [Reference datasets](REFERENCE_DATA.md).


## Multiscale native cloud experiment (v0.3 development)

Cloud/Canopy now support a `cloud.density_engine: multiscale` underlay (default in the development branch). Density is derived from **one real reference-tip sample per reference genome**, augmented with downweighted, on-segment samples of **original metadata-homogeneous edges that contain reference descendants**. It does not infer or add genomes or branches. The density wash is raster; tree geometry/text remain vectors. The alternative `cloud.density_engine: legacy` retains the previous reference-tip-only wash for comparison.

This changes only cloud appearance, not tree geometry, branch lengths or selected-edge relationships. Very sparse species cannot acquire large artificial reference clouds. Figure aesthetics at whole-tree scale remain constrained by strongly unequal genetic distances and sampling; use the existing `--detail-selected` exact-coordinate crop for dense focal areas. See [Issue #6](https://github.com/Benizao1980/PhyloCloud/issues/6) for further compositional refinement.


## Automatic reference-species neighbourhood composition (new opt-in preview)

For densely sampled reference phylogenies, add `--species-panels 3` to automatically create a **separate** visually organised review PNG alongside the normal editable SVG/PDF/PNG.

```bash
phylocloud plot \\
  --tree tree.nwk --metadata metadata.tsv --selected selected.txt \\
  --style cloud --cloud-group-by species --species-panels 3 \\
  --out outputs/my_phylogeny
```

This adds `my_phylogeny_species_panels.png` and a `species_panels` section in `*.provenance.json`. Panel categories are selected reproducibly: the most-sampled reference groups, plus one cohort of two or more selected genomes if it would otherwise be excluded. Group names and group sizes come from real metadata. Each panel uses **one original full-tree coordinate system** with a different camera crop; no graph is pruned or independently re-laid out. The raster composition is for visual review/communication; continue to use the separately exported SVG/PDF for editable scientific plotting.

**Scientific caution:** species panels have independent magnification. A species with a single reference genome is not assigned a fictitious rich cloud; grouped focal MAGs can still be labelled in that view. Sampling density is not prevalence. Original branch lengths and topology are unchanged. This feature is still experimental and not a substitute for manuscript validation.
