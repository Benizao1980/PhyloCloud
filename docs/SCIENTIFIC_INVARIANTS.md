# Scientific fidelity: population structure is the data, not decoration

**Non-negotiable design principle:** PhyloCloud is a visualization of an *existing, inferred tree*, not a generator of visually plausible evolutionary relationships. Ben Pascoe's GETcampy sketch guides the presentation, not the geometry that determines biological relationships.

## What must remain invariant

1. **Tips and IDs.** Keep every genome present in the full Newick tree exactly once. The selected MAGs must be exact full-tree tip IDs.
2. **Topology.** Preserve all bipartitions (unrooted splits), internal branching order in the graph, sister-group relationships, and the number of sampled genomes per lineage. Never shuffle tips or force species into decorative lobes.
3. **Evolutionary distances.** Preserve every original edge length and therefore every pairwise *patristic* distance. The drawn line segment between adjacent vertices must be proportional to its original branch length in the default phylogram. Do not normalise tips to one radius.
4. **Reference density.** Use **all available reference genomes** in the background layer; do not artificially fill a sparse clade or thin a dense one for aesthetic balance. Rendering opacity may change, but the data and counts must not. Visual density reflects **sampled reference coverage**, not necessarily natural population abundance.
5. **Species, lineages and support.** Colour solely from supplied metadata; mixed-taxonomy ancestral edges remain neutral. Do not infer a monophyletic species solely from labels. GTDB names (including suffixes such as `Campylobacter_D`) and tree support annotations must remain faithful to their sources.
6. **Foreground fidelity.** Highlight only original edges in the minimal connected subtree of the selected tips. A reconstructed or separately laid-out MAG-only tree is forbidden. Do not invent connections, shrink distances, or implicitly conflate a nearest patristic neighbour with an ANI neighbour.
7. **No false geometry.** Display-centre choice is not biological rerooting. Topology-preserving angular layouts and rotations are permitted; visual-only branch-length transformations or density blurs must be explicitly optional, labelled, and scientifically justified.

## Allowed changes versus disallowed changes

| Allowed without changing biology | Not allowed merely to match the sketch |
| --- | --- |
| Rotate the whole layout; reorient subtrees around nodes while keeping their edges and lengths | Regroup or rearrange taxa into preferred coloured species clusters |
| Use thinner strokes, transparent reference branches and subdued markers | Drop outliers or compress long phylogenetic branches secretly |
| Move labels independently and add callout connectors | Move genomic tip positions independently of the actual tree |
| Overlay a clearly identified translucent density treatment *computed from plotted branches* | Paint invented evolutionary branches or treat blur as a phylogenetic estimate |
| Show actual lineage sample counts and proximity from tree distances | Imply reference tip density measures population prevalence without a sampling model |

## Required regression checks

- Every original tip ID and branch appears in the full rendered tree and in the same topology.
- Compare the set of all non-trivial *unrooted splits* before and after layout.
- Compare all or sampled pairwise patristic distances with the original Newick, including distant and closely related taxa.
- Check that each highlighted edge belongs to the unmodified full graph, and each selected MAG connects through the correct paths.
- Check species labels and group sizes against metadata; report missing and mismatched IDs.
- Check resulting SVG/PDF for vector paths and clipping; colour and transparency should not erase genuine population substructure.
- Save tree hash, selected tip list, metadata/config versions, layout algorithm and parameters, plus a reproducibility summary with each figure.

## GETcampy test before v0.2 acceptance

Apply both layout options to **the identical inferred tree containing 6,436 GTDB references plus nine GETcampy MAGs**. Inspect clade memberships, between-lineage distances, deep divergences, reference sampling density and MAG placements *before* selecting the prettier visual treatment. If the real inferred tree does not make the same organic cloud shape as the hand drawing, we keep the actual population structure and change the design expectations instead.

The synthetic six-fan demo is an illustrative algorithm test. Those six apparent clades are **generated synthetic groupings**, not evidence that real Campylobacter reference species each form one neat fan.