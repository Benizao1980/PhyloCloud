# Architecture and roadmap

## Data flow

```text
Newick + metadata + selected tip IDs + optional YAML
                |
            validate IDs and branch lengths
                |
        undirected full weighted tree
                |
      unrooted equal-arc initial layout
                |
        shared fixed coordinates
           /              \
all original tree edges   exact induced connecting subtree
 (soft background)           (dark foreground)
           \              /
            SVG / PDF / PNG
```

Modules:

- `geometry.py`: Newick as an undirected tree; display-centre choice; equal-arc coordinates; exact original edge selection; species-pure branch classification.
- `data.py`: metadata/config reading; local snapshot of Ben-style semantic colours.
- `render.py`: vector branch collections, reference cloud, selected markers, deterministic labels, exports.
- `synthetic.py`: seeded fictional Newick + metadata fixtures.
- `cli.py`: `phylocloud demo` and `phylocloud plot`.

## Selected branches

We recursively remove terminal vertices not in the selection. The unique remaining edge set is the minimum connecting subtree in an input *tree*. Crucially, unlike highlighting root-to-focal paths, this does not add irrelevant paths toward the arbitrary Newick serialization root. No re-inference, extra nodes, edge contractions or new distances.

## Phases

1. **v0.1 baseline:** deterministic unrooted equal-arc, two visual layers, strict input parser, SVG/PDF/PNG, tests and CI.
2. **v0.2 aesthetic:** benchmark against original sketch; explore equal-daylight branch-angle optimization (preserve every original edge length); better label layout and soft background aesthetics.
3. **GETcampy validation:** apply to 6,436 GTDB reference genomes plus nine MAGs; check metadata mapping, taxonomy and structural integrity; compare against R ape/PHYLIP output; record tree and config hashes.
4. **Generalise:** pluggable palettes, metadata grouping, optional MAG neighbourhood zoom panels, automated scale bar, high-DPI export variants and sensible print presets.
5. **Release:** test distribution build and workflow; tag a prerelease only after code review. GitHub workflow currently creates drafts rather than publishing blindly.

## Engineering constraints

- For 6,445 tips, the full tree has approximately 12,887 edges (the exact count depends on input root representation and multifurcations). Plotting is O(V+E) before Matplotlib export.
- Changing branch direction with a topology-preserving layout is acceptable; changing edge length, topology or selected membership without disclosure is not.
- The input Newick root is a serialization/display detail, not evidence of biological rooting.
- Branch support and GTDB taxonomy should be carefully distinguished from inferred branch lengths, ANI and source-attribution results.
