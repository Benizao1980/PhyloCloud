"""Default metric fidelity and opt-in non-metric graphical length-mode tests."""
import math
import json
import pytest
from phylocloud.cli import run_plot
from phylocloud.geometry import TreeGraph, equal_arc_layout, connecting_edges
from phylocloud.synthetic import make_demo

def sample(tmp_path):
    p=tmp_path/'tree.nwk'
    p.write_text('((A:0,B:0.01):0.02,(C:0.03,D:0.04):0,E:0.06);')
    return TreeGraph.from_newick(p)

def test_default_preserves_branch_lengths_and_zero_edges(tmp_path):
    g=sample(tmp_path); lay=equal_arc_layout(g)
    assert lay.length_mode=='original'
    assert len(lay.edges)==len(g.adjacency)-1
    for a,b,l in lay.edges:
        assert math.dist(lay.coordinates[a],lay.coordinates[b])==pytest.approx(l,abs=1e-12)
        assert lay.display_lengths[frozenset((a,b))]==l

def test_graphic_retains_exact_original_edges_and_selected_subtree(tmp_path):
    g=sample(tmp_path); before=equal_arc_layout(g); after=equal_arc_layout(g,length_mode='graphic')
    assert {(frozenset((a,b)),l) for a,b,l in before.edges}=={(frozenset((a,b)),l) for a,b,l in after.edges}
    assert connecting_edges(g,['A','D']).issubset({frozenset((a,b)) for a,b,_ in after.edges})
    assert any(math.dist(after.coordinates[a],after.coordinates[b])>0 for a,b,l in after.edges if l==0)
    assert all(math.dist(after.coordinates[a],after.coordinates[b])==
               pytest.approx(after.display_lengths[frozenset((a,b))],abs=1e-12)
               for a,b,_ in after.edges)
    with pytest.raises(ValueError,match='length_mode'):
        equal_arc_layout(g,length_mode='invalid')

def test_cli_discloses_display_mode_and_preserves_graph(tmp_path):
    inp=make_demo(tmp_path/'data',seed=19,reference_count=60)
    cfg=tmp_path/'settings.yml'
    cfg.write_text('style:\n  preset: cloud\ncloud:\n  resolution: 128\n  max_density_groups: 3\nexport:\n  width_inches: 7\n  height_inches: 5\n  dpi: 72\n')
    original=run_plot(inp['tree'],inp['metadata'],inp['selected'],cfg,tmp_path/'orig',length_mode='original')
    graphic=run_plot(inp['tree'],inp['metadata'],inp['selected'],cfg,tmp_path/'graphic',length_mode='graphic')
    assert original['validation']['max_absolute_edge_length_error']<1e-10
    assert original['validation']['display_distances_are_evolutionary']
    assert original['display_length_transform'] is None
    assert graphic['validation']['max_absolute_edge_length_error'] is None
    assert not graphic['validation']['display_distances_are_evolutionary']
    assert graphic['validation']['max_absolute_display_length_error']<1e-10
    assert graphic['display_length_transform']['scale']>0
    assert (original['tree_edges'],original['foreground_edges'])==(graphic['tree_edges'],graphic['foreground_edges'])
    assert graphic['reference_genomes']==original['reference_genomes']
    assert 'NON-METRIC GRAPHIC LENGTHS' in (tmp_path/'graphic.svg').read_text()
    assert json.loads((tmp_path/'graphic.provenance.json').read_text())['length_mode']=='graphic'

def test_graphic_rejects_evolutionary_scale_bar(tmp_path):
    inp=make_demo(tmp_path/'data',seed=19,reference_count=60)
    cfg=tmp_path/'settings.yml'
    cfg.write_text('style:\n  scale_bar:\n    length: 0.01\n')
    with pytest.raises(ValueError,match='Scale bars'):
        run_plot(inp['tree'],inp['metadata'],inp['selected'],cfg,tmp_path/'bad',length_mode='graphic')
