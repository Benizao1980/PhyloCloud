# Visual design brief: comparison with original GETcampy sketch

**Reviewed 12 October 2026.** The original photograph was supplied to the project for design discussion; it is *not included in this public repository* (to avoid publishing a personal photograph and its possible embedded location metadata). Any eventual public copy should be cleared and have EXIF removed.

## What the drawing communicates

The core image is a sparse, approximately diagonal, strong branching skeleton running through a broad, irregular and very pale **cloud of GTDB reference diversity**. Selected GETcampy MAGs are focal tips along that same full phylogeny. The cloud lies *behind* the stronger foreground structure, not around the rim of a wheel.

The drawing also includes subordinate analytical components: recovered-MAG counts by species (C. infans, C. jejuni, C. coli, C. upsaliensis); a small stacked nearest-neighbour/species-assignment summary; and an illustrative closer-scale subtree. These are future optional compositional panels, not part of the core tree geometry engine.

## Evaluation of prototype v0.1

| Visual attribute | Sketch | v0.1 synthetic | Next iteration |
| --- | --- | --- | --- |
| Organic silhouette | Broad interconnected clouds with uneven density | Six separated species fans | Explore equal-daylight and less artificially segregated synthetic fixtures |
| Dark foreground | Sparse tree weaving through faint references | Correct original connecting subtree, but hub/spokes dominate | Adjust display rotation, subtree-order and daylight while retaining the same edge lengths |
| Background texture | Pale grey with soft translucent species washes | Thin species-specific strokes, with sharp sectors | Separate species fills/point density from edge colouring; verify visual claims |
| Labels | MAGs are directly indicated; details are secondary | Large bold labels on a few rays | Deterministic collision-aware placement and restrained type |
| Taxonomy | Four primary illustrative groups | Six fictional reference groups | Categories and legend should come from real metadata, never invented |
| Supporting panels | Species count, nearest reference, magnified subtree | Legend only | Optional panels, not hardwired into renderer |

## Non-negotiable scientific criteria

- The full input Newick supplies **every** foreground and background branch; never overlay separately laid-out pruned trees.
- Foreground = minimal connected subtree containing the chosen original tips; retain original junctions and branch lengths.
- Only rigid rotations or topology-preserving branch-angle changes may be used without an explicit transformed-length disclosure.
- Do not put terminals on a shared radius. No outward circular cladogram/ring.
- Keep GTDB nomenclature faithfully, including Campylobacter_D; do not silently rename classifications.
- Species colour must not imply distinct evolutionary clades when those metadata are intermixed.
- If adding smooth gradients or density washes, they are visual overlays, not inferred edges or confidence intervals.

## Design acceptance for v0.2

1. Compare an identically sized crop of the main tree against the sketch; evaluate balance, softness, texture and dark-subtree legibility at manuscript dimensions.
2. Include one more organically intermingled synthetic stress fixture without changing actual inferred topology at render time.
3. Check 6,445 real-tree tips, nine focal tip IDs, 100% original-edge lengths and shared coordinates.
4. Validate SVG/PDF as editable vectors and prevent labels from clipping.
5. Add parameter/palette snapshot and hashes for full reproducibility.

The actual input tree may not resemble the hand sketch in all particulars: accurate inferred evolutionary structure takes precedence over forcing a decorative silhouette.
