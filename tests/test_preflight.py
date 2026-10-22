"""Named synthetic inputs only; reports never modify sources or render."""
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
import pytest
from phylocloud.preflight import inspect_inputs, main


@pytest.fixture
def inputs(tmp_path):
    tree=tmp_path/'tree.nwk'; tree.write_text('((A:0,B:0):.2,C:5,D:.1);')
    meta=tmp_path/'meta.tsv'; meta.write_text('genome_id\tspecies\tsource\nA\tMixed\tselected\nB\tMixed\tGTDB\nC\tOther\treference\nD\tMixed\tselected\n')
    selected=tmp_path/'selected.txt'; selected.write_text('A\nD\n')
    return tree,meta,selected


def codes(report,field='errors'):
    return {r['code'] for r in report[field]}


def test_preflight_preserves_original_files_and_never_lays_out_or_renders(inputs):
    before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    with patch('phylocloud.geometry.equal_arc_layout',side_effect=AssertionError('layout forbidden')), \
         patch('phylocloud.render.draw',side_effect=AssertionError('render forbidden')):
        result=inspect_inputs(*inputs)
    assert result['valid']
    assert result['tree']==dict(tips=4,nodes=6,original_edges=5,zero_length_edges=2,minimum_edge_length=0,maximum_edge_length=5)
    assert result['reference']['count']==2
    assert result['species']==dict(categories=2,blank_labels=0)
    assert result['permissions_assessed'] is result['scientific_or_visual_acceptance'] is False
    assert inspect_inputs(*inputs)==result
    assert before=={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    assert '/Users/' not in json.dumps(result)


@pytest.mark.parametrize('content,code', [('A\nA\n','duplicate_selected_ids'),('A\nunknown\n','selected_outside_tree')])
def test_bad_selection_is_diagnosed_without_identifier_disclosure(inputs,content,code):
    inputs[2].write_text(content)
    r=inspect_inputs(*inputs)
    assert not r['valid'] and code in codes(r)
    assert all('identifiers' not in item for item in r['errors'])
    detailed=inspect_inputs(*inputs,include_identifiers=True)
    assert any('identifiers' in item for item in detailed['errors'])


@pytest.mark.parametrize('newick', ['(A:0,A:1,C:2);','(A:0,B:-1,C:2);','(A:0,B,C:2);','((A:0,B:1,C:2);'])
def test_invalid_original_tree_is_rejected(inputs,newick):
    inputs[0].write_text(newick)
    r=inspect_inputs(*inputs)
    assert not r['valid'] and r['errors'][0]['input']=='tree'


def test_missing_and_extra_metadata_are_distinguished(inputs):
    inputs[1].write_text('genome_id\tspecies\nA\tMixed\nB\tMixed\nC\tOther\nextra\tOther\n')
    r=inspect_inputs(*inputs,include_identifiers=True)
    assert not r['valid']
    assert r['errors']==[dict(code='metadata_missing_tree_tips',count=1,identifiers=['D'])]
    assert r['warnings']==[dict(code='metadata_outside_tree',count=1,identifiers=['extra'])]


def test_partial_sources_expose_production_reference_policy(inputs):
    inputs[1].write_text('genome_id\tspecies\tsource\nA\tMixed\tGTDB\nB\tMixed\t\nC\t\treference\nD\tMixed\tselected\nextra\tOther\tGTDB\n')
    r=inspect_inputs(*inputs)
    assert r['valid']
    assert r['reference']==dict(count=2,source_policy='explicit_source',selected_also_reference=1,nonselected_not_reference=1)
    assert codes(r,'warnings')=={'metadata_outside_tree','selected_tips_also_classified_as_reference','nonselected_tips_not_classified_as_reference','blank_species_labels'}


def test_cli_exclusive_report_and_exit_status(inputs,tmp_path):
    out=tmp_path/'report.json'
    args=['--tree',str(inputs[0]),'--metadata',str(inputs[1]),'--selected',str(inputs[2]),'--out',str(out)]
    assert main(args)==0
    before=out.read_bytes()
    with pytest.raises(FileExistsError): main(args)
    assert out.read_bytes()==before
    args[-1]=str(inputs[0]); original=inputs[0].read_bytes()
    with pytest.raises(FileExistsError): main(args)
    assert inputs[0].read_bytes()==original
    inputs[2].write_text('unknown\n')
    args[-1]=str(tmp_path/'invalid.json')
    assert main(args)==1


def test_one_selected_tip_matches_existing_plot_contract(inputs):
    inputs[2].write_text('A\n')
    result=inspect_inputs(*inputs)
    assert result['valid']
    assert 'single_selected_tip_no_connecting_subtree' in codes(result,'warnings')
