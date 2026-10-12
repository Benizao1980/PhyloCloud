# Current PhyloCloud v0.2 CLI — inputs and outputs

This document describes **implemented** behaviour on `main` as inspected 2026-10-12. It is not a preview of an implemented `phylocloud render`, `cloud`, `cloud-hero` or `--cloud-labels`. Those are proposals in [DESIGN_SPEC.md](DESIGN_SPEC.md).

## Install from source

```bash
git clone https://github.com/Benizao1980/PhyloCloud.git
cd PhyloCloud
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest -q
```

## Currently supported commands

```bash
phylocloud demo --outdir outputs/demo --seed 47 --references 900
```

Produces deterministic **synthetic** input fixtures and figures:

```text
outputs/demo/
  synthetic_tree.nwk
  synthetic_metadata.tsv
  selected_genomes.txt
  config.yml
  phylocloud_demo.svg
  phylocloud_demo.pdf
  phylocloud_demo.png
  phylocloud_demo.provenance.json
```

```bash
phylocloud plot \
  --tree path/to/tree.nwk \
  --metadata path/to/metadata.tsv \
  --selected path/to/selected_genomes.txt \
  --config examples/presets/soft_cloud.yml \
  --out outputs/my_cloud
```

`--tree`, `--metadata`, `--selected`, `--out` are required; `--config` is optional. Without config, the default style is `publication`. Current bundled configs are `examples/presets/publication.yml` and `examples/presets/soft_cloud.yml`; the latter uses experimental `phylogenetic_spread` (not true equal-daylight).

This command generates:
- `outputs/my_cloud.svg` — vector tree paths, markers and editable text; optional embedded raster density haze.
- `outputs/my_cloud.pdf` — vector tree paths/text; optional embedded raster density haze.
- `outputs/my_cloud.png` — high-resolution raster.
- `outputs/my_cloud.provenance.json` — source hashes and layout/style plus edge-count/length checks.

## Input examples

Newick (branch lengths required for every edge; identifiers must be unique):

```newick
((GTDB_001:0.03,GETCAMPY_GC_135:0.05):0.06,
 (GTDB_002:0.07,GETCAMPY_GC_413:0.04):0.08,
 GTDB_003:0.09);
```

Metadata: TSV/CSV with exact `genome_id` from tree and **required `species` column**. Additional arbitrary columns are retained but not yet used for broad cloud groups:

```tsv
genome_id	species	source	label	lineage	host
GTDB_001	Campylobacter infans	GTDB		L1	chicken
GETCAMPY_GC_135	Campylobacter infans	MAG	GC_135	L1	human
GTDB_002	Campylobacter_D jejuni	GTDB		L2	chicken
GETCAMPY_GC_413	Campylobacter_D jejuni	MAG	GC_413	L2	human
GTDB_003	Campylobacter coli	GTDB		L3	cattle
```

Selected genomes: `selected_genomes.txt`, exactly one matching genome tip per line:

```text
GETCAMPY_GC_135
GETCAMPY_GC_413
```

When `source` is supplied, the existing renderer recognises reference rows whose source equals `GTDB` or includes the word `reference` (case insensitive). Without any source values, nonselected tips are treated as references. Use explicit `source` for a real mixed-input tree until reference membership gets a dedicated validated field.

## Current YAML example

```yaml
layout:
  angle_mode: phylogenetic_spread  # experimental, not classical equal-daylight
  rotation_degrees: 19
style:
  preset: soft_cloud              # currently publication | soft_cloud
  species_background: true       # eligible tree branches coloured by metadata species
  density_overlay: true          # current *neutral* sampled-tip density haze
  density_opacity: 0.20
  title: "PhyloCloud / diversity in context"
export:
  width_inches: 14
  height_inches: 11
  dpi: 350
```

Important: the current species tint colours branches identified from taxonomy, **not separate coloured Gaussian density clouds**. Cloud labels aren't implemented. Arbitrary `lineage`/host/source grouping for the haze is also not implemented.

## Future proposed interface (NOT YET RUNNABLE)

```bash
phylocloud render \
  --tree tree.nwk --metadata metadata.tsv \
  --selected selected_genomes.txt --style cloud \
  --cloud-group-by species --cloud-labels same \
  --out outputs/my_cloud
```

Defaults: `--cloud-group-by species` and `--cloud-labels same`, meaning broad labels follow the colour grouping. To use a different metadata column, e.g. `--cloud-group-by lineage`, labels automatically become lineage labels too. A YAML variant would use `cloud.group_by: species`, `cloud.label_by: same` and `cloud.palette: ben-style:getcampy.species`, optionally `cloud.colours` for exact values.

Planned visual motifs: `cloud` (default), `constellation`, `river` (experimental) and `canopy`. A separate `finish=publication|hero` will govern restraint/atmosphere. Current v0.2 `publication`/`soft_cloud` presets remain supported. The new CLI will retain `plot` for compatibility. See [ROADMAP.md](ROADMAP.md).
