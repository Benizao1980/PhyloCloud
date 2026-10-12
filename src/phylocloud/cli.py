"""PhyloCloud command-line interface."""
from __future__ import annotations
import argparse
import json
import hashlib
import math
from pathlib import Path
from .data import load_config,load_metadata,load_selected
from .geometry import TreeGraph, equal_arc_layout
from .render import draw
from .synthetic import make_demo


def run_plot(tree,metadata,selected,config,out):
    graph=TreeGraph.from_newick(tree)
    meta=load_metadata(metadata)
    ids=load_selected(selected)
    unknown=sorted(set(graph.tips)-set(meta))
    if unknown:
        raise ValueError(f'Metadata missing {len(unknown)} tree tips (first: {unknown[:5]})')
    cfg=load_config(config)
    layout=equal_arc_layout(
        graph, rotate_degrees=cfg['layout']['rotation_degrees'],
        angle_mode=cfg['layout'].get('angle_mode', 'tip_count'),
    )
    summary = draw(graph,layout,meta,ids,cfg,out)
    original_edges = {frozenset((node,nb)) for node,nbrs in graph.adjacency.items()
                      for nb,_ in nbrs}
    plotted_edges = {frozenset((p,c)) for p,c,_ in layout.edges}
    assert len(plotted_edges) == len(layout.edges) == len(original_edges)
    assert plotted_edges == original_edges, 'Plot edges differ from original topology'
    deviations = [abs(math.dist(layout.coordinates[p],layout.coordinates[c]) - length)
                  for p,c,length in layout.edges]
    max_error = max(deviations,default=0)
    assert max_error <= 1e-10, 'Original edge length changed in plot'
    def digest(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    original_lengths = [length for _,_,length in layout.edges]
    summary['validation'] = {
        'tip_ids_unique': len(graph.tips)==len(set(graph.tips)),
        'all_original_edges_retained': True,
        'original_edges_retained': len(plotted_edges),
        'zero_length_edges': sum(length == 0 for length in original_lengths),
        'max_absolute_edge_length_error': max_error,
    }
    summary['input_sha256'] = {
        'tree': digest(tree), 'metadata': digest(metadata),
        'selected': digest(selected),
        'config': digest(config) if config else None,
    }
    summary['layout_parameters'] = cfg['layout']
    summary['style_parameters'] = {
        key:cfg['style'][key] for key in ('preset','density_overlay','density_opacity',
                                        'species_background')
    }
    report = Path(out).with_suffix('.provenance.json')
    report.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return summary


def main(argv=None):
    parser=argparse.ArgumentParser(prog='phylocloud',description='Unrooted reference diversity cloud with a topology-preserving selected subtree')
    sub=parser.add_subparsers(dest='command',required=True)
    plot=sub.add_parser('plot',help='Render a Newick tree with selected tips')
    plot.add_argument('--tree',required=True)
    plot.add_argument('--metadata',required=True)
    plot.add_argument('--selected',required=True)
    plot.add_argument('--config')
    plot.add_argument('--out',required=True,help='Output stem (no file extension)')
    demo=sub.add_parser('demo',help='Create reproducible synthetic inputs and preview')
    demo.add_argument('--outdir',default='outputs/demo')
    demo.add_argument('--seed',type=int,default=47)
    demo.add_argument('--references',type=int,default=900)
    args=parser.parse_args(argv)
    if args.command=='demo':
        paths=make_demo(args.outdir,args.seed,args.references)
        result=run_plot(paths['tree'],paths['metadata'],paths['selected'],paths['config'],
                        Path(args.outdir)/'phylocloud_demo')
    else:
        result=run_plot(args.tree,args.metadata,args.selected,args.config,args.out)
    print(json.dumps(result,indent=2))
    return result


if __name__=='__main__':main()
