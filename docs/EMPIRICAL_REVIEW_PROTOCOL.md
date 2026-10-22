# Empirical phylogeny: input and permission checklist for owner approval

Status: **awaiting supplied locations and explicit approval**. No private project
search, unpublished-data access, inference or empirical render is authorized yet.
Please complete the fields below. Approval may cover local visualization while
withholding public redistribution; these are separate permissions.

| Required item | Owner-supplied information / approval |
|---|---|
| Original inferred Newick | Exact approved local path or public URL; original combined reference + focal tree, inference method/version, database/GTDB release and expected tip count. No new inference or placement is proposed. |
| Metadata | Exact approved path/URL; genome ID, reference/focal status, exact species/taxonomy labels, and provenance/accession/version. Identify private fields that must not enter captions or exports. |
| Selected genomes | Exact approved file/path or list of tip IDs, already present in this tree. No arbitrary placements or independent focal-only layout. |
| Tip matching | Permission for read-only validation of unique IDs, missing/extra metadata, duplicate aliases, branch lengths/zeros and reference/focal counts. Alias changes require an explicit mapping and approval. |
| Provenance | Who supplied the tree/metadata; accession/release dates; whether selected genomes are MAGs/isolates; permission to record hashes and restricted source manifests locally. |
| Local use | Explicit approval to read these named inputs and make local matched visualization exports. Does not authorize inference, HPC, copying raw inputs into Git or biological interpretation. |
| Publication | Which tree, metadata, sample labels, figures and aggregate statistics may be shown in a manuscript, draft PR or public gallery? Identify embargoes and reviewers. Local-use permission alone does not authorize this. |
| Redistribution | Whether any inputs may be redistributed and under which licence/consent. Default is **no input redistribution**. |
| Output location | Approved local, gitignored directory; permitted labels/pseudonyms and access restrictions. Do not put unpublished figures or private absolute paths in committed manifests. |
| Figure dimensions | Intended journal column/full-page width and height, minimum print font size, DPI, SVG/PDF editing needs, required panels. Suggested review: full-page first, then the actual final journal dimensions. |
| Biological questions | Owner-defined questions and focal neighbourhoods to inspect. The software agent will assess visual fidelity and readability, not infer new biological conclusions. |

After approval: hash the named files, validate joins and every original edge,
construct ONE original-length layout, freeze the exact full focal edge set and
reference membership, then render the complete tree, Cloud, Canopy and geometric
details from that same layout. Any optical bandwidth change is a disclosed visual
overlay parameter, not new phylogeny/prevalence/confidence. Report runtime/RSS,
fonts, vector/raster content, dimensions and file hashes. Human visual review is
mandatory before a publication-ready claim or proposed alpha release gate.

## Empirical visual acceptance record (pending)

| Criterion | Required evidence / acceptance |
|---|---|
| Scientific fidelity | One layout of the supplied original tree; exact edge identities/lengths, zero edges, coordinate and full selected-edge hashes; complete-tree comparison at matched coordinates. Owner compares genuine population structure. |
| Taxonomy and density | Nonmonophyletic labels retained; no implied clade, prevalence or confidence boundary; full source membership/counts; disclose optical grouping, normalization and bandwidth. |
| Foreground | Selected markers and exact connectors traceable at final size; coincident tips explicitly disclosed, no jitter. Crop does not silently reselect foreground. |
| Composition | Full-size complete-tree, Cloud, Canopy and useful geometric details; readable source/species key, no text overlaps/clipping; inspect dense branches and label leaders manually. |
| Framing and wash | Identify remaining rectangular crop/raster artefacts explicitly; compare overview and viewport bandwidths; no arbitrary masking or scientific repositioning. |
| Export and reproducibility | Final dimensions and minimum font sizes agreed; white backgrounds; SVG editable branches/text, PDF embedded fonts/vector strokes, hybrid raster wash disclosed; reproducible PNG and output/input/config hashes. |
| Resources | Record runtime and peak RSS with measurement scope on approximately 6,500 tips, versions and machine; no HPC or new biological analyses. |
| Human review | Owner records accepted/rejected panels and changes requested. Passing tests alone never grants visual or empirical acceptance. |

## Proposed v0.3 alpha release gate (not yet eligible)

- [ ] Owner approves named empirical inputs and permitted local/public usage.
- [ ] Exact original-tree invariants, membership and full focal-edge checks pass.
- [ ] Owner accepts matched empirical figures at agreed journal dimensions.
- [ ] Remaining visual/scientific limitations and optical methods are documented.
- [ ] Synthetic regression and compatibility CI pass on supported Python versions.
- [ ] Clean install, versioned examples, deterministic exports and provenance checked.
- [ ] Rights-cleared examples, citation metadata and draft release notes reviewed.
- [ ] Owner explicitly authorizes any merge and, separately, release publication.

There is no empirical approval, publication-ready declaration or release action
implicit in this checklist. Unpublished inputs/outputs stay local and gitignored.

## Read-only input preflight (on the preflight development branch)

Once the owner supplies named locations and authorizes reading them, run:

```sh
python -m phylocloud.preflight --tree /approved/tree.nwk \
  --metadata /approved/metadata.tsv --selected /approved/selected.txt \
  --out outputs/new-local-preflight.json
```

This does not search directories, generate a layout, render, infer a tree, modify
inputs or grant permission to publish them. The output must be a **new file**;
existing reports and input files cannot be overwritten. Exit status is 0 for
valid inputs (possibly with warnings), 1 for integrity failures. A missing output
parent or existing output raises a filesystem error before inputs are inspected.
Reports may still contain sensitive aggregate counts/hashes: keep empirical
reports local and gitignored unless publication is separately authorized.

The checker reuses production Newick/metadata/selection parsers and reference
classification. It checks missing/extra metadata IDs, unknown/duplicate selections,
invalid/missing branch lengths and duplicate tree/metadata IDs. Original zero-length
edges remain valid. It reports source-classification overlaps/gaps and blank species
labels, without repairing aliases, editing labels or changing membership. A single
selected genome remains valid but receives a no-connecting-subtree warning.
Production parser whitespace stripping is unchanged; aliases are never guessed.

Default reports contain counts and hashes without file paths or identifier lists.
Use `--include-identifiers` only for a local detailed diagnostic; those reports
include offending IDs and parser error text. Hashes are checked before/after each
individual parse to detect file changes during that read, not as a transactional
snapshot across all files. Retain the frozen approved inputs for later rendering.

`valid: true` means input integrity only. Provenance, taxonomic correctness,
publication rights, ecological representativeness and human visual acceptance are
**not assessed**. No empirical figure is approved or produced by this command.
