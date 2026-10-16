"""Measured label packing and invariant fixed-canvas publication exports."""
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
from PIL import Image
import pytest

from phylocloud.benchmark import make_structure_benchmark
from phylocloud.cli import run_plot
from phylocloud.composition import _pack_vertical
from phylocloud.geometry import TreeGraph, equal_arc_layout, connecting_edges


def test_measured_vertical_pack_respects_order_gaps_and_canvas():
    heights=[24,12,16,12]
    ys=_pack_vertical([50,50,51,500],heights,0,100,4)
    assert ys[0]>=heights[0]/2 and ys[-1]<=100-heights[-1]/2
    for i in range(1,len(ys)):
        assert ys[i]-ys[i-1]>=(heights[i]+heights[i-1])/2+4
    assert _pack_vertical([],[],0,100,4)==[]
    with pytest.raises(ValueError,match='increase export height'):
        _pack_vertical([0,0],[60,60],0,100,4)


@pytest.mark.parametrize('preset',['publication','cloud','canopy','soft_cloud'])
def test_publication_composition_discloses_coincident_tips_and_exact_canvas(tmp_path,preset):
    p=make_structure_benchmark(tmp_path/'inputs',tip_count=240)
    cfg=tmp_path/'config.yml'
    cfg.write_text(f'style:\n  preset: {preset}\n  composition: publication\n'
                   '  title: Structure comparison\ncloud:\n  resolution: 128\n'
                   'export:\n  width_inches: 8\n  height_inches: 8\n  dpi: 100\n')
    stem=tmp_path/'figure'
    report=run_plot(**p,config=cfg,out=stem)
    a=report['annotation_layout']
    assert a['text_box_overlaps']==a['clipped_text_boxes']==0
    assert len(a['label_groups'])==9
    assert sorted(n for g in a['label_groups'] for n in g['ids'])==p['selected'].read_text().splitlines()
    together=next(g for g in a['label_groups'] if len(g['ids'])==4)
    assert 'coincident tips' in together['text']
    assert report['native_cloud_labels']==[]  # taxonomy is a separate counted key
    assert sum(a['reference_group_counts'].values())==228
    assert report['validation']['all_original_edges_retained']
    assert report['validation']['max_absolute_edge_length_error']<1e-10
    graph=TreeGraph.from_newick(p['tree']); layout=equal_arc_layout(graph,10)
    assert together['anchor_xy']==list(layout.coordinates[graph.tips['FOCAL_01']])
    svg=ET.parse(stem.with_suffix('.svg')); root=svg.getroot()
    assert root.get('width')=='576pt' and root.get('height')=='576pt'
    ns={'s':'http://www.w3.org/2000/svg'}
    for gid,n in [('reference-tree-edges',len(layout.edges)),
                  ('selected-original-edges',len(connecting_edges(graph,p['selected'].read_text().splitlines())))]:
        group=svg.find(f".//s:g[@id='{gid}']",ns)
        assert len(group.findall('s:path',ns))==n
    with Image.open(stem.with_suffix('.png')) as png:
        assert png.size==(800,800)
    assert b'/MediaBox [ 0 0 576 576 ]' in stem.with_suffix('.pdf').read_bytes()
    if preset=='cloud':
        repeat=tmp_path/'repeat'
        run_plot(**p,config=cfg,out=repeat)
        for ext in ('svg','pdf','png'):
            assert stem.with_suffix('.'+ext).read_bytes()==repeat.with_suffix('.'+ext).read_bytes()


def test_long_labels_are_wrapped_without_moving_nodes(tmp_path):
    p=make_structure_benchmark(tmp_path/'inputs',tip_count=240)
    data=p['metadata'].read_text().replace('\tF05\t','\tF05 with a deliberately long descriptive identifier to wrap\t')
    p['metadata'].write_text(data)
    cfg=tmp_path/'cfg.yml'
    cfg.write_text('style:\n  preset: cloud\n  composition: publication\n  title: Wrapped labels\n'
                   'cloud:\n  resolution: 128\nexport:\n  width_inches: 12\n  height_inches: 10\n  dpi: 75\n')
    report=run_plot(**p,config=cfg,out=tmp_path/'wrapped')
    group=next(g for g in report['annotation_layout']['label_groups'] if g['ids']==['FOCAL_05'])
    assert '\n' in group['text']
    assert report['annotation_layout']['text_box_overlaps']==0


def test_insufficient_canvas_fails_explicitly(tmp_path):
    p=make_structure_benchmark(tmp_path/'inputs',tip_count=240)
    cfg=tmp_path/'cfg.yml'
    cfg.write_text('style:\n  composition: publication\nexport:\n  width_inches: 4\n  height_inches: 4\n')
    with pytest.raises(ValueError,match='at least 5 inches'):
        run_plot(**p,config=cfg,out=tmp_path/'bad')
    plt.close('all')


def test_publication_zoom_and_scale_keep_original_full_graph(tmp_path):
    p=make_structure_benchmark(tmp_path/'inputs',tip_count=240)
    p['selected'].write_text('FOCAL_01\nFOCAL_02\nFOCAL_05\n')
    graph=TreeGraph.from_newick(p['tree'])
    reference=next(n for n in graph.tips if n.startswith('REF_'))
    cfg=tmp_path/'cfg.yml'
    cfg.write_text('style:\n  composition: publication\n  zoom_to_selected: true\n'
                   '  title: Coordinate-preserving crop\n  context_reference_ids:\n    - '+reference+'\n'
                   '  scale_bar:\n    length: 0.001\n    units: synthetic units\n'
                   'export:\n  width_inches: 10\n  height_inches: 9\n  dpi: 75\n')
    report=run_plot(**p,config=cfg,out=tmp_path/'zoom')
    assert report['density_camera_policy']=='explicit_selected_crop'
    assert report['tree_edges']==len(graph.adjacency)-1
    assert report['context_references']==1
    assert report['validation']['all_original_edges_retained']
    assert report['annotation_layout']['text_box_overlaps']==0
    assert '0.001 synthetic units' in (tmp_path/'zoom.svg').read_text()
