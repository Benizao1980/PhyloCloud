# PhyloCloud v0.2: population structure first

PhyloCloud uses the original complete Newick. Both visual layers are the same inferred tree, and every edge keeps its length. Reference clouds are **not** cartoons or alternative phylogenetic inferences.

## Presets

Publication: unrooted equal-arc weighted by descendant tip counts, neutral faint vector branches, dark exact MAG connecting subtree.

Soft cloud: experimental angular sectors weighted by tip_count^0.40 times sum_of_descendant_branch_lengths^0.60; NOT the classical equal-daylight algorithm. The optional diffuse underlay is a deterministic Gaussian blur of **observed reference tip coordinates**, not an inferred distribution, prevalence estimate, or topology. Original branches and text remain vector-editable in SVG/PDF; only the haze is raster.

True zoom: crop of the full original coordinate system, no pruned-tree re-layout. Optional exact tree context-reference IDs and original branch-length scale bar.

## Real-tree assessment (local Box sources, not published)

The user-provided GTDB R226 FastTree and metadata match 6,445 distinct tips: 6,436 GTDB references and nine GETcampy MAGs. The tree has 11,389 edges, including 3,060 zero-length edges; 72 original edges connect the nine selected MAG tips. A separate zoom of six C. infans MAGs marks the previously identified GCF_013416015.1 reference. No private genome tree, MAG metadata or handwritten image is committed.

Original tree SHA-256: ed2743f8d1974fd377a553844650f0437a998ecca7a2475b09cd6adfaf76e3c2.

## Reproducibility

Use the CLI demo to generate an entirely synthetic 900+9 dataset, then rerun plot with either examples/presets/publication.yml or examples/presets/soft_cloud.yml. Every run exports SVG, PDF, PNG and a provenance JSON containing input SHA-256 hashes, exact edge retention, zero-length edge counts and maximum edge-length error.

## Next

Validate a genuine equal-daylight reference implementation, handle closely coincident labels, and build optional detailed neighbour/context panels. Population structure takes priority over resemblance to the original sketch.