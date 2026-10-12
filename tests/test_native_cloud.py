"""Native Cloud/Canopy style regression tests, always using fictional trees."""
import csv
import math
import pytest
from phylocloud.geometry import TreeGraph, equal_arc_layout, connecting_edges
from phylocloud.cloud_layers import (groups_for_references, reference_ids,
                                     compute_cloud_fields)
from phylocloud.synthetic import make_demo
from phylocloud.data import load_config, load_metadata, load_selected
from phylocloud.cli import run_plot


def tiny(tmp_path):
    return make_demo(tmp_path / 'data', seed=17, reference_count=60)


def test_native_groups_keep_all_reference_genomes_and_coordinates(tmp_path):
    p=tiny(tmp_path)
    tree=TreeGraph.from_newick(p['tree'])
    meta=load_metadata(p['metadata'])
    selected=load_selected(p['selected'])
    ids=reference_ids(tree, meta, selected)
    assert len(ids)==60
    groups=groups_for_references(tree,meta,ids,'species')
    assert sum(map(len,groups.values()))==60
    assert set(sum(groups.values(),[]))==set(ids)
    layout=equal_arc_layout(tree)
    raw=dict(layout.coordinates)
    points=list(raw.values())
    bounds=(min(x for x,y in points)-.05,max(x for x,y in points)+.05,
            min(y for x,y in points)-.05,max(y for x,y in points)+.05)
    config=load_config(None)
    config['cloud']['max_density_groups']=3
    fields,counts=compute_cloud_fields(tree,layout,meta,ids,config['cloud'],
                                        config['style']['species_colors'],bounds)
    assert sum(counts.values())==60   # no silent rare-group data loss
    assert len(fields)<=3            # bounded visual layering
    assert layout.coordinates==raw    # no genome moved for colour or haze
    assert all(f['rgba'].shape[-1]==4 for f in fields)


def test_configurable_lineage_grouping_is_not_inferred(tmp_path):
    p=tiny(tmp_path)
    tree=TreeGraph.from_newick(p['tree'])
    meta=load_metadata(p['metadata'])
    ids=reference_ids(tree,meta,load_selected(p['selected']))
    for i,k in enumerate(ids):
        meta[k]['lineage']='A' if i % 3 else 'B'
    groups=groups_for_references(tree,meta,ids,'lineage')
    assert len(groups['A'])==40 and len(groups['B'])==20
    with pytest.raises(ValueError,match='grouping column'):
        groups_for_references(tree,meta,ids,'not_a_column')


@pytest.mark.parametrize('style',['cloud','canopy','constellation','river'])
def test_native_style_render_retains_tree_and_original_tip_count(tmp_path,style):
    p=tiny(tmp_path)
    config=tmp_path / 'config.yml'
    config.write_text('style:\n  preset: '+style+'\ncloud:\n  resolution: 128\n  max_density_groups: 3\n'
                      '  opacity: 0.40\nexport:\n  width_inches: 8\n  height_inches: 6\n  dpi: 85\n')
    out=tmp_path / style
    r=run_plot(p['tree'],p['metadata'],p['selected'],config,out)
    graph=TreeGraph.from_newick(p['tree'])
    assert r['validation']['all_original_edges_retained']
    assert r['validation']['max_absolute_edge_length_error'] < 1e-10
    assert r['tree_edges']==len(graph.adjacency)-1
    assert r['reference_genomes']==60
    assert r['style_preset']==style
    assert sum(r['reference_group_counts'].values())==60
    assert out.with_suffix('.pdf').exists() and out.with_suffix('.png').exists()
    assert '<path' in out.with_suffix('.svg').read_text()
    if style in ('cloud','canopy'):
        assert r['density_type']=='reference_tip_gaussian_visual'
        assert '<image' in out.with_suffix('.svg').read_text()


def test_demo_new_native_default_cli(tmp_path):
    from phylocloud.cli import main
    out=tmp_path/'demo'
    data=main(['demo','--outdir',str(out),'--seed','47','--references','60','--style','canopy'])
    assert data['style_preset']=='canopy'
    assert data['reference_genomes']==60
    assert (out/'phylocloud_demo.svg').exists()
