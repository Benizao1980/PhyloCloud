"""Regression tests for two layout modes, true crop and population fidelity."""
from math import hypot
from pathlib import Path
import hashlib
import json
import pytest
from phylocloud.geometry import TreeGraph, equal_arc_layout, connecting_edges
from phylocloud.data import load_config
from phylocloud.synthetic import make_demo
from phylocloud.cli import run_plot


def fixture(tmp_path):
    return make_demo(tmp_path/'data',seed=47,reference_count=60)


def test_original_edges_and_foreground_conserved(tmp_path):
    paths=fixture(tmp_path)
    graph=TreeGraph.from_newick(paths['tree'])
    expected={frozenset((n,k)) for n,nbrs in graph.adjacency.items() for k,_ in nbrs}
    selected=paths['selected'].read_text().splitlines()
    foreground=connecting_edges(graph,selected)
    for mode in ('tip_count','phylogenetic_spread'):
        lay=equal_arc_layout(graph,rotate_degrees=19,angle_mode=mode)
        assert len(lay.edges)==len(expected)
        assert {frozenset((p,c)) for p,c,_ in lay.edges}==expected
        for p,c,length in lay.edges:
            assert hypot(lay.coordinates[p][0]-lay.coordinates[c][0],
                         lay.coordinates[p][1]-lay.coordinates[c][1])==pytest.approx(length,abs=1e-12)
        assert foreground <= expected


def test_zero_length_polytomies(tmp_path):
    nwk=tmp_path/'polytomy.nwk'
    nwk.write_text('((A:0,B:0,C:0):0,D:0.1,E:0.5);')
    graph=TreeGraph.from_newick(nwk)
    for mode in ('tip_count','phylogenetic_spread'):
        lay=equal_arc_layout(graph,angle_mode=mode)
        assert len(lay.edges)==len(graph.adjacency)-1
        for p,c,length in lay.edges:
            if length==0:
                assert lay.coordinates[p]==lay.coordinates[c]


def test_not_mislabelled_equal_daylight(tmp_path):
    graph=TreeGraph.from_newick(fixture(tmp_path)['tree'])
    with pytest.raises(ValueError,match='angle_mode'):
        equal_arc_layout(graph,angle_mode='equal_daylight')


def test_preset_override(tmp_path):
    cfg=load_config(None)
    assert cfg['style']['preset']=='publication'
    assert not cfg['style']['density_overlay']
    f=tmp_path/'soft.yml'
    f.write_text('style:\n  preset: soft_cloud\n  reference_alpha: 0.12\n')
    cfg=load_config(f)
    assert cfg['style']['density_overlay']
    assert cfg['style']['reference_alpha']==0.12
    f.write_text('style:\n  preset: unknown\n')
    with pytest.raises(ValueError,match='Unknown style preset'):
        load_config(f)


def test_provenance_and_editable_edges(tmp_path):
    paths=fixture(tmp_path)
    cfg=tmp_path/'density.yml'
    cfg.write_text('layout:\n  angle_mode: phylogenetic_spread\nstyle:\n  preset: soft_cloud\nexport:\n  dpi: 150\n')
    dest=tmp_path/'out'/'figure'
    result=run_plot(paths['tree'],paths['metadata'],paths['selected'],cfg,dest)
    assert result['validation']['all_original_edges_retained']
    assert result['validation']['max_absolute_edge_length_error'] < 1e-10
    assert result['validation']['original_edges_retained']==result['tree_edges']
    assert result['input_sha256']['tree']==hashlib.sha256(Path(paths['tree']).read_bytes()).hexdigest()
    svg=dest.with_suffix('.svg').read_text()
    assert '<path' in svg
    assert '<image' in svg or 'image/png' in svg
    assert json.loads(dest.with_suffix('.provenance.json').read_text())['selected']==9


def test_crop_reference_and_scale_bar(tmp_path):
    paths=fixture(tmp_path)
    graph=TreeGraph.from_newick(paths['tree'])
    reference=next(name for name in graph.tips if name.startswith('REF_'))
    cfg=tmp_path/'zoom.yml'
    cfg.write_text('style:\n  preset: publication\n  zoom_to_selected: true\n'
                   '  context_reference_ids:\n    - '+reference+'\n'
                   '  scale_bar:\n    length: 0.01\n    units: subs/site\n'
                   'export:\n  dpi: 150\n')
    dest=tmp_path/'zoom'
    result=run_plot(paths['tree'],paths['metadata'],paths['selected'],cfg,dest)
    assert result['geometric_zoom']
    assert result['context_references']==1
    assert result['reference_genomes']==60
    assert result['tree_edges']==len(graph.adjacency)-1
    assert result['validation']['max_absolute_edge_length_error']<1e-10
    assert dest.with_suffix('.svg').exists()
