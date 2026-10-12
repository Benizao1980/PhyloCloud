# Where do I get reference genomes and a phylogenetic tree?

PhyloCloud is a **visualisation tool**, not a read classifier, genome assembler or phylogenetic inference engine. It takes one *already inferred* Newick tree with **both reference and focal genome tips**, metadata keyed by the exact tip IDs, and a text file listing focal tips. A downloaded genome collection, a Kraken2 database or a taxonomy table is **not by itself a phylogenetic tree**.

## Recommended source: GTDB

- [Genome Taxonomy Database](https://gtdb.ecogenomic.org/) — browse taxonomy, search and choose representative genomes.
- [GTDB download and genome access FAQ](https://gtdb.ecogenomic.org/faq) — advice on representative FASTAs, subsets and NCBI Datasets download scripts.
- [GTDB release archive](https://data.gtdb.ecogenomic.org/releases/latest/) — release-specific taxonomy tables, representative trees (`bac120.tree`, `ar53.tree`), and metadata.
- [GTDB representative sequences and alignments](https://data.gtdb.ecogenomic.org/releases/latest/genomic_files_reps/) — genomes, bac120/ar53 marker alignments and other large downloads. **The whole-genome tarballs are enormous; use smaller selected genome subsets where possible.**
- [GTDB-Tk](https://github.com/Ecogenomics/GTDBTk) — classifier / phylogenetic placement workflow, not simply a substitute for a jointly inferred focal-plus-reference phylogeny.

**Version note:** the current GTDB archive has advanced since the GETcampy R226 analysis. A newly downloaded tree or taxonomy may be R232 or later. Record the release and **do not silently combine tips, classifications or markers from incompatible GTDB releases**. If focal MAGs are absent from the downloaded reference tree, PhyloCloud cannot simply overplot them at arbitrary locations. First generate/obtain a valid *combined inferred tree* or appropriately validated placement tree containing the reference and focal tips and their branch lengths.

## Alternative genome sources

- [NCBI Datasets](https://www.ncbi.nlm.nih.gov/datasets/) — download selected genome FASTA files and assembly metadata from RefSeq/GenBank by taxon or accession. See the [official download tutorial](https://www.ncbi.nlm.nih.gov/datasets/docs/v2/how-tos/genomes/download-genome/).
- [ENA Browser](https://www.ebi.ac.uk/ena/browser/home) — assemblies/sequence accessions with associated metadata.
- [BV-BRC](https://www.bv-brc.org/) — bacterial/pathogen genome collections and analysis services; check actual tree formats and access/licensing for each dataset.
- Your own assembly collection or existing public/consortium phylogeny, including IQ-TREE/FastTree/RAxML outputs, as long as the tree actually includes both reference and highlighted tips.

**Example NCBI Datasets command** (a deliberately small batch of known accessions is safest):

```bash
datasets download genome accession GCF_000005845.2 --filename ecoli_reference.zip
unzip -l ecoli_reference.zip
```

This downloads sequences/metadata, **not a combined Newick tree**. Before tree inference, QC the genomes, select appropriate homologous markers/core alignment, ensure consistent naming, and estimate the phylogeny with an appropriate method (for example, [IQ-TREE 2](https://github.com/iqtree/iqtree2)). For a precomputed `*.treefile`/Newick that already includes your samples and references, skip the inference step and proceed straight to PhyloCloud.

## What about Kraken2 / Kraken databases?

[Kraken2](https://github.com/DerrickWood/kraken2) is a **k-mer/minimizer based taxonomic classifier**. Its databases associate sequence words with taxonomy; the classification report does **not** contain a phylogram of individual genomes with branch lengths. A Kraken2 report can inform a separate metadata column (for example `taxon` or `classification`), but **cannot be loaded as `--tree`**.

You *can* reuse genome FASTA records underlying a Kraken reference database if you retrieve their original sequences, deduplicate/quality-check them, and infer a valid phylogeny. Do not equate NCBI/Kraken names automatically with GTDB taxonomic names; map and document the taxonomy version or use a separate column. See the [official Kraken2 documentation](https://kraken2.readthedocs.io/en/latest/introduction.html) and [custom-database guide](https://kraken2.readthedocs.io/en/latest/custom_databases.html).

## Minimum reproducible workflow

1. Choose reference genomes and focal genomes; record database release, assembly IDs and any licensing/sharing constraints.
2. QC them and infer or obtain **one** combined tree in Newick format with unique tip IDs and valid nonnegative branch lengths (including zero lengths if inferred).
3. Prepare `metadata.tsv` with `genome_id`, `species`, optional `source`, `label`, `lineage`, `host`, etc. Every tree tip must map exactly once. In v0.3, `species` is required even if you colour by lineage.
4. Prepare `selected_genomes.txt`: one exact tree-tip ID per focal genome.
5. Run a reproducible figure, optionally colour/label by a metadata column or request a genuine zoom:

```bash
phylocloud plot --tree combined_tree.nwk --metadata metadata.tsv \
  --selected selected_genomes.txt --style cloud \
  --cloud-group-by species --out outputs/figure
```

PhyloCloud outputs an editable SVG, PDF, PNG and provenance JSON with counts and edge-length checks. All original reference genomes are retained in the graph; note that a dense wash visualises **sampling density**, not ecological population prevalence.

## Ready-made downloadable test, no external genomes required

See the [synthetic E. coli lineage example](../examples/other_pathogen/README.md). It includes a complete fictional Newick, metadata, selected tips and YAML. Its `lineage` colouring validates an alternative use case without requiring assembly download or tree inference.
