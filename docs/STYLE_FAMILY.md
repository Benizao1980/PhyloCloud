# Native visual style family

**Status:** agreed product direction / implementation specification, not yet integrated into the `phylocloud` CLI.

The three experimental local GETcampy style studies (`Cloud`, `River`, `Constellation`) are exploratory **Python/software** renderings based on the real source tree. They are not the AI-generated concept images and do not prove that these modes are available in the installed application. `Canopy` is proposed for the next real-data prototype. Do not commit unpublished real-tree data or manuscript plots without permission.

## Four visual motifs

| Motif | Status and priority | Scientific data-driven visual treatment | Primary use |
| --- | --- | --- | --- |
| **Cloud** | **Default / implement first** | Fine reference branches, terminal-position and/or true-edge density splats, soft overlapping metadata-coloured washes | Main manuscripts, grants, project site |
| **Constellation** | **Alternative / implement second** | Exact reference tip coordinates as luminous points with fine original connecting edges and a distinct highlighted focal subtree; optionally dark canvas | Talks, posters, digital interactions |
| **River** | **Experimental** | Soft graduated strokes, halos and line collections following **only original edges**; thickness represents styling or explicitly defined density measure, never invented flow | Experimental visual communication |
| **Canopy** | **New prototype / implement after Cloud** | Ultra-fine original branches like twigs, with soft translucent foliage-like species/group density **at true branch and tip locations**; no freehand leaves or invented clades | Editorial manuscripts and visuals close to hand sketch |

Each motif must display **every original tip/edge**, the same unmodified topology and edge lengths, and the exact minimum connecting original-edge subtree for selected genomes, from **one immutable LayoutMap**. Themes change **appearance**, not evolutionary structure. Any apparent direction or “flow” in River does **not** establish transmission, ancestral directionality, migration or gene flow. Canopy “foliage” is a data-derived density texture, **not** inferred biological foliage or a new leaf dataset.

## Group colour and labels — shared across all motifs

```yaml
cloud:
  group_by: species       # default; any supplied metadata column permitted
  label_by: same          # broad labels match the selected grouping
  palette: ben-style:getcampy.species
```

The category mapping is resolved **before** drawing the motif. Cloud, River, Constellation and Canopy must share exactly the same category-to-colour mapping and text labels for the same inputs. The palette can be user-specified, with exact category overrides. Where one species or category has several disconnected clades, give each region appropriate labels (or use a legend), **never** paint a false continuous species cloud.

## Orthogonal concerns: `style`, `finish`, and `cloud_mode`

To avoid combinations such as “publication style vs Cloud style” meaning two different things:

- `style`: the **motif** (`cloud`, `constellation`, `river`, `canopy`).
- `finish`: intended print/screen treatment (`publication` = readable and restrained, `hero` = richer atmospheric wash). **Scientific coordinates do not change.**
- `cloud_mode`: explicit rendering implementation where applicable (`points`, `branches+points`, `density-wash`, `hybrid`). In particular, non-Cloud motifs may not require a cloud underlay; `cloud_mode` should not silently override their specific drawing semantics.

These fields and values are **planned API**, not current CLI flags. Preserve existing v0.2 `publication` and `soft_cloud` YAML preset names. The old `cloud-hero` concept maps to **`style=cloud, finish=hero`** in a future clean interface, with an alias for compatibility if previously exposed.

Example intended command (**not yet implemented**):

```bash
phylocloud render --tree tree.nwk --metadata genomes.tsv \
  --selected focal.txt --style canopy --finish publication \
  --cloud-group-by species --cloud-labels same \
  --out outputs/getcampy_canopy
```

## Testable style requirements

1. Render all four styles from **the same ScientificTree, LayoutMap, SelectedEdgeSet and metadata grouping**, changing only style parameters. Record identical edge IDs, zero-length counts, branch lengths and focal tip coordinates.
2. Assert exact species/group assignments, reference counts, label identities, and neutral unassigned colours for every style. No fabricated extra tips, flow paths, connecting edges, foliage nodes or artificial species boundaries.
3. For Canopy, sample real edges deterministically (or use actual tips) and ensure foliage density is bounded by the selected data-driven kernels. Do **not** manufacture decorative branching.
4. River strokes must stay on the original segments or be an explicit display-only stroke treatment. Width/opacity must be explained; do not present it as inferred direction or flux.
5. Compare outputs at manuscript print scale, website scale, dark/light backgrounds and colourblind/grayscale. Ensure foreground MAG connecting paths remain independently readable.
6. Keep SVG/PDF original tree lines and text editable; mark any embedded raster density wash in provenance.
7. The visually appealing AI-generated paintings remain **design references only** and may not be delivered as validated topology-preserving scientific figures.

## Implementation order

**Now:** immutable tree/layout + native Cloud renderer (#5, #6). **Next:** Constellation as a stable alternative; refine experimental River with scientific safeguards; prototype Canopy once the cloud-density engine and branch-sampling architecture are in place. Add semantic group labels (#7) across all motifs. See [ROADMAP.md](ROADMAP.md).

