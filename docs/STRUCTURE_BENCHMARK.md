# Structural benchmark: visual acceptance before aesthetic claims

The original `make_demo` is a friendly illustration: six independently grown
species-specific subtrees attach to a common centre, species are monophyletic by
construction, reference counts differ only modestly, branch lengths have a
restricted distribution, and nine focal tips are distributed 3/2/1/1/1/1 among
species. It cannot establish that clouds faithfully represent mixed taxonomy,
dense co-located focal genomes, severe sampling imbalance or sparse outliers.
Passing its technical tests did not demonstrate publication-quality composition.

## Data choice and scope

No approved real reference tree was found among checked-in fixtures. The only
previously documented 6,445-tip real tree is unpublished GETcampy material and
was **not accessed**. Existing public examples here are synthetic. This review
therefore generates an explicitly fictional, adversarial tree; no new inference,
sequence downloads, HPC jobs or biological interpretation occur.

`phylocloud.benchmark.make_structure_benchmark` uses seed 650047 to construct
6,500 tips (6,488 references and 12 focal tips), 28 uneven sampled populations,
a nested asymmetric hierarchy, heterogeneous internal/terminal lengths,
1,012 zero-length edges, a sparse long terminal, and four exactly coincident
focal tips. Eight synthetic species labels recur across distant populations,
with local mixed-label runs and isolated discordant labels. Labels never drive
the topology or the layout. Dominant reference categories range from 2,930 to 82
members. These choices stress realistic failure modes; this is **not** a fitted
microbial evolutionary model, a reproduction of GETcampy or empirical validation.

## Full-size matched views

The script constructs **one graph and one original-length equal-arc layout**,
then passes that same layout object to all three renderers. Every original
edge remains present. A common camera is applied before export. No independently
pruned or positioned foreground tree exists. An independent union-of-paths
oracle checks all 72 selected edges. Exact identity of all 12,996 original edges
and lengths establishes graph/split preservation, including zero-length edges.
All node coordinates are hashed before/after, and each SVG branch collection is
checked for exactly the expected number of vector paths.

```sh
python scripts/review_structure_benchmark.py --outdir outputs/structure_review
python -m pytest -q
```

Choose a new directory; existing outputs are never overwritten. Individual
exports include 300 dpi PNG, hybrid SVG/PDF and
per-view provenance. The preserved legacy baseline uses a 14 × 11 inch configuration;
the revised publication composition uses an exact 12 × 11 inch canvas. `index.html` links to each full-size view; review JPEGs are
2,400 pixels on their longest side, **not miniaturized composite panels**.
Source/input/output hashes, dependencies, shared bounds, coordinate hash,
selected edge identities and boundary alpha are in `review.json`.

Baseline views using the PR #23 renderer:

- [Complete original tree](../examples/structure_benchmark/baseline-tree.jpg)
- [Cloud](../examples/structure_benchmark/baseline-cloud.jpg)
- [Canopy](../examples/structure_benchmark/baseline-canopy.jpg)
- [Provenance](../examples/structure_benchmark/baseline-review.json) and
  [fixture specification](../examples/structure_benchmark/fixture.json)

Large generated SVG/PDF/PNG and generated inputs stay under ignored `outputs/`.
Only separate review JPEGs and small manifests are retained in Git.

## Critical baseline review

- No visible rectangular wash termination was found on full-page inspection;
  outer raster alpha is zero in Cloud and Canopy. This does **not** certify that
  every density setting is free of grid or tone artefacts.
- The irregular, separated populations and true gaps survive; the cloud does not
  become six neatly separated species arms. Sparse lineages remain sparse.
- The underlying reference tree is too faint to serve as a strong visual oracle.
- Species captions collide with each other, focal labels and original branches.
  One caption per nonmonophyletic category is semantically weak: prefer a key.
- The dark foreground remains traceable overall, but crowded/coincident focal
  labels have ambiguous leaders. Numerical geometry preservation is insufficient.
- Excess margins waste canvas. Some internal whitespace is genuine: the long
  outlier and asymmetric original tree cannot be compacted by moving its nodes.
- These baseline figures **fail publication-composition acceptance**. The
  [publication composition review](PUBLICATION_COMPOSITION_REVIEW.md) tests a
  focused follow-up on this exact fixture, with full-size comparisons and actual
  text-box collision checks.
