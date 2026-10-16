"""Adversarial benchmark semantics, independent of renderer appearance."""
from collections import Counter, defaultdict
from math import dist

from Bio import Phylo
import pytest

from phylocloud.benchmark import make_structure_benchmark
from phylocloud.data import load_metadata, load_selected
from phylocloud.geometry import TreeGraph, equal_arc_layout, connecting_edges


def test_6500_fixture_is_mixed_uneven_reproducible_and_difficult(tmp_path):
    paths=make_structure_benchmark(tmp_path/'first')
    repeat=make_structure_benchmark(tmp_path/'repeat')
    for key in paths:
        assert paths[key].read_bytes()==repeat[key].read_bytes()
    with pytest.raises(FileExistsError):
        make_structure_benchmark(tmp_path/'first')
    meta=load_metadata(paths['metadata']); selected=load_selected(paths['selected'])
    tree=Phylo.read(paths['tree'],'newick'); graph=TreeGraph.from_newick(paths['tree'])
    assert len(graph.tips)==len(meta)==6500 and len(selected)==12
    assert all(meta[n]['group']=='selected' for n in selected)
    refs={n:r for n,r in meta.items() if r['group']=='reference'}
    assert len(refs)==6488
    sizes=Counter(r['species'] for r in refs.values())
    assert len(sizes)==8 and max(sizes.values())/min(sizes.values())>20
    populations=defaultdict(set)
    for row in refs.values(): populations[row['population']].add(row['species'])
    assert sum(len(s)>1 for s in populations.values())>=20
    # At least six categories are explicitly nonmonophyletic in source topology.
    polyphyletic=0
    for species in sizes:
        tips=[n for n,r in meta.items() if r['species']==species]
        ancestor=tree.common_ancestor(tips)
        polyphyletic+=any(meta[t.name]['species']!=species for t in ancestor.get_terminals())
    assert polyphyletic>=6
    layout=equal_arc_layout(graph,19)
    assert len(layout.edges)==len(graph.adjacency)-1
    original={frozenset((n,k)):length for n,adj in graph.adjacency.items() for k,length in adj}
    assert {frozenset((a,b)):length for a,b,length in layout.edges}==original
    lengths=list(original.values())
    assert sum(x==0 for x in lengths)>500
    assert max(lengths)/min(x for x in lengths if x)>1000
    assert all(abs(dist(layout.coordinates[a],layout.coordinates[b])-length)<1e-10
               for a,b,length in layout.edges)
    assert len({layout.coordinates[graph.tips[n]] for n in selected[:4]})==1
    assert connecting_edges(graph,selected)<=original.keys()
    assert tree.distance(selected[0],selected[-1])>tree.distance(selected[0],selected[4])


def test_small_fixture_remains_bounded_and_complete(tmp_path):
    paths=make_structure_benchmark(tmp_path/'small',tip_count=240)
    assert len(TreeGraph.from_newick(paths['tree']).tips)==240
    assert len(load_selected(paths['selected']))==12
    with pytest.raises(ValueError):
        make_structure_benchmark(tmp_path/'bad',tip_count=100)
