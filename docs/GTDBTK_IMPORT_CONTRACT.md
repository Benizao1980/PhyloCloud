# Next increment: actual GTDB-Tk placement output import

Design handoff, checked against official documentation on 2026-10-23.
**Not implemented by the offline bundle validator.** No GTDB-Tk run, split-tree
reconstruction, placement conversion or database download has been performed.

## Evidence roles

| Artifact | What it establishes about the recorded run | What it cannot establish alone |
|---|---|---|
| Query-containing `classify.tree` | References and query tips in a serialized placement-derived tree, with lengths | Ground-truth evolutionary accuracy, correct release, or which alternative placement was suppressed |
| Matching `pplacer.*.json` | Encoded reference tree/edge numbers, query names and recorded candidate edge placements with distal/pendant lengths and weight fields | A validated final combined topology without reconciliation to the exported tree; independent biological truth |
| `*.summary.tsv` | Classification method/results and query QC context | ANI-only/taxonomy assignments are not placements |
| `*.tree.mapping.tsv` | Which class-level tree was used for a query | Attachment to a single global branch-length tree |
| `gtdbtk.json`, logs, package VERSION/checksums and MSA/mask manifest | Version/method/package declarations and run identity when reconciled with actual files | Correctness merely from a directory name or a shared release label |
| Filtered/failed/disappearing-genome reports | Queries lacking a usable placement in that run | Permission to silently omit requested focal genomes |

The official tree description identifies placed query genomes in the Newick.
[tree format](https://ecogenomics.github.io/GTDBTk/files/classify.tree.html)
The pplacer JSON documents named fields including edge, distal length, pendant
length and likelihood weight; parse the `fields` array rather than assuming a
fixed column order. Preserve candidate records and query multiplicities.
[placement JSON](https://ecogenomics.github.io/GTDBTk/files/pplacer.domain.json.html)
The mapping file describes class-level assignments, not a global combined tree.
[mapping](https://ecogenomics.github.io/GTDBTk/files/tree.mapping.tsv.html)

These files can independently cross-check a **recorded placement** using distinct
representations. They do not independently establish the true biological position.
The summary alone cannot pass this gate: current GTDB-Tk can classify by ANI and
skip placement unless the relevant explicit placement option was used. The importer
must account for every focal ID as actually placed, ANI-only, filtered or failed.
[classification/output documentation](https://ecogenomics.github.io/GTDBTk/commands/classify.html)

## Scope and branch conventions

First support one explicitly pinned output/software format and one supplied tree:
archaeal domain tree, full bacterial tree, bacterial backbone or one class-level
bacterial tree. Record which. Inspect actual files/mappings; filenames alone are
not a scope test. A class-level tree can support valid local context but cannot be
advertised as complete GTDB diversity. Queries distributed across class trees
require separate scoped panels or an independently supplied valid combined tree.
Never stitch trees by taxonomy, reuse local branch scales as a global tree or
attach an ANI-classified query to its nearest named representative.

Placement distance fields refer to the matching encoded reference tree/model.
Expected edge/pendant lengths must be finite and nonnegative; distal positions
must be compatible with the referenced edge within a documented serialization
tolerance. Marker protein branch lengths are not ANI percentages, years or
nucleotide SNP counts. Record exact marker alignment/mask, model, branch units
and any upstream rescaling; do not infer all conventions from a release name.
Release-match tests must use the exact placement-package backbone, not assume
that the public GTDB taxonomy-curation tree is identical.

A query-containing tree subdivides reference edges. Reference-only projected
splits and summed segment lengths should recover the supplied package backbone.
This is a **verification-only calculation**, never pruning or collapsing the
rendered scientific input. Zero-length and multifurcating edges must remain
explicitly tested. Multiple queries on one edge do not by themselves establish
independently inferred query-to-query ancestry. Never invent a resolved query
subtree to improve a cloud.

## Required release and correctness gates

- Actual package VERSION/release and hashes, GTDB-Tk/pplacer versions, marker set,
  source tree and mask/MSA hashes must agree. Reject unsupported version pairs;
  do not extrapolate compatibility solely from taxonomy matches.
- Exact query IDs appear in the selected serialized tree and corresponding
  placement records; all requested missing/failed/ANI-only queries fail with reasons.
- Independently compare the encoded placement backbone, actual exported tree and
  package backbone using a separate tree/parser oracle and small hand-worked
  insertion fixtures. Small cases receive exhaustive patristic checks; resource-
  bounded checks for larger trees must state their scope rather than claim an
  unexecuted all-pairs validation.
- Verify reference census, zero-edge behavior, candidate/best-placement provenance,
  near-boundary lengths, duplicates, aliases, split-tree mapping and corruption.
  Keep likelihood weights distinct from support/confidence/prevalence and from
  the optical density wash.
- Preserve the supplied combined tree, reference set, every original length and
  complete selected connecting-edge set when passing to rendering. Reuse one
  layout for original/Cloud/Canopy/details. Visual acceptance is a separate gate.

Prefer importing the existing GTDB-Tk tree, not creating a replacement. If only
placement JSON exists, any upstream conversion needs its own validated/pinned
backend operation and explicit review. That conversion is outside this increment.
An evidence status should be 'recorded placement reconciled' at most; independent
biological accuracy and empirical fitness remain scientific-owner review.
