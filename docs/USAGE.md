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
