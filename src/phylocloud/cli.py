"""PhyloCloud command-line interface."""
from __future__ import annotations
import argparse
import json
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
    layout=equal_arc_layout(graph,rotate_degrees=cfg['layout']['rotation_degrees'])
    return draw(graph,layout,meta,ids,cfg,out)


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
