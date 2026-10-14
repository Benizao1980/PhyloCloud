# Running PhyloCloud on a Linux HPC cluster

This guide uses the **real `phylocloud` CLI in GitHub**, not concept-art visualisations. The current installation is an early alpha; any manuscript-ready figure still needs visual review. Tested Python versions in GitHub Actions: **3.10 and 3.12**. The renderer uses non-interactive Matplotlib (`Agg`), so no desktop or X11 is required.

## 1. Install on a login node

Choose a Python **3.10+** module made available by your own cluster; the example module name is not universal. Do **not** run expensive plotting on the login node.

```bash
module avail python                # if your cluster uses environment modules
# module load python/3.11          # adapt to the actual module shown above
python3 --version

mkdir -p "\${SCRATCH:-$HOME}/phylocloud_work"
cd "\${SCRATCH:-$HOME}/phylocloud_work"
git clone https://github.com/Benizao1980/PhyloCloud.git
cd PhyloCloud

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[test]'
python -m pytest -q
phylocloud --help
```

If the HPC does not have `venv`, use the site's supported Conda module/environment instead; e.g. `conda create -n phylocloud python=3.11`, `conda activate phylocloud`, then install the same package. If login-node outbound GitHub/PyPI access is restricted, use your institutional mirror or transfer an approved repository/virtualenv/wheel package; don't assume compute nodes have internet access.

## 2. Smoke test with synthetic data

The first render is small and publicly reproducible, and creates **fictional genomes**, not unpublished Campylobacter or GETcampy inputs. Use an interactive compute session for testing or submit a short batch job if required.

```bash
source .venv/bin/activate
export MPLBACKEND=Agg
export MPLCONFIGDIR="\${TMPDIR:-$HOME}/phylocloud-mpl-\${USER}"
mkdir -p "$MPLCONFIGDIR"

phylocloud demo --outdir outputs/demo --seed 47 --references 60 \
  --style cloud --length-mode original
```

Expected: `outputs/demo/phylocloud_demo.svg`, `.pdf`, `.png` and `.provenance.json`, plus synthetic Newick, metadata, selected-tip list and YAML. A larger synthetic demo uses `--references 900`.

## 3. Your dataset: input contract

PhyloCloud is a **drawing program**. It does not infer a phylogeny from FASTA files, reads or a Kraken2 report. Provide:

- `tree.nwk`: combined original reference+focal Newick phylogeny, unique exact tip IDs, finite non-negative lengths on **every edge**.
- `metadata.tsv` (or CSV): one matching `genome_id` row for **every** tree tip, a `species` column, optionally `source`, `label`, `lineage`, `host`, etc. To mark reference tips in a mixed dataset, set their `source` to `GTDB` or a value containing `reference`; mark focal samples differently (such as `MAG`). Without source values, nonselected tips are treated as references.
- `selected.txt`: one **exact** focal tip name per line; selected names must be present in the Newick and metadata.

Reference genome assemblies/IDs and taxonomic metadata can come from [GTDB](https://gtdb.ecogenomic.org/) or [NCBI Datasets](https://www.ncbi.nlm.nih.gov/datasets/), but you must construct/infer a **tree containing both your references and focal genomes**. The [reference data guide](REFERENCE_DATA.md) explains why Kraken2 is not a Newick-tree source.

For the private GETcampy/GTDB R226 example, check that the files you're using are exactly the intended tree and metadata, not just a GTDB reference-only tree. The audited original example had **6,445 tips**, **6,436 GTDB references**, **nine focal MAGs**, **11,389 original tree edges**, and a **72-edge** minimal focal connecting subtree. The public repo does *not* distribute those data.

## 4. Reproduce Cloud or graphical mode

Set the following paths to your **actual HPC locations**; these are placeholders, not guaranteed paths to your existing Box/HPC files.

```bash
TREE=/path/to/tree.nwk
META=/path/to/metadata.tsv
SELECTED=/path/to/selected.txt
mkdir -p outputs/real

# Original Newick branch lengths: default and appropriate for evolutionary distances.
phylocloud plot --tree "$TREE" --metadata "$META" --selected "$SELECTED" \
  --style cloud --length-mode original --cloud-group-by species \
  --out outputs/real/cloud_original

# Broader, explicitly NON-METRIC graphic (original splits and tip IDs preserved).
phylocloud plot --tree "$TREE" --metadata "$META" --selected "$SELECTED" \
  --style cloud --length-mode graphic --cloud-group-by species \
  --out outputs/real/cloud_graphic
```

**Distance interpretation:** `original` draws source branch lengths. `graphic` deliberately expands/compresses displayed edges, including original zero-length edges; it must not be described as evolutionary divergence or shown with a phylogenetic distance scale bar. Both report the original input checksum and whether displayed distances remain evolutionary. The same `--length-mode` works for all aesthetic presets.

Try the alternative available alpha motifs (each is a software style, not a different phylogeny):

```bash
for style in canopy river constellation; do
  phylocloud plot --tree "$TREE" --metadata "$META" --selected "$SELECTED" \
    --style "$style" --length-mode graphic \
    --out "outputs/real/\${style}_graphic"
done
```

The `river` and `constellation` modes are **experimental**: River's visual strokes do not imply migration/transmission or gene flow; Constellation simply marks original reference-tip positions on a dark background. A genuinely polished visual family is still under development.

For a single combined PNG with metadata-derived neighbourhood crops:

```bash
phylocloud plot --tree "$TREE" --metadata "$META" --selected "$SELECTED" \
  --style cloud --length-mode original --species-panels 3 \
  --out outputs/real/cloud_panels
```

`*_species_panels.png` is an additional **raster review sheet**; normal SVG/PDF remain the editable full-tree exports. If you want an editable magnified focal subset, create a `detail_selected.txt` of at least two focal tip IDs from `selected.txt` and use `--detail-selected detail_selected.txt`.

## 5. Example Slurm job

Slurm directives are **only an example**. Check whether your system uses Slurm, PBS or another scheduler; adjust account/partition/memory/time as required. Do not assume `python/3.11` is an installed module on every HPC.

```bash
#!/usr/bin/env bash
#SBATCH --job-name=phylocloud
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=phylocloud-%j.log

set -euo pipefail
cd /absolute/path/to/PhyloCloud
source .venv/bin/activate
export MPLBACKEND=Agg
export MPLCONFIGDIR="\${SLURM_TMPDIR:-\${TMPDIR:-$PWD}}/phylocloud-mpl-\${SLURM_JOB_ID:-manual}"
mkdir -p "$MPLCONFIGDIR"
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1

TREE=/absolute/path/to/tree.nwk
META=/absolute/path/to/metadata.tsv
SELECTED=/absolute/path/to/selected.txt
mkdir -p outputs/hpc

phylocloud plot --tree "$TREE" --metadata "$META" --selected "$SELECTED" \
  --style cloud --length-mode original --species-panels 3 \
  --out outputs/hpc/cloud_original
```

Save as `phylocloud.sbatch`, replace the paths, and submit `sbatch phylocloud.sbatch`. These resources are **initial requests**, not measured requirements for all trees. Benchmark with a smaller tree, and move the output directory to project scratch if your home quota is limited.

## 6. Verify the output and copy figures home

```bash
python - <<'PY'
import json
p = json.load(open("outputs/hpc/cloud_original.provenance.json"))
print("Tips:", p["tips"], "edges:", p["tree_edges"])
print("Reference genomes:", p["reference_genomes"],
      "focal edges:", p["foreground_edges"])
print("Display distances evolutionary:",
      p["validation"]["display_distances_are_evolutionary"])
print("All original edges retained:",
      p["validation"]["all_original_edges_retained"])
print("Max original-length display error:",
      p["validation"]["max_absolute_edge_length_error"])
PY
```

To transfer from a local workstation, use `scp` or `rsync`, substituting the real HPC login host and path:

```bash
rsync -avP your_username@your_hpc_login:/absolute/path/to/PhyloCloud/outputs/hpc/ ./phylocloud_hpc_outputs/
```

The basic output stem has `.svg`, `.pdf`, `.png` and `.provenance.json`. SVG/PDF tree/text layers are vectors but coloured density washes can be embedded raster images. Review output visually at the intended journal/presentation size; scientific invariants alone do **not** certify an attractive or publication-ready figure.
