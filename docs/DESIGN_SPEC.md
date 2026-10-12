# PhyloCloud — product and visual design specification

**Status:** approved design direction; **not** a claim that the native renderer already achieves the concept-art quality.
**Last updated:** 2026-10-12
**Owner project:** [PhyloCloud](https://github.com/Benizao1980/PhyloCloud).

## Product statement

> PhyloCloud is an open-source tool for rendering full phylogenies as publication-quality diversity clouds, combining a scientifically faithful unrooted tree layout with soft, density-based reference visualisation and an exact highlighted subtree for selected genomes.

The design benchmark is the stronger atmospheric cloud concepts developed from the original GETcampy hand drawing. **Those concepts were generated as illustrations; they are not validated exports from PhyloCloud.** We will reproduce their appearance computationally from the actual tree, not embed them, copy their invented lines, or claim that they preserve topology.

Success = a user can provide a full Newick, reference metadata and a short selected-tip list and produce a visually distinctive, scientifically auditable figure without manual post-processing.

## Scientific contract (mandatory)

See [SCIENTIFIC_INVARIANTS.md](SCIENTIFIC_INVARIANTS.md). Specifically:

1. **One inferred tree, one shared layout** for both layers. Unrooted display orientation is not a claim about ancestral rooting.
2. Preserve all original tip IDs, unrooted graph edges/splits, original branch lengths, zero-length edges, sampled clade sizes and path-based **patristic** distances. A 2D Euclidean distance between arbitrary tips is *not* a patristic distance.
3. The focal tree is the **minimal connected set of original edges** spanning selected tips. No MAG-only inference or separately positioned overlay.
4. The cloud is an *additional visual field* derived exclusively from actual reference tip/edge positions and metadata. No decorative fabricated branching or manual manipulation of genome coordinates.
5. Sampled genome density is **sampling density**, not natural abundance or prevalence. An image blur is neither an uncertainty region nor a taxonomic boundary.
6. Annotation and colour come from exact user metadata; preserve GTDB naming. Labels for paraphyletic or disjoint species must not imply monophyly.
7. Topology-preserving rotations/angle optimisation are allowed; branch-length transformations, filtering or overlap mitigation that move true tree coordinates require an explicit separate display mode, disclosure, and invariant tests.

## Native visual language

- **Cloud, not fan diagram:** a legible network of ultra-fine, semitransparent reference edges surrounded by continuous, overlapping, *coordinate-derived* soft density fields.
- **Population structure is visible:** preserve disjoint lineages, long outliers, genuine voids, and unevenly sampled clades even if the image looks less symmetrical.
- **Foreground structure:** warm dark-ink original connecting edges, selected genome markers with subtle outlines, direct uncluttered labels.
- **Typography:** clean, modest hierarchy using Arial/Helvetica/DejaVu Sans; no false precision, oversize titles, default decorative bands or intrusive legend boxes.
- **Ben-style palette:** source stable semantic names from the Ben-style master/preset scheme (sage, powder blue, dusty pink, lavender, mustard, teal, stone, ink). Preserve project-specific category mappings across figures.
- **Whites and transparent overlap:** lightly textured only when generated from data; paper white is default. Include grayscale and colour-blind-aware review.
- **Aesthetic evaluation:** compare against the hand sketch and concept designs in a *separate design review*. These are style references, not authoritative branch-coordinate maps.

## Default cloud taxonomy, colours and broad labels

**Explicit default: \`cloud.group_by = species\` and \`cloud.label_by = same\`**, where \`same\` means “use the cloud's grouping column”. For GETcampy, major cloud regions therefore use the **species recorded in metadata** for both their soft wash colour and their broad, unobtrusive label (for example, *Campylobacter infans*, *Campylobacter_D jejuni*, *Campylobacter coli*). Never assign species solely from tree position or copy labels/colour regions from image-generation concepts.

**The user may override the grouping:** \`cloud.group_by = lineage\`, \`source\`, \`host\`, \`country\`, \`clonal_complex\`, or any exact metadata column. Cloud labels follow the selected grouping by default. Advanced users may explicitly set \`cloud.label_by\` to another column, \`none\`, or select a custom label field, but this must not imply that labels and colours are the same if they aren't.

**The user may override the palette:** \`cloud.palette\` chooses a semantic palette (initial default \`ben-style:getcampy.species\` when applicable) and \`cloud.colours\` optionally maps exact metadata values to Ben-style colour names or hex codes. The palette and map are presentation-only; they cannot alter the graph, selected subtree or metadata identities. Colour mappings are a data-driven **lookup**, not an attempt to construct visually neat monophyletic colour islands.

**Unassigned/unknown values** receive a neutral cloud colour and an explicit “Unassigned” label/legend entry where appropriate. A metadata group occupying genuinely separated clades may produce several disjoint washes and multiple labels or an external legend; *never invent a merged species cloud* to match the sketch. No false membership, prevalence estimates or phylogenetic confidence regions.

### Proposed future YAML schema (not runnable with v0.2)

\`\`\`yaml
cloud:
  group_by: species             # default; any validated metadata column
  label_by: same                # default; same grouping as the cloud colour
  palette: ben-style:getcampy.species
  colours:                     # optional exact group overrides
    "Campylobacter infans": sage
    "Campylobacter_D jejuni": powder_blue
  label_style:
    min_references: 12         # hide labels for tiny groups; keep all tree data
    italicise_species: true
\`\`\`

To colour and label the same tree by lineage, a future user only changes \`group_by: lineage\` (and optionally a lineage-specific palette); \`label_by: same\` follows automatically. See [CURRENT_CLI.md](CURRENT_CLI.md) for the **existing** commands/inputs and proposed future calls.

## Visual motifs and figure finishes

**The four motifs are independent visualizations of the exact same scientific geometry; see [STYLE_FAMILY.md](STYLE_FAMILY.md).**

| Motif | Priority | What changes visually |
| --- | --- | --- |
| \`cloud\` | **Default** | Soft, continuous, data-derived species-coloured diversity washes beneath original reference branches |
| \`constellation\` | Alternative | Discrete reference-tip stars with fine original edges on a light or dark background |
| \`river\` | **Experimental** | Faint flow-like styling of the *original* branches; never implied migration/gene flow |
| \`canopy\` | Next prototype | Fine botanical branch texture and soft density/foliage centred on actual tips and original branch segments |

**Finishes are separate from motifs:** \`publication\` (legible, restrained) and \`hero\` (more atmospheric). For example, a \`cloud\` figure can use either finish without moving genomes. Shared grouping defaults are \`cloud.group_by: species\` and \`cloud.label_by: same\`; user-supplied columns and palettes are supported by the **planned** engine.

**Current status:** \`publication\` and \`soft_cloud\` are the existing v0.2 preset values. None of the four new named motifs is integrated as a selectable PhyloCloud CLI style yet; real-tree Cloud/River/Constellation local style experiments do not change the public CLI. The previous \`cloud-hero\` design corresponds to a future \`cloud\` motif with \`hero\` finish.

## Cloud visualisation modes

1. **`points`:** vector points exactly at actual reference tip coordinates. Deterministic size/alpha. Duplicated/zero-length coordinates remain coincident; they are not jittered without a separately labelled diagnostic mode.
2. **`branches+points`:** all original vector edges at low opacity plus tip points; no fake topology.
3. **`density-wash`:** smooth field estimated over actual reference tips and, optionally, points sampled deterministically on original segments; metadata strata may yield separate colour fields.
4. **`hybrid`:** vector tree + points/text with transparent, bounded-resolution raster density underlay. The underlay is visual; only the geometric elements are individually editable.

The density algorithm must expose and record its **source** (tips / branches / both), sample weights (each reference tip once by default; if branch samples are used, specify length-normalisation), bandwidth, kernel, alpha mapping, colour blending, clipping bounds, raster resolution and seed if sampling is stochastic. Default generation should be deterministic.

The wash should become stronger through principled kernel bandwidth, opacity and compositing — never by moving genomes or drawing invented branches. Document differences between equal-weight genomes and length-weighted edge sampling, especially when reference coverage is uneven.

## Population / cloud labels

By default, cloud labels use **the same metadata category as cloud colour** (`cloud.group_by: species`, `cloud.label_by: same`). Alternative metadata columns are user-configurable. Groups are **metadata categories**, not necessarily monophyletic clades.

- For a genuinely connected/monophyletic group, anchor near a weighted medoid or a suitable density mode. Label only if there is enough whitespace.
- For multiple disjoint components, label each supported region with a disambiguated suffix or create a legend; **never draw one encompassing silhouette that falsely suggests a single clade**.
- Place cloud labels below focal sample text but above background haze. Use light text halos and short leader lines if needed; avoid masking important nodes.
- Labels for selected MAGs are placed independently of fixed tip coordinates, with deterministic collision resolution and leader lines to the **exact tips**.
- Optional main-group count and nearest-reference annotations must be computed or read from validated inputs, not inferred from picture position.

## Panels and composition

- Default: main full-tree cloud, minimalist legend, optional branch-length scale bar.
- Optional: `geometric-zoom` panels using the original coordinate map and exactly identified focal and context tips. Do not recompute a new tree layout inside a zoom.
- Additional optional panels: selected-genome counts by species, nearest *tree*-neighbour summary, host/source metadata, separate species neighbourhoods, explanatory inset. Report the relevant measurement/criterion (tree distance is not ANI).
- Layout presets for one-column, two-column, landscape presentation and poster/hero. A multi-panel figure uses a common provenance manifest and explicit crop bounds.

## Inputs and outputs

**Inputs:** unrooted or rooted-serialization Newick with finite non-negative lengths; exact tip IDs; metadata TSV/CSV with `genome_id` plus the selected category column (default `species`); selected-tip text file; optional declarative YAML style/layout/panel file. **Today** the v0.2 loader always requires `genome_id` and `species`, even if custom metadata are present; a future schema revision should require `genome_id` and only the configured grouping columns. Reject ambiguous/missing selection IDs and duplicate metadata IDs.

**Outputs:** high-resolution PNG, native SVG/PDF geometry and labels (with optional embedded density raster), and `*.provenance.json` recording tool version, input hashes, full/selected/reference counts, exact original-edge audit, layout parameters, cloud algorithm/parameters, semantic palette names and resolutions, warnings, and export settings.

Do **not** call hybrid SVG/PDF “fully vector” when the density underlay is raster. Offer pure-vector alternatives. Preserve original proprietary/unpublished data outside the public repository.

## Quality gates / acceptance criteria

**Scientific (automated; no exceptions)**

- Every input tip and original edge is accounted for; all zero-length edges retained and all unrooted splits unchanged.
- Edge segment lengths match original edge lengths within numerical tolerance; check pairwise path lengths on deterministic diverse sample pairs.
- Every foreground edge is an original full-tree edge, and no reference edge is silently dropped.
- Full metadata and selection audit, exact source counts, taxonomic integrity, missing category warnings.
- Repeat run with same data/config produces same cloud image within defined deterministic tolerance and matching provenance.
- Density origin points can be traced to exact reference IDs or original edges, and no cloud changes selected coordinates.

**Visual (review + measurable checks)**

- Reference population is legible at print dimensions and hero dimensions; transparent cloud is richer than v0.2 but doesn't hide dark selected topology.
- No substantial collisions among foreground/cloud labels, clipping, incorrect overlapping tips or misleading species regions.
- Cloud silhouettes may be irregular; preserve real gaps and outliers. Test heterogeneous/mixed-taxon trees and dense zero-length clades.
- Verify SVG/PDF paths and text remain editable; clearly identify any embedded raster density field.
- Side-by-side review with concept-art target, including grayscale and colour accessibility check.

## CLI: desired interface (future)

```bash
phylocloud render \
  --tree tree.nwk --metadata metadata.tsv --selected focal_ids.txt \
  --style cloud --cloud-mode hybrid \
  --cloud-labels species --species-column species \
  --label-field label --out outputs/my_cloud
```

Planned: `--style cloud|constellation|river|canopy` and `--finish publication|hero`, plus `--cloud-mode points|branches+points|density-wash|hybrid`, `--cloud-labels none|species|group|lineage|custom`, `--cloud-label-column`, `--zoom-panel`, and cloud density/bandwidth/alpha controls.

**Current stable prototype commands remain `phylocloud plot` and `phylocloud demo`.** A compatibility alias should precede any CLI rename; do not silently break users.

## Explicit non-goals for now

No phylogenetic inference, ANI inference, prevalence estimation, hidden species collapsing, automatic biological rooting, general image generation, or unsupported assertion that decorative clouds are evolutionary confidence regions. Design illustrations are **not** scientific outputs.

## Links

- [Planned code architecture](ARCHITECTURE.md)
- [Implementation milestones](ROADMAP.md)
- [Scientific invariant tests](SCIENTIFIC_INVARIANTS.md)
- [Four native visual motifs and validation requirements](STYLE_FAMILY.md)
- [Existing v0.2 analysis notes](V02_LAYOUT_REVIEW.md)
