"""Optional overview/detail geometric-composition safety."""
import json
import pytest
from phylocloud.cli import run_plot
from phylocloud.synthetic import make_demo
from phylocloud.data import load_selected


def test_overview_and_detail_share_original_full_tree(tmp_path):
    paths = make_demo(tmp_path/'fixtures', seed=51, reference_count=60)
    all_selected = load_selected(paths['selected'])
    detail_file = tmp_path/'detail.txt'
    detail_file.write_text('\n'.join(all_selected[:3])+'\n')
    config = tmp_path/'fast.yml'
    config.write_text('style:\n  preset: canopy\n  title: Testing detail layout\ncloud:\n  resolution: 128\n  max_density_groups: 3\nexport:\n  width_inches: 7\n  height_inches: 6\n  dpi: 75\n')
    out = tmp_path/'testtree'
    summary = run_plot(paths['tree'], paths['metadata'], paths['selected'], config, out,
                       detail_selected=detail_file)
    assert summary['detail_panel']['same_layout'] is True
    assert summary['detail_panel']['full_tree_edges'] == summary['tree_edges']
    assert summary['detail_panel']['selected_tip_ids'] == all_selected[:3]
    for name in ('testtree.png','testtree.svg','testtree_detail.svg',
                 'testtree_detail.pdf','testtree_overview_detail.png',
                 'testtree.provenance.json'):
        assert (tmp_path/name).is_file(), name
    report=json.loads((tmp_path/'testtree.provenance.json').read_text())
    assert report['detail_panel']['composition'] == 'raster_contact_sheet'


def test_detail_rejects_nonfocal_tip_without_mutating_tree(tmp_path):
    paths=make_demo(tmp_path/'fixtures',seed=55,reference_count=60)
    wrong=tmp_path/'wrong.txt'
    wrong.write_text('REF_INF_0001\nMAG_SYN_01\n')
    config=tmp_path/'fast.yml'
    config.write_text('style:\n  preset: publication\nexport:\n  dpi: 60\n  width_inches: 5\n  height_inches: 5\n')
    with pytest.raises(ValueError,match='subset'):
        run_plot(paths['tree'],paths['metadata'],paths['selected'],config,tmp_path/'wrongout',detail_selected=wrong)


@pytest.mark.parametrize('composition',['legacy','publication'])
def test_detail_preserves_full_selection_even_without_source_metadata(tmp_path,composition):
    from phylocloud.geometry import TreeGraph, connecting_edges
    from phylocloud.data import load_metadata
    import xml.etree.ElementTree as ET
    paths=make_demo(tmp_path/'fixtures',seed=51,reference_count=60)
    # Without sources, reference membership depends on the FULL focal selection.
    rows=load_metadata(paths['metadata'])
    paths['metadata'].write_text('genome_id\tspecies\tlabel\n'+''.join(
        f"{n}\t{r['species']}\t{n}\n" for n,r in rows.items()))
    selected=load_selected(paths['selected']); focus=selected[:3]
    graph=TreeGraph.from_newick(paths['tree'])
    assert connecting_edges(graph,focus)!=connecting_edges(graph,selected)
    detail=tmp_path/'detail.txt'; detail.write_text('\n'.join(focus)+'\n')
    config=tmp_path/'config.yml'
    config.write_text(f'style:\n  preset: cloud\n  composition: {composition}\n  title: Detail regression\n'
                      'cloud:\n  resolution: 128\nexport:\n  width_inches: 12\n  height_inches: 10\n  dpi: 75\n')
    out=tmp_path/'figure'
    report=run_plot(paths['tree'],paths['metadata'],paths['selected'],config,out,detail_selected=detail)
    zoom=json.loads((tmp_path/'figure_detail.provenance.json').read_text())
    assert zoom['highlighted_tip_ids']==selected
    assert zoom['labelled_tip_ids']==zoom['crop_tip_ids']==focus
    assert zoom['reference_genomes']==report['reference_genomes']==60
    assert zoom['foreground_original_edge_ids']==report['foreground_original_edge_ids']
    assert zoom['coordinate_sha256']==report['coordinate_sha256']
    assert zoom['foreground_edges']==len(connecting_edges(graph,selected))
    assert zoom['density_raster']==report['density_raster']  # same sampled field, only camera changes
    assert report['detail_panel']['same_foreground_edge_set']
    assert zoom['validation']['all_original_edges_retained']
    ns={'s':'http://www.w3.org/2000/svg'}
    svg=ET.parse(tmp_path/'figure_detail.svg')
    paths_svg=svg.find(".//s:g[@id='selected-original-edges']",ns).findall('s:path',ns)
    assert len(paths_svg)==report['foreground_edges']
    import hashlib
    for ext,sha in zoom['output_sha256'].items():
        assert hashlib.sha256((tmp_path/('figure_detail.'+ext)).read_bytes()).hexdigest()==sha


def test_invalid_detail_writes_no_partial_exports(tmp_path):
    paths=make_demo(tmp_path/'fixtures',reference_count=60)
    invalid=tmp_path/'invalid.txt'; invalid.write_text('MAG_SYN_01\nnot-in-tree\n')
    stem=tmp_path/'must-not-exist'
    with pytest.raises(ValueError,match='subset'):
        run_plot(paths['tree'],paths['metadata'],paths['selected'],None,stem,detail_selected=invalid)
    assert not list(tmp_path.glob('must-not-exist*'))
