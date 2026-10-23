# Offline reference-bundle validation (schema version 1)

Validate **explicitly named, approved local files** without GTDB-Tk, a database,
network access, layout, rendering or phylogenetic modification:

```sh
python -m phylocloud.reference_bundle \
  --tree examples/reference_bundle/tree.nwk \
  --metadata examples/reference_bundle/metadata.tsv \
  --selected examples/reference_bundle/selected.txt \
  --manifest examples/reference_bundle/manifest.json \
  --out outputs/new-bundle-report.json
```

`--selected` is optional. It means the exact focal genomes requested for a future
render; omitting it selects **none**, rather than silently selecting every focal.
Focal genomes still need metadata and genuine tips in any combined tree.
Reference-only trees may omit it entirely. If an expected selected-file hash is
supplied, the corresponding selection file is required.

Exit status is **0** for integrity/declaration validity (possibly with warnings),
**1** for validation failure. JSON goes to the new `--out` file and a concise
summary goes to stdout. Existing reports and inputs are never replaced: output
uses exclusive creation before any input is read. A nonexistent output directory
or existing output produces a filesystem error without modifying existing files.
Malformed/missing inputs or manifest produce a useful failure JSON when the
output location is writable. Unexpected runtime failures are not scientific passes.

## Meaning of a pass

A pass means named inputs parse, IDs/roles/census agree, branch lengths satisfy
the production parser, supplied expected hashes match and supported provenance
declarations are consistent. It **does not establish phylogenetic correctness**,
accurate placement, correct taxonomy, reference completeness relative to a whole
database, sampling representativeness, licensing or permission to publish.
Every report fixes `phylogenetic_correctness.status` to `not_assessed` and
`permissions_assessed` to false. Provenance verification is declaration consistency
only. Neither a taxonomy label nor a nearest ANI reference places a genome.

An absent focal tip fails; no query is inferred, grafted or silently omitted.
No topology, original edge/zero-length edge, branch length, coordinate or reference
selection is modified. No tree is pruned/reconstructed. The validator does not
calculate a layout or selected connecting branches. Later rendering still uses
one original combined-tree layout and exact foreground-edge selection.

## Metadata and roles

Use the existing CSV/TSV metadata input: required `genome_id` and `species` plus
an explicit `source` role for **every tree tip**. The existing renderer's source
convention is deliberately reused, with a strict bundle subset:

| `source` (case-insensitive) | Bundle role |
|---|---|
| `reference` or `GTDB` | Reference genome |
| `focal` or `selected` | Focal genome |

`source` here denotes display membership, not the ecological reservoir or country.
Provider/release/original accession provenance belongs in the manifest/additional
metadata fields; a genome's origin in GTDB does not force it into the reference
role if it is explicitly focal. No source substring or missing-source fallback
is accepted by the bundle validator. Ordinary preflight/plot behaviour is preserved.

Tip and metadata sets must match **exactly**: missing rows and extra rows (including
references absent from the tree) fail. The generic preflight's extra-row warning
becomes an error for a bundle. Duplicate metadata headers and IDs fail. Existing
parser whitespace trimming is retained; aliases, accession-version stripping and
GTDB-prefix conversion are not performed. Only exact, unambiguous IDs are accepted.
Blank species labels remain explicit preflight warnings, not inferred taxonomy.

Selection must be unique and a subset of focal tips. Reference/focal roles are
disjoint. At least one reference is required; combined-tree kinds require at least
one focal. The optional `reference_release` and `marker_set` metadata columns,
when nonblank on reference rows, must match the manifest exactly. Focal-genome
metadata remains untouched; release identity is not guessed from species labels.

## Small manifest schema

JSON object, unique keys, no NaN/Infinity, no unknown fields. Required fields:

| Field | Type / values |
|---|---|
| `schema_version` | Integer `1` (not boolean) |
| `provider` | `gtdb` or `independent` |
| `tree_kind` | `reference_only`, `fixed_backbone_placement`, `joint_inference`, `curated_combined` |
| `reference_scope` | `species_representatives`, `class_subset`, `dense_collection`, `custom` |

Optional fields (absence is retained, not fabricated):

| Field | Type / validation |
|---|---|
| `release` | Nonblank string; moving `latest`/`current` aliases rejected. Required for GTDB: `R` plus digits, optionally `.subrelease`, e.g. `R232` or `R232.0`. |
| `marker_set` | Nonblank string. Required for GTDB-associated bundles. GTDB reference-only/fixed-backbone kinds require `bac120` or `ar53`; GTDB-associated joint/curated trees may declare their actual different alignment set. |
| `domain` | `bacteria` or `archaea`; if supplied must agree with `bac120` / `ar53`. Not inferred into the report if absent. |
| `branch_length_units` | Nonblank explicit string, e.g. `amino_acid_substitutions_per_site`, `nucleotide_substitutions_per_site`, `allele_differences`. `unknown` is allowed with a warning; units are not established by parsing lengths. |
| `reference_ids`, `focal_ids` | Unique exact nonblank string arrays. If supplied, each must match its **entire** metadata/tree role set, not just a subset. Use these for an explicit expected census. |
| `file_sha256` | Object with optional `tree`, `metadata`, `selected` hex SHA256 values, case-insensitive. Each supplied expected hash must match the named file; no arbitrary manifest-referenced files are opened. |
| `provenance` | Object with only the optional fields below, all nonblank strings. |

Allowed provenance fields: `method`, `software`, `software_version`,
`reference_release`, `marker_set`, `citation`, `source_uri`, `alignment_sha256`,
`mask_sha256`, `notes`. Nested release/marker declarations must match top-level
values. Alignment/mask hashes must have SHA256 form but are **recorded only**;
those files are not read or independently verified in this increment. Source
URIs are recorded strings, never fetched. No alias mappings, database paths,
placement files or automatic tree assembly are supported.

Known contradictory `fixed_backbone_placement` methods `ani_screen` and
`taxonomy_only` fail. Free-text method declarations are not semantic proof of
placement; a made-up or misleading statement is not independently detectable here.
A GTDB release declaration is not verification of upstream database contents or
GTDB-Tk/software compatibility. Those require the next importer/provenance gate.

Minimal independent manifests may omit unknown release, marker, unit or method
information. Missing marker/units/method produce actionable warnings. Missing
expected file hashes produce a warning: computed hashes identify bytes, but
without a trusted baseline they cannot establish file authenticity. An explicitly
supplied contradictory value fails instead of being silently ignored.

## Reports and privacy

The report includes copied supported declarations, file hashes (including manifest),
expected-hash comparisons, reference/focal/selection counts and membership hashes,
original-edge/zero counts through nested preflight, error/warning codes with actions,
validation scope and the same human summary printed to stdout. The core checks
reuse preflight's parsing/context once. Optional selection support extends its
Python API without changing the existing selected-file CLI contract or valid reports.

File hashes are checked around each parse, not as a transactional cross-file
snapshot. Retain frozen source files for later rendering. Existing expected hashes
must not be replaced simply to silence corruption/version mismatches.

Diagnostics omit offending ID lists and parser detail by default; add
`--include-identifiers` for a local detailed report. Declarations are preserved,
so free-text provenance fields may themselves contain sensitive information.
Even hashes/counts and declarations can be sensitive. Keep real reports local
and gitignored; input access/publication approval remains separate. The manifest
is read-only and cannot grant that approval to this tool.

## Synthetic examples and failures

The [example directory](../examples/reference_bundle/) contains a tiny complete
**hand-specified synthetic tree**, three references, two focal tips, nonmonophyletic
species labels, unequal branch lengths and two zero-length edges. It is a parser/
consistency fixture, not inferred biology or a performance benchmark.

- [Valid manifest](../examples/reference_bundle/manifest.json) and [sample report](../examples/reference_bundle/valid-report.json).
- [Missing declared reference](../examples/reference_bundle/invalid-missing-reference.json) and [failure report](../examples/reference_bundle/invalid-missing-reference-report.json).
- [Inconsistent marker provenance](../examples/reference_bundle/invalid-provenance.json) and [failure report](../examples/reference_bundle/invalid-provenance-report.json).
- [Stale tree hash](../examples/reference_bundle/invalid-hash.json) and [failure report](../examples/reference_bundle/invalid-hash-report.json).

Replace `--manifest` with an invalid example and use a fresh output path to inspect
a failure. The small synthetic reports are committed; empirical files are not.
Regression tests also cover absent/duplicate focal/reference IDs, duplicate headers,
missing/negative branch lengths, absent roles, optional/no selection, malformed
JSON, GTDB release/marker/domain contradictions, deterministic outputs and exclusive
reports. No visual comparison is required because rendering is unchanged.

The PR is explicitly stacked on draft #28, which depends on #27 and #26; no merge
is authorized. The [GTDB-Tk importer handoff](GTDBTK_IMPORT_CONTRACT.md) is design
for the next increment, not an importer or a placement-verification claim.
