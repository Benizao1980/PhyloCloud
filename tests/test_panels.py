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
