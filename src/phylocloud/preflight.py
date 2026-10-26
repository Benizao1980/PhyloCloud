"""Read-only checks of explicitly supplied inputs; no layout or figure creation."""
from __future__ import annotations

import argparse
import csv
from collections import Counter
import hashlib
import json
from pathlib import Path

from Bio.Phylo.NewickIO import NewickError

from . import __version__
from .data import load_metadata, load_selected
from .geometry import TreeGraph


def _digest(path):
    with Path(path).open('rb') as handle:
        digest = hashlib.sha256()
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_inputs(tree, metadata, selected, *, include_identifiers=False):
    """Audit named files only. Permission, provenance and visual review are external.

    Reuse production parsers and reference classification; never silently repair
    aliases, drop extra rows, normalize taxonomy or calculate a layout.
    """
    report = dict(schema_version=1, phylocloud_version=__version__, valid=False,
                  scope='input_integrity_only', permissions_assessed=False,
                  scientific_or_visual_acceptance=False, input_sha256={},
                  errors=[], warnings=[])
    parsed = {}
    for key, path, loader in [('tree', tree, TreeGraph.from_newick),
                              ('metadata', metadata, load_metadata),
                              ('selected', selected, load_selected)]:
        try:
            before = _digest(path)
            parsed[key] = loader(path)
            after = _digest(path)
            report['input_sha256'][key] = after
            if before != after:
                report['errors'].append(dict(code='input_changed_during_read', input=key))
        except (ValueError, OSError, KeyError, AttributeError, TypeError, csv.Error, NewickError) as error:
            issue = dict(code='invalid_input', input=key, reason=type(error).__name__)
            if include_identifiers:
                issue['detail'] = str(error)
            report['errors'].append(issue)
    if len(parsed) != 3 or report['errors']:
        return report
    graph, rows, ids = (parsed[k] for k in ('tree', 'metadata', 'selected'))
    tips = set(graph.tips)

    def diagnostic(collection, code, values):
        if values:
            issue = dict(code=code, count=len(values))
            if include_identifiers:
                issue['identifiers'] = sorted(values)
            collection.append(issue)

    diagnostic(report['errors'], 'metadata_missing_tree_tips', tips - rows.keys())
    diagnostic(report['warnings'], 'metadata_outside_tree', rows.keys() - tips)
    diagnostic(report['errors'], 'selected_outside_tree', set(ids) - tips)
    diagnostic(report['errors'], 'duplicate_selected_ids',
               {n for n, count in Counter(ids).items() if count > 1})
    if len(set(ids)) < 2:
        report['warnings'].append(dict(code='single_selected_tip_no_connecting_subtree'))
    lengths = [length for a, neighbours in graph.adjacency.items()
               for b, length in neighbours if id(a) < id(b)]
    report['tree'] = dict(tips=len(tips), nodes=len(graph.adjacency),
                          original_edges=len(lengths), zero_length_edges=lengths.count(0),
                          minimum_edge_length=min(lengths), maximum_edge_length=max(lengths))
    report['selection'] = dict(rows=len(ids), distinct_ids=len(set(ids)))
    if report['errors']:
        return report
    # Import the production policy, rather than duplicating its source semantics.
    from .cloud_layers import reference_ids
    references = reference_ids(graph, rows, ids)
    sources = Counter(rows[n].get('source', '') for n in tips)
    report['reference'] = dict(count=len(references),
                              source_policy='explicit_source' if any(sources.keys()) else 'nonselected_fallback',
                              selected_also_reference=len(set(ids) & set(references)),
                              nonselected_not_reference=len(tips - set(ids) - set(references)))
    report['species'] = dict(categories=len({rows[n]['species'] for n in tips}),
                            blank_labels=sum(not rows[n]['species'] for n in tips))
    if report['species']['blank_labels']:
        report['warnings'].append(dict(code='blank_species_labels', count=report['species']['blank_labels']))
    if report['reference']['nonselected_not_reference']:
        report['warnings'].append(dict(code='nonselected_tips_not_classified_as_reference',
                                      count=report['reference']['nonselected_not_reference']))
    if report['reference']['selected_also_reference']:
        report['warnings'].append(dict(code='selected_tips_also_classified_as_reference',
                                      count=report['reference']['selected_also_reference']))
    report['membership_sha256'] = {
        key: hashlib.sha256(json.dumps(sorted(values)).encode()).hexdigest()
        for key, values in [('tips', tips), ('selected', ids), ('reference', references)]}
    report['valid'] = True
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tree', required=True)
    parser.add_argument('--metadata', required=True)
    parser.add_argument('--selected', required=True)
    parser.add_argument('--out', required=True, help='New local JSON report; existing files are never replaced')
    parser.add_argument('--include-identifiers', action='store_true', help='Include potentially sensitive IDs/error details in local report')
    args = parser.parse_args(argv)
    # Reserve exclusively before reading inputs: a typo must never truncate one.
    with Path(args.out).open('x', encoding='utf8') as handle:
        report = inspect_inputs(args.tree, args.metadata, args.selected,
                                include_identifiers=args.include_identifiers)
        handle.write(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return 0 if report['valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
