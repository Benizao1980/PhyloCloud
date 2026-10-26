"""Offline validation of named reference-tree files and declared provenance.

No placement, inference, layout, rendering, directory discovery or network I/O.
A passing report is not independent verification of phylogenetic correctness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from . import __version__
from .preflight import _digest, _inspect_inputs

SCHEMA_VERSION = 1
KINDS = {'reference_only', 'fixed_backbone_placement', 'joint_inference', 'curated_combined'}
SCOPES = {'species_representatives', 'class_subset', 'dense_collection', 'custom'}
FIELDS = {'schema_version', 'provider', 'tree_kind', 'reference_scope', 'release',
          'domain', 'marker_set', 'branch_length_units', 'file_sha256',
          'reference_ids', 'focal_ids', 'provenance'}
PROVENANCE_FIELDS = {'method', 'software', 'software_version', 'reference_release',
                     'marker_set', 'citation', 'source_uri', 'alignment_sha256',
                     'mask_sha256', 'notes'}
ROLES = {'reference': 'reference', 'gtdb': 'reference',
         'focal': 'focal', 'selected': 'focal'}
SHA256 = re.compile(r'[0-9a-fA-F]{64}\Z')


def _issue(report, code, message, action, *, warning=False, values=None, details=False):
    item = dict(code=code, message=message, action=action)
    if values is not None:
        item['count'] = len(values)
        if details:
            item['identifiers'] = sorted(values)
    report['warnings' if warning else 'errors'].append(item)


def _unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError('Duplicate JSON key')
        obj[key] = value
    return obj


def _reject_constant(value):
    raise ValueError('Nonfinite JSON constant')


def _manifest(path, report):
    try:
        before = _digest(path)
        with Path(path).open(encoding='utf8') as handle:
            data = json.load(handle, object_pairs_hook=_unique_object,
                             parse_constant=_reject_constant)
        report['input_sha256']['manifest'] = _digest(path)
        if before != report['input_sha256']['manifest']:
            raise ValueError('Manifest changed during read')
    except (ValueError, OSError, TypeError, RecursionError) as exc:
        _issue(report, 'invalid_manifest', f'Manifest could not be read as stable JSON ({type(exc).__name__}).',
               'Supply a readable JSON object with unique keys and schema_version=1.')
        return {}
    if not isinstance(data, dict):
        _issue(report, 'invalid_manifest', 'Manifest must be a JSON object.', 'Use the documented version-1 bundle schema.')
        return {}
    if set(data) - FIELDS:
        _issue(report, 'unknown_manifest_fields', 'Manifest contains unsupported fields.',
               'Remove unsupported fields; aliases, placement imports and tree assembly are not supported in v1.')
    if type(data.get('schema_version')) is not int or data['schema_version'] != SCHEMA_VERSION:
        _issue(report, 'unsupported_schema', 'Expected integer schema_version=1.', 'Use the version-1 schema.')
    for field, allowed in [('provider', {'gtdb', 'independent'}), ('tree_kind', KINDS),
                           ('reference_scope', SCOPES), ('domain', {'bacteria', 'archaea'})]:
        if field == 'domain' and field not in data:
            continue
        if not isinstance(data.get(field), str) or data[field] not in allowed:
            _issue(report, 'invalid_declaration', f'Invalid or missing {field}.',
                   f'Declare {field} as one of: {", ".join(sorted(allowed))}.')
    for field in ('release', 'marker_set', 'branch_length_units'):
        if field in data and (not isinstance(data[field], str) or not data[field].strip()):
            _issue(report, 'invalid_declaration', f'{field} must be a nonblank string.',
                   'Supply a known value or omit this optional field; do not guess provenance.')
    release = data.get('release')
    if isinstance(release, str) and release.lower() in {'latest', 'current'}:
        _issue(report, 'unpinned_release', 'A moving release alias is not a version pin.', 'Use the exact release or immutable snapshot identifier.')
    if data.get('provider') == 'gtdb':
        if not isinstance(release, str) or not re.fullmatch(r'R\d+(?:\.\d+)?', release):
            _issue(report, 'gtdb_release_required', 'GTDB-associated bundles need a pinned release.', 'Declare e.g. R232 or R232.0, matching the actual source artifacts.')
        if not isinstance(data.get('marker_set'), str) or not data['marker_set'].strip():
            _issue(report, 'marker_set_required', 'GTDB-associated bundles require a marker declaration.', 'Declare the actual marker/alignment set; taxonomy alone is insufficient.')
        if data.get('tree_kind') in ('reference_only', 'fixed_backbone_placement') and data.get('marker_set') not in ('bac120', 'ar53'):
            _issue(report, 'invalid_gtdb_marker', 'GTDB reference/placement trees require bac120 or ar53.', 'Supply the actual domain-specific tree; describe a new combined inference as joint_inference.')
    expected_domain = {'bac120': 'bacteria', 'ar53': 'archaea'}.get(data.get('marker_set')) if isinstance(data.get('marker_set'), str) else None
    if expected_domain and 'domain' in data and data['domain'] != expected_domain:
        _issue(report, 'marker_domain_mismatch', 'Marker set and domain disagree.', 'Correct declarations using the actual source tree; never mix domain trees.')
    for field in ('reference_ids', 'focal_ids'):
        if field not in data:
            continue
        values = data[field]
        if (not isinstance(values, list) or any(not isinstance(n, str) or not n.strip() or n != n.strip() for n in values)
                or len(set(values)) != len(values)):
            _issue(report, 'invalid_declared_ids', f'{field} must contain unique exact nonblank strings.', 'Use original tip IDs; do not trim aliases or merge genomes.')
    hashes = data.get('file_sha256', {})
    if not isinstance(hashes, dict) or set(hashes) - {'tree', 'metadata', 'selected'} or any(not isinstance(v, str) or not SHA256.fullmatch(v) for v in hashes.values()):
        _issue(report, 'invalid_hash_declarations', 'file_sha256 must map tree/metadata/selected to SHA256 hex strings.', 'Remove unknown entries and supply exact hashes of named local files.')
    provenance = data.get('provenance', {})
    if not isinstance(provenance, dict) or set(provenance) - PROVENANCE_FIELDS or any(not isinstance(v, str) or not v.strip() for v in provenance.values()):
        _issue(report, 'invalid_provenance', 'provenance has unknown fields or non-string/blank values.', 'Use documented optional provenance fields; this is a declaration, not verification.')
    else:
        for nested, top in [('reference_release', 'release'), ('marker_set', 'marker_set')]:
            if nested in provenance and provenance[nested] != data.get(top):
                _issue(report, 'inconsistent_provenance', f'provenance.{nested} disagrees with {top}.', 'Reconcile the supplied artifacts and declarations; do not relabel incompatible files.')
        for key in ('alignment_sha256', 'mask_sha256'):
            if key in provenance and not SHA256.fullmatch(provenance[key]):
                _issue(report, 'invalid_provenance_hash', f'provenance.{key} is not SHA256.', 'Supply a 64-character hex digest; this increment records but does not open alignment/mask files.')
    if data.get('tree_kind') == 'fixed_backbone_placement' and isinstance(provenance, dict) and provenance.get('method') in ('ani_screen', 'taxonomy_only'):
        _issue(report, 'classification_is_not_placement', 'ANI/taxonomy-only classification cannot establish fixed-backbone placement.', 'Supply actual placed-query tree and placement provenance; never attach queries by taxonomy.')
    return data


def validate_bundle(tree, metadata, manifest, selected=None, *, include_identifiers=False):
    preflight, context = _inspect_inputs(tree, metadata, selected,
                                         include_identifiers=include_identifiers)
    report = dict(schema_version=SCHEMA_VERSION, phylocloud_version=__version__, valid=False,
                  scope='offline_integrity_and_declared_provenance', input_sha256=dict(preflight['input_sha256']),
                  errors=[], warnings=[], preflight=preflight, hash_checks=[],
                  phylogenetic_correctness=dict(status='not_assessed',
                      reason='No placement, backbone comparison or independent inference verification is performed.'),
                  permissions_assessed=False, provenance_verification='declaration_consistency_only')
    for level in ('errors', 'warnings'):
        for issue in preflight[level]:
            item = dict(issue)
            item.setdefault('message', 'Input integrity check: ' + issue['code'] + '.')
            actions = {
                'tree': 'Use a single Newick with unique tips and explicit finite nonnegative lengths on every edge.',
                'metadata': 'Supply a CSV/TSV with unique genome_id/species/source columns and unique genome IDs.',
                'selected': 'Supply a nonempty exact-ID list with no duplicates; every ID must occur in the tree.',
            }
            item.setdefault('action', actions.get(issue.get('input'),
                'Reconcile the complete tree/metadata/selection census; use --include-identifiers for local ID details.'))
            if issue['code'] not in {'nonselected_tips_not_classified_as_reference', 'selected_tips_also_classified_as_reference'}:
                report[level].append(item)
    # Bundles are exact censuses; unlike ordinary preflight, extra rows are errors.
    extra = [e for e in report['warnings'] if e['code'] == 'metadata_outside_tree']
    report['warnings'] = [e for e in report['warnings'] if e not in extra]
    report['errors'].extend(extra)
    data = _manifest(manifest, report)
    report['declarations'] = {k: v for k, v in data.items() if k not in {'reference_ids', 'focal_ids', 'file_sha256'}}
    if not report['errors']:
        graph, rows = context['tree'], context['metadata']
        role_ids = {'reference': set(), 'focal': set()}
        unknown = []
        for name in graph.tips:
            role = ROLES.get(rows[name].get('source', '').lower())
            if role is None:
                unknown.append(name)
            else:
                role_ids[role].add(name)
        if unknown:
            _issue(report, 'unknown_genome_role', 'Every tip needs an explicit source role.',
                   'Use reference/GTDB or focal/selected in the metadata source column.', values=unknown, details=include_identifiers)
        if not role_ids['reference']:
            _issue(report, 'no_reference_genomes', 'Bundle contains no declared reference genomes.', 'Supply reference metadata for the actual tree, not taxonomy-only query records.')
        if data['tree_kind'] == 'reference_only' and role_ids['focal']:
            _issue(report, 'reference_only_has_focals', 'reference_only contradicts focal metadata.', 'Provide the real combined tree or correct the declared kind using its provenance.')
        if data['tree_kind'] != 'reference_only' and not role_ids['focal']:
            _issue(report, 'combined_tree_has_no_focals', 'Combined-tree declaration has no focal genomes.', 'Provide the combined tree and metadata; do not invent placements.')
        wrongly_selected = set(context['selected']) - role_ids['focal']
        if wrongly_selected:
            _issue(report, 'selection_not_focal', 'Requested selection contains nonfocal genomes.', 'Select exact focal IDs or resolve their metadata roles explicitly.', values=wrongly_selected, details=include_identifiers)
        for field, role in [('reference_ids', 'reference'), ('focal_ids', 'focal')]:
            if field in data and set(data[field]) != role_ids[role]:
                _issue(report, 'declared_membership_mismatch', f'{field} does not match the exact metadata/tree census.', 'Supply every declared member in both tree and metadata, or correct the documented reference scope.',
                       values=set(data[field]) ^ role_ids[role], details=include_identifiers)
        for column, field in [('reference_release', 'release'), ('marker_set', 'marker_set')]:
            mismatch = [n for n in role_ids['reference'] if rows[n].get(column) and rows[n][column] != data.get(field)]
            if mismatch:
                _issue(report, 'metadata_provenance_mismatch', f'Reference metadata {column} conflicts with the manifest.', 'Use matching reference artifacts/versions and declare their actual provenance.', values=mismatch, details=include_identifiers)
        report['membership'] = dict(reference_genomes=len(role_ids['reference']), focal_genomes=len(role_ids['focal']),
                                     selected_genomes=len(context['selected']), selection_file_supplied=selected is not None,
                                     sha256={role: hashlib.sha256(json.dumps(sorted(ids)).encode()).hexdigest() for role, ids in role_ids.items()})
    hashes = data.get('file_sha256', {})
    if isinstance(hashes, dict):
        for name, expected in hashes.items():
            if name not in {'tree', 'metadata', 'selected'} or not isinstance(expected, str) or not SHA256.fullmatch(expected):
                continue
            actual = report['input_sha256'].get(name)
            matched = actual == expected.lower()
            report['hash_checks'].append(dict(file=name, expected=expected.lower(), actual=actual, matched=matched))
            if not matched:
                _issue(report, 'file_hash_mismatch', f'{name} is unavailable or differs from its declared hash.', 'Supply the correct named file and manifest; never replace expected hashes merely to silence a mismatch.')
    if not hashes:
        _issue(report, 'no_expected_hashes', 'Actual hashes recorded without an expected file-hash baseline.', 'Optionally supply trusted file_sha256 values; recorded hashes alone do not establish authenticity.', warning=True)
    for field in ('marker_set', 'branch_length_units'):
        if field not in data or data.get(field) == 'unknown':
            _issue(report, 'incomplete_provenance', f'{field} is not established.', 'Obtain the original methods/provenance before scientific comparison; no unit or marker set is inferred.', warning=True)
    if isinstance(data.get('provenance', {}), dict) and not data.get('provenance', {}).get('method'):
        _issue(report, 'incomplete_provenance', 'Inference/placement method is not declared.', 'Record the original method when available; technical validity does not verify phylogenetic correctness.', warning=True)
    if data.get('reference_scope') == 'class_subset':
        _issue(report, 'limited_reference_scope', 'This bundle declares a class-level subset, not complete GTDB diversity.', 'Keep the scope explicit in figures; do not stitch split trees.', warning=True)
    report['valid'] = not report['errors']
    report['summary'] = format_summary(report)
    return report


def format_summary(report):
    status = 'PASS' if report['valid'] else 'FAIL'
    lines = [f'{status}: offline file integrity and declared provenance only.',
             'Phylogenetic correctness: NOT ASSESSED. Permissions: NOT ASSESSED.']
    if 'membership' in report:
        m = report['membership']
        lines.append(f"Genomes: {m['reference_genomes']} reference, {m['focal_genomes']} focal; {m['selected_genomes']} selected.")
    for level in ('errors', 'warnings'):
        for issue in report[level]:
            lines.append(f"{level[:-1].upper()} [{issue['code']}]: {issue['message']} {issue['action']}")
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('tree', 'metadata', 'manifest', 'out'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--selected', help='Optional exact focal IDs; omission does not select all focal genomes')
    parser.add_argument('--include-identifiers', action='store_true')
    args = parser.parse_args(argv)
    with Path(args.out).open('x', encoding='utf8') as handle:
        report = validate_bundle(args.tree, args.metadata, args.manifest, args.selected,
                                 include_identifiers=args.include_identifiers)
        handle.write(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(report['summary'])
    return 0 if report['valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
