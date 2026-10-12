# Independent example: synthetic *Escherichia coli* lineages

All 189 tip IDs and genome assignments are **fictional**, created from a deterministic synthetic generator. This is an algorithm usability test, not a biologically inferred E. coli tree or an epidemiological claim.

The tree has 180 reference tips and nine focal tips, with six synthetic lineages (A-F). All tips are in one species but coloured by the user-defined `lineage` metadata column.

```bash
phylocloud plot \
  --tree examples/other_pathogen/synthetic_tree.nwk \
  --metadata examples/other_pathogen/synthetic_metadata.tsv \
  --selected examples/other_pathogen/selected_genomes.txt \
  --config examples/other_pathogen/config.yml \
  --style cloud --cloud-group-by lineage \
  --detail-selected examples/other_pathogen/detail_selected.txt \
  --out outputs/ecoli_example
```

This creates full-tree SVG/PDF/PNG, a zoomed detail SVG/PDF/PNG, a labelled overview-detail contact-sheet PNG, and one main provenance JSON. The full tree and detail both use identical inferred topology and coordinates; only the visual field of view changes.
