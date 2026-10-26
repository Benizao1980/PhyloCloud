"""Offline bundle contract: synthetic only, no tree editing or placement claims."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from unittest.mock import patch

import pytest
from phylocloud.reference_bundle import validate_bundle, main

EXAMPLE = Path(__file__).resolve().parents[1] / 'examples/reference_bundle'


@pytest.fixture
def bundle(tmp_path):
    root = tmp_path / 'bundle'
    shutil.copytree(EXAMPLE, root)
    return root


def run(root, selected=True):
    return validate_bundle(root/'tree.nwk', root/'metadata.tsv', root/'manifest.json',
                           root/'selected.txt' if selected else None)


def edit_manifest(root, edit):
    path = root/'manifest.json'
    data = json.loads(path.read_text())
    edit(data)
    path.write_text(json.dumps(data))


def codes(report):
    return {e['code'] for e in report['errors']}


def test_valid_complete_tree_reuses_preflight_without_render_or_mutation(bundle):
    before = {p.name: p.read_bytes() for p in bundle.iterdir()}
    with patch('phylocloud.geometry.equal_arc_layout', side_effect=AssertionError('no layout')), \
         patch('phylocloud.render.draw', side_effect=AssertionError('no render')), \
         patch('socket.create_connection', side_effect=AssertionError('no network')):
        report = run(bundle)
    assert report['valid'] and not report['errors']
    assert report['membership']['reference_genomes'] == 3
    assert report['membership']['focal_genomes'] == report['membership']['selected_genomes'] == 2
    assert report['preflight']['tree']['original_edges'] == 7
    assert report['preflight']['tree']['zero_length_edges'] == 2
    assert report['phylogenetic_correctness']['status'] == 'not_assessed'
    assert report['permissions_assessed'] is False
    assert len(report['hash_checks']) == 3 and all(e['matched'] for e in report['hash_checks'])
    assert all(name in report['input_sha256'] for name in ('tree','metadata','selected','manifest'))
    assert run(bundle) == report
    assert before == {p.name: p.read_bytes() for p in bundle.iterdir()}
    assert 'NOT ASSESSED' in report['summary']


def test_optional_selection_does_not_select_all_focals(bundle):
    edit_manifest(bundle, lambda d: d['file_sha256'].pop('selected'))
    report = run(bundle, selected=False)
    assert report['valid']
    assert report['membership']['focal_genomes'] == 2
    assert report['membership']['selected_genomes'] == 0
    assert report['membership']['selection_file_supplied'] is False


def test_reference_only_without_any_selection(bundle):
    (bundle/'tree.nwk').write_text('(REF_A:0,REF_B:.2,REF_C:1);')
    lines = (bundle/'metadata.tsv').read_text().splitlines()
    (bundle/'metadata.tsv').write_text('\n'.join(lines[:4])+'\n')
    def change(d):
        d['tree_kind'] = 'reference_only'; d['focal_ids'] = []; d.pop('file_sha256')
    edit_manifest(bundle, change)
    report = run(bundle, selected=False)
    assert report['valid'] and report['membership']['focal_genomes'] == 0


@pytest.mark.parametrize('filename,old,new,code', [
    ('selected.txt','FOCAL_2','ABSENT','selected_outside_tree'),
    ('selected.txt','FOCAL_2','FOCAL_1','duplicate_selected_ids'),
    ('selected.txt','FOCAL_2','REF_A','selection_not_focal'),
    ('tree.nwk','REF_C','REF_B','invalid_input'),
    ('tree.nwk','FOCAL_2:1.25','FOCAL_2','invalid_input'),
    ('tree.nwk','REF_B:0.05','REF_B:-0.05','invalid_input'),
    ('tree.nwk',',REF_C:0.08','','metadata_outside_tree'),
    ('metadata.tsv','FOCAL_2\tSynthetic other species\tfocal\t\tcore_genome\n','','metadata_missing_tree_tips'),
    ('metadata.tsv','REF_B\tSynthetic other species\treference','REF_A\tSynthetic other species\treference','invalid_input'),
    ('metadata.tsv','REF_A\tSynthetic mixed species\treference','REF_A\tSynthetic mixed species\tunknown','unknown_genome_role'),
    ('metadata.tsv','reference\tsynthetic-v1\tcore_genome','reference\twrong-release\tcore_genome','metadata_provenance_mismatch'),
])
def test_invalid_files_report_actionable_failures(bundle, filename, old, new, code):
    path = bundle/filename; path.write_text(path.read_text().replace(old,new))
    edit_manifest(bundle, lambda d: d.pop('file_sha256'))
    report = run(bundle)
    assert not report['valid'] and code in codes(report)
    assert all(e['message'] and e['action'] for e in report['errors'])
    assert all('identifiers' not in e for e in report['errors'])


@pytest.mark.parametrize('patch_data,code', [
    ({'reference_ids':['REF_A','REF_B','REF_C','REF_MISSING']},'declared_membership_mismatch'),
    ({'focal_ids':['FOCAL_1','MISSING_MAG']},'declared_membership_mismatch'),
    ({'focal_ids':['FOCAL_1','FOCAL_1']},'invalid_declared_ids'),
    ({'tree_kind':'reference_only'},'reference_only_has_focals'),
    ({'provenance':{'marker_set':'ar53'}},'inconsistent_provenance'),
    ({'provenance':{'reference_release':'R226'}},'inconsistent_provenance'),
    ({'marker_set':'ar53'},'marker_domain_mismatch'),
    ({'release':'latest'},'unpinned_release'),
    ({'file_sha256':{'tree':'0'*64}},'file_hash_mismatch'),
    ({'file_sha256':{'tree':'bad'}},'invalid_hash_declarations'),
    ({'phylogenetic_correctness':True},'unknown_manifest_fields'),
    ({'schema_version':True},'unsupported_schema'),
    ({'tree_kind':['split','trees'],'provider':'gtdb','marker_set':'bac120'},'invalid_declaration'),
    ({'reference_ids':[{}]},'invalid_declared_ids'),
    ({'provenance':{'alignment_sha256':'bad'}},'invalid_provenance_hash'),
    ({'provider':'gtdb','tree_kind':'reference_only','marker_set':[]},'invalid_declaration'),
    ({'provider':'gtdb','tree_kind':'reference_only','marker_set':{}},'invalid_declaration'),
    ({'tree_kind':{}},'invalid_declaration'),
    ({'provider':{}},'invalid_declaration'),
    ({'reference_scope':[]},'invalid_declaration'),
    ({'provenance':[]},'invalid_provenance'),
    ({'file_sha256':[]},'invalid_hash_declarations'),
])
def test_manifest_contradictions_are_not_accepted_as_provenance(bundle, patch_data, code):
    edit_manifest(bundle, lambda d: d.update(copy.deepcopy(patch_data)))
    report = run(bundle)
    assert not report['valid'] and code in codes(report)
    assert report['phylogenetic_correctness']['status'] == 'not_assessed'


@pytest.mark.parametrize('content', ['{','[]','{"schema_version":1,"schema_version":2}', '{"schema_version":NaN}'])
def test_bad_json_returns_a_failure_report(bundle, content):
    (bundle/'manifest.json').write_text(content)
    report = run(bundle)
    assert not report['valid'] and 'invalid_manifest' in codes(report)


def test_gtdb_declarations_are_checked_but_not_independently_verified(bundle):
    def change(d):
        d.update(provider='gtdb', release='R232', marker_set='bac120', tree_kind='fixed_backbone_placement', reference_scope='class_subset')
        d.pop('file_sha256')
        d['provenance'] = dict(method='pplacer (synthetic declaration, no run)', reference_release='R232', marker_set='bac120')
    edit_manifest(bundle, change)
    p=bundle/'metadata.tsv'; p.write_text(p.read_text().replace('synthetic-v1','R232').replace('core_genome','bac120'))
    report=run(bundle)
    assert report['valid'] and report['phylogenetic_correctness']['status']=='not_assessed'
    assert 'limited_reference_scope' in {w['code'] for w in report['warnings']}
    edit_manifest(bundle, lambda d: d['provenance'].update(method='ani_screen'))
    assert 'classification_is_not_placement' in codes(run(bundle))


def test_incomplete_independent_provenance_is_explicit_not_invented(bundle):
    data=dict(schema_version=1,provider='independent',tree_kind='curated_combined',reference_scope='custom')
    (bundle/'manifest.json').write_text(json.dumps(data))
    # No per-reference declarations exist in this minimal metadata file.
    lines=(bundle/'metadata.tsv').read_text().splitlines()
    (bundle/'metadata.tsv').write_text('\n'.join('\t'.join(line.split('\t')[:3]) for line in lines)+'\n')
    report=run(bundle)
    assert report['valid']
    assert len([w for w in report['warnings'] if w['code']=='incomplete_provenance'])==3
    assert 'marker_set' not in report['declarations']


def test_gtdb_requires_release_and_marker_set(bundle):
    edit_manifest(bundle, lambda d: d.update(provider='gtdb',release='snapshot',marker_set=''))
    report=run(bundle)
    assert {'gtdb_release_required','marker_set_required'} <= codes(report)


def test_cli_reports_failure_and_never_overwrites_inputs_or_reports(bundle,tmp_path,capsys):
    out=tmp_path/'report.json'
    args=['--tree',str(bundle/'tree.nwk'),'--metadata',str(bundle/'metadata.tsv'),
          '--manifest',str(bundle/'manifest.json'),'--selected',str(bundle/'selected.txt'),'--out',str(out)]
    assert main(args)==0
    assert 'PASS' in capsys.readouterr().out
    before=out.read_bytes()
    with pytest.raises(FileExistsError): main(args)
    assert out.read_bytes()==before
    args[-1]=str(bundle/'tree.nwk'); before_tree=(bundle/'tree.nwk').read_bytes()
    with pytest.raises(FileExistsError): main(args)
    assert (bundle/'tree.nwk').read_bytes()==before_tree
    args[-1]=str(tmp_path/'failure.json')
    (bundle/'manifest.json').write_text('{')
    assert main(args)==1
    assert not json.loads(Path(args[-1]).read_text())['valid']
    assert 'FAIL' in capsys.readouterr().out


def test_installed_module_subprocess_and_example_hashes(tmp_path):
    command=[sys.executable,'-m','phylocloud.reference_bundle','--tree',str(EXAMPLE/'tree.nwk'),
             '--metadata',str(EXAMPLE/'metadata.tsv'),'--selected',str(EXAMPLE/'selected.txt'),
             '--manifest',str(EXAMPLE/'manifest.json'),'--out',str(tmp_path/'subprocess.json')]
    process=subprocess.run(command,cwd=tmp_path,text=True,capture_output=True)
    assert process.returncode==0,process.stderr
    report=json.loads((tmp_path/'subprocess.json').read_text())
    assert report['valid'] and 'NOT ASSESSED' in process.stdout
    for name,filename in [('tree','tree.nwk'),('metadata','metadata.tsv'),('selected','selected.txt')]:
        assert report['input_sha256'][name]==hashlib.sha256((EXAMPLE/filename).read_bytes()).hexdigest()


@pytest.mark.parametrize('mutation,code', [
    ('no_references','no_reference_genomes'),
    ('no_focals','combined_tree_has_no_focals'),
    ('duplicate_header','invalid_input'),
    ('marker_mismatch','metadata_provenance_mismatch'),
    ('missing_file','invalid_input'),
])
def test_role_and_metadata_edge_cases(bundle,mutation,code):
    path=bundle/'metadata.tsv'
    text=path.read_text()
    if mutation=='no_references': text=text.replace('reference','focal')
    if mutation=='no_focals': text=text.replace('focal','reference')
    if mutation=='duplicate_header': text=text.replace('marker_set','source',1)
    if mutation=='marker_mismatch': text=text.replace('synthetic-v1\tcore_genome','synthetic-v1\twrong_markers')
    path.write_text(text)
    if mutation=='missing_file': path.unlink()
    assert code in codes(run(bundle))


def test_selected_hash_requires_named_selection_file(bundle):
    report=run(bundle,selected=False)
    assert not report['valid'] and 'file_hash_mismatch' in codes(report)
    check=next(r for r in report['hash_checks'] if r['file']=='selected')
    assert check['actual'] is None and not check['matched']


def test_identifier_diagnostics_are_opt_in(bundle):
    (bundle/'selected.txt').write_text('PRIVATE_UNKNOWN_ID\n')
    minimal=run(bundle)
    assert 'PRIVATE_UNKNOWN_ID' not in json.dumps(minimal)
    detailed=validate_bundle(bundle/'tree.nwk',bundle/'metadata.tsv',bundle/'manifest.json',
                             bundle/'selected.txt',include_identifiers=True)
    assert 'PRIVATE_UNKNOWN_ID' in json.dumps(detailed)
