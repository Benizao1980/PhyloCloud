from math import hypot
import pytest
from phylocloud.geometry import TreeGraph, equal_arc_layout, connecting_edges, edge_taxa
from phylocloud.synthetic import make_demo


def tree_from_text(tmp_path, text):
    f=tmp_path/'t.nwk';f.write_text(text)
    return TreeGraph.from_newick(f)


def test_preserve_every_original_edge_and_length(tmp_path):
    graph=tree_from_text(tmp_path,'((A:1,B:2):3,((C:4,D:5):6,E:7):8,F:9);')
    layout=equal_arc_layout(graph,14)
    assert len(layout.coordinates)==len(graph.adjacency)
    assert len(layout.edges)==len(graph.adjacency)-1
    for p,c,expected in layout.edges:
        distance=hypot(layout.coordinates[p][0]-layout.coordinates[c][0],
                       layout.coordinates[p][1]-layout.coordinates[c][1])
        assert distance==pytest.approx(expected)


def test_minimal_foreground_exact_original_edges(tmp_path):
    graph=tree_from_text(tmp_path,'((A:1,B:2):3,(C:4,D:5):6,(E:7,F:8):9);')
    layout=equal_arc_layout(graph)
    selected=connecting_edges(graph,['A','B'])
    assert selected.issubset({frozenset((p,c)) for p,c,_ in layout.edges})
    assert len(selected)==2
    selected3=connecting_edges(graph,['A','B','F'])
    assert selected < selected3
    assert all(graph.tips[n] in set().union(*selected3) for n in ['A','B','F'])


def test_ids_and_missing_lengths_rejected(tmp_path):
    g=tree_from_text(tmp_path,'((A:1,B:2):3,C:1,D:2);')
    with pytest.raises(ValueError,match='absent'):
        connecting_edges(g,['A','not_on_tree'])
    with pytest.raises(ValueError,match='unique'):
        connecting_edges(g,['A','A'])
    with pytest.raises(ValueError,match='Missing branch length'):
        tree_from_text(tmp_path,'((A:1,B):2,C:2);')


def test_deterministic_synthetic_tree_and_layout(tmp_path):
    a=make_demo(tmp_path/'one',seed=47,reference_count=60)
    b=make_demo(tmp_path/'two',seed=47,reference_count=60)
    assert a['tree'].read_bytes()==b['tree'].read_bytes()
    graph=TreeGraph.from_newick(a['tree'])
    assert len(graph.tips)==69
    la=equal_arc_layout(graph,10)
    lb=equal_arc_layout(graph,10)
    assert [la.coordinates[x] for x in la.coordinates]==[lb.coordinates[x] for x in lb.coordinates]


def test_taxonomy_pure_vs_mixed(tmp_path):
    g=tree_from_text(tmp_path,'(((A:1,C:1):1,B:1):1,(D:1,E:1):1,F:1);')
    layout=equal_arc_layout(g)
    tax=edge_taxa(layout,g,{'A':'species1','B':'species1','C':'species2','D':'species3','E':'species3','F':'species4'})
    assert 'species1' in tax.values()
    assert 'species2' in tax.values()
    assert None in tax.values()
