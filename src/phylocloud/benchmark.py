"""Deterministic adversarial tree fixture, not simulated or inferred biology."""
from __future__ import annotations

from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import random

from Bio import Phylo
from Bio.Phylo.Newick import Clade, Tree


def make_structure_benchmark(output_dir: str | Path, seed: int = 650047,
                             tip_count: int = 6500):
    """Generate one nested, uneven tree before assigning mixed synthetic taxonomy.

    No biological sequences, fitted evolutionary model, taxonomy rearrangement or
    layout optimization is involved. Selected tips are existing generated tips.
    Refuse to overwrite a prior fixture. The small-size option serves CI only.
    """
    if tip_count < 240:
        raise ValueError('Structure benchmark requires at least 240 tips')
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=False)
    rng = random.Random(seed)
    # Heavy-tailed population sizes, independent of the eight taxonomic labels.
    weights = [1200, 950, 780, 650, 500, 390, 310, 260, 220, 180, 150, 125,
               100, 85, 70, 60, 52, 45, 38, 32, 27, 23, 20, 17, 14, 11, 9, 7]
    sizes = [max(4, int(tip_count*w/sum(weights))) for w in weights]
    sizes[0] += tip_count-sum(sizes)
    rows = {}; blocks = []; local_tips = []; serial = 0
    categories = ['Synthetic species '+c for c in 'ABCDEFGH']
    # Repeated labels across distant blocks; far from one-species/one-arm.
    dominant = [0, 0, 1, 0, 2, 1, 0, 3, 2, 0, 4, 1, 0, 5, 2, 0,
                6, 1, 0, 3, 7, 0, 2, 4, 0, 5, 6, 7]

    def edge(scale, terminal=False):
        if rng.random() < .075:
            return 0.
        return max(1e-6, min(1.8, rng.lognormvariate(-5.0 if terminal else -3.9, .9 if terminal else .8)*scale))

    def grow(tips, scale):
        if len(tips) == 1:
            tips[0].branch_length = edge(scale, terminal=True)
            return tips[0]
        # Variable asymmetric splits, including short ladder-like stretches.
        frac = rng.betavariate(.7, .7)
        cut = max(1, min(len(tips)-1, int(len(tips)*frac)))
        return Clade(branch_length=edge(scale),
                     clades=[grow(tips[:cut], scale), grow(tips[cut:], scale)])

    for block, size in enumerate(sizes):
        tips = []
        for j in range(size):
            serial += 1
            name = f'REF_{serial:05d}'
            # Runs of an alternative label create small homogeneous subtrees;
            # isolated interspersed tips stress mixed ancestral-edge treatment.
            category = dominant[block]
            if j % 71 < 12:
                category = (category+1+block % 3) % 8
            if rng.random() < .025:
                category = rng.randrange(8)
            rows[name] = dict(genome_id=name, species=categories[category],
                              source='synthetic reference', label=name,
                              population=f'P{block+1:02d}', group='reference', case='')
            tips.append(Clade(name=name))
        local_tips.append(tips)
        scale = [.12, .40, 1.4, .25, .75][block % 5]
        if block == 0:
            # A real zero-length polytomy in this synthetic input. Labels must
            # disclose co-location rather than silently jitter these genomes.
            coincident = Clade(branch_length=.004,
                               clades=[Clade(name=t.name, branch_length=0.) for t in tips[:4]])
            subtree = Clade(branch_length=.03,
                            clades=[coincident, grow(tips[4:], scale)])
            local_tips[0][:4] = coincident.clades
        else:
            subtree = grow(tips, scale)
        subtree.branch_length = [.06, .14, .035, .23, .09][block % 5]
        blocks.append(subtree)

    # Nested hierarchy, no species-specific root spokes. Shuffle block order
    # before joining: category identity has no role in tree construction.
    rng.shuffle(blocks)
    def join(nodes, depth=0):
        if len(nodes) == 1:
            return nodes[0]
        cut = max(1, min(len(nodes)-1, int(len(nodes)*rng.uniform(.22, .78))))
        return Clade(branch_length=rng.uniform(.05, .22)*(1.3 if depth<2 else 1.),
                     clades=[join(nodes[:cut], depth+1), join(nodes[cut:], depth+1)])
    root = join(blocks)
    # A sparse long terminal tests honest whitespace/framing, not truncation.
    local_tips[-1][-1].branch_length = 1.25
    picks = [(t, 'coincident zero-length tips') for t in local_tips[0][:4]]
    for block, offset, case in [(0, -1, 'dense population'), (1, 0, 'dense distant population'),
                                (3, -1, 'short branch neighbourhood'), (6, 0, 'mixed taxonomy'),
                                (12, -1, 'small population'), (20, 0, 'rare category'),
                                (26, -1, 'sparse lineage'), (27, -1, 'long terminal outlier')]:
        picks.append((local_tips[block][offset], case))
    selected = []
    for i, (tip, case) in enumerate(picks, 1):
        old = tip.name; tip.name = f'FOCAL_{i:02d}'; selected.append(tip.name)
        row = rows.pop(old)
        row.update(genome_id=tip.name, source='synthetic focal', group='selected',
                   label=f'F{i:02d}', case=case)
        rows[tip.name] = row
    paths = {key:out/name for key, name in [('tree','tree.nwk'), ('metadata','metadata.tsv'),
                                          ('selected','selected.txt')]}
    Phylo.write(Tree(root=root, rooted=False), str(paths['tree']), 'newick',
                format_branch_length='%1.10f')
    with paths['metadata'].open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['genome_id','species','source','label',
                                                   'population','group','case'], delimiter='\t')
        writer.writeheader(); writer.writerows(rows.values())
    paths['selected'].write_text('\n'.join(selected)+'\n')
    manifest = dict(kind='synthetic adversarial visualization fixture; not biological validation',
                    seed=seed, tips=tip_count, references=tip_count-12, selected=selected,
                    population_sizes=sizes,
                    reference_categories=dict(Counter(r['species'] for r in rows.values()
                                                      if r['group']=='reference')),
                    focal_cases={r['genome_id']:r['case'] for r in rows.values() if r['case']},
                    input_sha256={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()})
    (out/'fixture.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return paths
