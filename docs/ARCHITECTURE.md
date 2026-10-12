# PhyloCloud architecture — scientific geometry + native visual clouds

**Status:** target architecture for a staged refactor beyond merged v0.2. The folders, classes and CLI commands under “Proposed” do not exist yet. See [DESIGN_SPEC.md](DESIGN_SPEC.md) for the aesthetic target and [ROADMAP.md](ROADMAP.md) for implementation order.

## What exists today (v0.2)

- `src/phylocloud/geometry.py`: parse unrooted graph from Newick, calculate equal-arc or experimental `phylogenetic_spread` coordinates, derive exact selected connecting edges and species-pure branches.
- `src/phylocloud/data.py`: metadata and YAML, Ben-style colours, publication and `soft_cloud` presets.
- `src/phylocloud/render.py`: one Matplotlib drawing function, vector tree/text + neutral blurred sampled-tip reference underlay, selected labels, optional context references/zoom.
- `src/phylocloud/cli.py`: `plot`/`demo` commands, edge retention/length audit and JSON provenance.
- Synthetic data, CI, scientific invariants and real-tree assessment: [V02_LAYOUT_REVIEW.md](V02_LAYOUT_REVIEW.md).

This foundation is valuable, but direct plotting mixes scientific decisions, cloud density, typography, style and export. The refactor should **move** those responsibilities without changing existing CLI outputs by default.

## Architectural law

```text
source Newick + metadata + selection + validated YAML
                          |
                          v
           Immutable ScientificTree (all edges, tip IDs)
                          |
           +--------------+--------------+
           |                             |
           v                             v
  Shared LayoutMap             ExactSelectedEdgeSet
 (every original node)         (original edge IDs only)
           |                             |
           +--------------+--------------+
                          |
                    FigureGeometry
               /          |         \
       reference edges    tip xy    highlighted edges
               \          |         /
                v         v        v
         CloudField     LabelPlan  StylePreset
        (DATA-DERIVED)   (move     (visual-only)
                        text ONLY)
                \          |         /
                 v         v        v
                    Immutable RenderScene
                          |
                validated ordered layers
                          |
              SVG / PDF / PNG + manifest
```

**No stage after ScientificTree is allowed to edit a node, edge or inferred length.** The unrooted layout chooses edge directions and preserves lengths; label planning never modifies tree coordinates; foreground and background use one LayoutMap.

## Proposed module packages

```text
src/phylocloud/
  core/
    tree.py           # typed immutable tree/edge IDs, Newick parser and validations
    metadata.py       # exact ID join, taxonomy/group strata, reference classification
    selection.py      # original-edge minimal connecting subtree
    provenance.py     # run manifest and hashes
  layout/
    equal_arc.py      # established baseline, tip-count weighting
    spread.py         # existing experimental phylogenetic-spread mode (correctly named)
    daylight.py       # planned genuine equal-daylight, separately validated
    optimizer.py      # constrained branch-angle rotations only
    anchors.py        # extent, display centre, crop and group anchor helpers
  cloud/
    points.py         # real reference tip points and original-edge samples
    density.py        # kernels, normalization, colour-stratified density fields
    washes.py         # alpha/compositing, raster buffers or bounded vector substitutes
    groups.py         # disconnected vs connected semantic component detection
  annotations/
    tip_labels.py     # collision-resistant focal labels anchored to exact tips
    cloud_labels.py   # taxonomy/group labels + disjoint-component validation
    titles.py         # typographic layout and captions
    legend.py         # semantic legend
    panels.py         # coordinate-preserving geometric zoom and optional tables
  render/
    scene.py          # immutable scene/layer command model
    layers.py         # ordered layer builders
    backend_mpl.py    # current Matplotlib implementation
    styles.py         # publication / cloud / cloud-hero named presets
    palette.py        # versioned Ben-style semantic palettes
  export/
    svg.py            # exact vector drawing, embedded wash when needed
    pdf.py            # hybrid/vector PDF with correct raster disclosure
    png.py            # controlled DPI rasterisation of whole scene
    manifest.py       # audit fields + output checksums
  cli.py              # compatibility plot/demo; planned render command
```

Refactor the existing geometry/data/render functions through adapters first, keeping existing Python imports and `phylocloud plot` usable. Do not do a simultaneous full rewrite.

## Domain objects and boundaries

Proposed lightweight Python dataclasses/protocols (names are design contracts, not implemented API):

```python
@dataclass(frozen=True)
class ScientificEdge:
    edge_id: int
    node_a: int
    node_b: int
    branch_length: float

@dataclass(frozen=True)
class ScientificTree:
    tip_id_to_node: Mapping[str, int]
    edges: tuple[ScientificEdge, ...]
    adjacency: Mapping[int, tuple[int, ...]]
    source_hash: str
    # No layout or style fields.

@dataclass(frozen=True)
class LayoutMap:
    coordinates: Mapping[int, tuple[float, float]]
    edge_segments: Mapping[int, tuple[tuple[float, float], tuple[float, float]]]
    algorithm: str
    parameters: Mapping[str, object]
    # All original edge IDs exactly once.

@dataclass(frozen=True)
class CloudField:
    data: object  # array/grid or vector points, NOT tree data
    transform: object  # exact coordinate-to-canvas mapping
    category: str | None
    density_method: str
    weights: object
    parameters: Mapping[str, object]

@dataclass(frozen=True)
class RenderLayer:
    kind: str  # wash, reference_edges, focal_edges, labels, ...
    payload: object
    z_index: int

@dataclass(frozen=True)
class RenderScene:
    geometry: LayoutMap
    selected_edge_ids: frozenset[int]
    layers: tuple[RenderLayer, ...]
    canvas: object
    audit: Mapping[str, object]
```

Keep layout coordinate precision independent of device resolution. RenderScene stores **true geometry references**, not a flat PNG; cloud imagery carries the same numerical coordinate transform.

## Layout engine

1. Treat Newick rooting as serialization/display choice; preserve original undirected graph topology.
2. Default to established unrooted equal-arc. Retain experimental `phylogenetic_spread` but **never mislabel it classical equal-daylight**.
3. Add genuine equal-daylight only after independent comparison (e.g. PHYLIP or ape); branch-angle optimisation is restricted to rotations of intact subtrees, not independent shifts of tips.
4. Keep all zero-length edges; many original nodes may occupy identical XY positions. No hidden random jitter.
5. Export actual edge-length scale bar only when untransformed proportional edge lengths are drawn. Avoid “scale” on topology-only modes.
6. Regress unrooted splits, individual edge lengths, sampled path distances and identical selected-edge IDs after every layout addition.

## Cloud engine: central scientific design

**Input:** immutable reference-tip coordinates from LayoutMap; optionally edge segments from that same map; metadata category per tip/edge.

**Point field:**
- Each reference genome contributes exactly one tip sample by default, including coincident tips; distinguish a reference count from a rendered dot count.
- Optional edge samples are taken *on* real line segments with deterministic spacing; choose and record weighting (e.g. per-unit branch length vs per-edge total weight). Edge samples must not masquerade as genomes.
- No introduction of random decorative branches, false tips or invented lineage labels.

**Density field:**
- Prefer a reproducible normalized Gaussian kernel or splatting implementation with a documented bandwidth in **data/figure units**, pixel mapping and numerical bounds.
- Compute separate category grids when metadata colour is requested, then blend with a documented alpha/compositing rule. Mixed ancestry should be neutral; taxonomy categories may intermix spatially.
- The density field changes optical weight **without changing the original underlying tree**. Do not shift points to improve aesthetics. Preserve real voids, discontinuities and outliers instead of drawing artificial connecting washes.
- Choose a default that is stable between print and screen; include `normalization = count|sqrt|log` with transparent reporting because tone curves change how perceived abundance looks.
- A halo can be Gaussian-blurred, but must be labelled **visual density aid only**. It is not a phylogenetic confidence interval, a spatial dispersal model or ecological population prevalence.

**Visual layer order:**
1. white/transparent canvas;
2. derived species/group cloud underlay;
3. derived density and/or tiny real tip markers;
4. faint **all-original-edge** branch collection;
5. darker exact selected connecting subtree;
6. selected genome point markers and optional exact reference neighbours;
7. group/cloud labels (collision-aware);
8. selected genome labels with leader lines;
9. optional inset/zoom panels;
10. captions, legend, scale/provenance note.

For hybrid figures, *only* the cloud grid is rasterised. Edges, markers, labels and scale bars remain native editable paths/text in SVG/PDF.

## Species and cloud labels

- Semantics always follow a metadata column, **not** inferred proximity in XY.
- Partition each group into actual connected subtrees or spatial components before choosing labels; metadata species is not automatically monophyletic.
- Choose actual density modes/medoids for labels, then move label boxes (never genomes) into nearby negative space.
- Detect collisions with focal labels, selected segments, other cloud labels and axes/crops. Suppress or use an external legend when uncertain.
- Supports `none`, `species`, `group`, `lineage`, `custom` with explicit metadata key and provenance.

## Export, audit, reproducibility

`RunManifest` must include input SHA-256, selection, exact tip/reference/edge counts, graph split checksum, layout name/params, original vs drawn length errors, cloud kernel/weight/bandwidth/alpha/normalisation/resolution, taxonomy/palette mapping and source version, label-placement policy, zoom bounds, package/dependency versions, output size/dpi/format, SHA-256 of each output and warning list.

Retain original vector path/text editability. Warn clearly when SVG/PDF embeds a raster alpha wash; optionally ship its independent transparent PNG/PSD-like asset for visual editing without implying the complete PDF is pure vector.

CI must run against heterogeneous fixtures, polytomies, zero-length branches, large outliers and taxonomic non-monophyly. Golden image checks may be supplementary, **never** a replacement for tree-structure tests.

## Implementation seam / migration

- **Step A:** wrap existing TreeGraph, Layout and selection in immutable interfaces; move **no algorithms** yet; keep old module public imports working.
- **Step B:** add `RenderScene` and a minimal `MatplotlibBackend`; compare a legacy preset PNG/SVG/PDF and provenance against current output.
- **Step C:** add the native cloud point/density/wash engine and explicit presets. Existing `soft_cloud` stays available and is labelled legacy until migrated.
- **Step D:** add semantic cloud labels and deterministic collision rules.
- **Step E:** add optional zoom/multi-panel composition and production-quality exports/benchmarks.
- **Step F:** add `phylocloud render` while retaining `plot` as alias with deprecation warning only in a planned major release.

## Performance and operational requirements

Start with a 6,445-tip (~11,389-edge for the real GETcampy source) regression, then benchmark 25k and 50k-tip trees. Avoid building an `N x N` pairwise-distance table, repeated recursive `get_terminals()` on every node or keeping one image per tip. Use batch line collections and bounded raster grid resolution. Measure time and memory per stage and save summaries in CI/benchmark output. Refuse unreasonably oversized allocations with a clear error.

## Security/data stewardship

The real GETcampy Newick, clinical/sample metadata and original hand-drawn photograph are **not** part of the public GitHub repository. Synthetic fixtures and machine-generated example plots are safe to publish only when clearly marked synthetic. Never upload unpublished study-derived files without explicit permission.

## Architecture decisions to document as ADRs

1. Full undirected original tree is immutable after parsing.
2. Foreground = exact graph-minimal connecting subtree.
3. Density field is an annotation derived from plotted reference geometry, not a second phylogeny.
4. Hybrid vector/tree + raster/underlay export is permitted only with provenance.
5. Semantically labelled clouds must not imply false monophyly.

See [ROADMAP.md](ROADMAP.md) for delivery sequence and acceptance gates.
