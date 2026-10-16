"""PhyloCloud command-line interface."""
from __future__ import annotations
import argparse
import json
import copy
import hashlib
import math
from pathlib import Path
from .data import load_config,load_metadata,load_selected
from .geometry import TreeGraph, equal_arc_layout
from .render import draw
from .synthetic import make_demo


def run_plot(tree,metadata,selected,config,out,style=None,cloud_group_by=None,detail_selected=None,length_mode=None,species_panels=None):
    graph=TreeGraph.from_newick(tree)
    meta=load_metadata(metadata)
    ids=load_selected(selected)
    unknown=sorted(set(graph.tips)-set(meta))
    if unknown:
        raise ValueError(f'Metadata missing {len(unknown)} tree tips (first: {unknown[:5]})')
    cfg=load_config(config)
    if style is not None:
        # New CLI style overrides must adopt full preset defaults, not merely
        # change the name; honour user YAML as the baseline otherwise.
        from .data import PRESETS
        if style not in PRESETS:
            raise ValueError(f'Unknown style {style!r}; choices: {sorted(PRESETS)}')
        cfg['style'].update(PRESETS[style])
        cfg['style']['preset']=style
    if cloud_group_by is not None:
        cfg['cloud']['group_by']=cloud_group_by
    if length_mode is not None:
        cfg['layout']['length_mode'] = length_mode
    if cfg['layout'].get('length_mode','original') == 'graphic' and cfg['style'].get('scale_bar'):
        raise ValueError('Scale bars are invalid for non-metric graphic display lengths')
    layout=equal_arc_layout(
        graph, rotate_degrees=cfg['layout']['rotation_degrees'],
        angle_mode=cfg['layout'].get('angle_mode', 'tip_count'),
        length_mode=cfg['layout'].get('length_mode', 'original'),
    )
    detail = None
    if detail_selected is not None:
        detail = load_selected(detail_selected)
        if len(set(detail)) != len(detail) or len(detail) < 2:
            raise ValueError('Detail selection needs at least two distinct tip IDs')
        if not set(detail).issubset(ids):
            raise ValueError('Detail selection must be a subset of the full selected-genomes file')
    summary = draw(graph,layout,meta,ids,cfg,out)
    original_edges = {frozenset((node,nb)) for node,nbrs in graph.adjacency.items()
                      for nb,_ in nbrs}
    plotted_edges = {frozenset((p,c)) for p,c,_ in layout.edges}
    assert len(plotted_edges) == len(layout.edges) == len(original_edges)
    assert plotted_edges == original_edges, 'Plot edges differ from original topology'
    deviations = [abs(math.dist(layout.coordinates[p],layout.coordinates[c]) -
                      layout.display_lengths[frozenset((p,c))])
                  for p,c,_ in layout.edges]
    max_display_error = max(deviations,default=0)
    assert max_display_error <= 1e-10, 'Displayed edge length inaccurate'
    max_error = (max((abs(math.dist(layout.coordinates[p],layout.coordinates[c])-length)
                      for p,c,length in layout.edges),default=0)
                 if layout.length_mode == 'original' else None)
    assert max_error is None or max_error <= 1e-10, 'Original edge length changed in plot'
    def digest(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    original_lengths = [length for _,_,length in layout.edges]
    summary['validation'] = {
        'tip_ids_unique': len(graph.tips)==len(set(graph.tips)),
        'all_original_edges_retained': True,
        'original_edges_retained': len(plotted_edges),
        'zero_length_edges': sum(length == 0 for length in original_lengths),
        'max_absolute_edge_length_error': max_error,
        'max_absolute_display_length_error': max_display_error,
        'display_distances_are_evolutionary': layout.length_mode == 'original',
        'original_edge_lengths_retained_in_graph': True,
    }
    summary['input_sha256'] = {
        'tree': digest(tree), 'metadata': digest(metadata),
        'selected': digest(selected),
        'config': digest(config) if config else None,
    }
    summary['layout_parameters'] = cfg['layout']
    summary['display_length_transform'] = (None if layout.length_mode == 'original' else {
        'meaning': 'NON-METRIC VISUALIZATION: plotted distances are not evolutionary',
        'formula': '0.36 + 0.63 * log1p(length / scale)**0.64',
        'scale': layout.display_scale,
        'scale_from': 'median positive original branch length',
        'zero_length_edges_expanded': True,
    })
    summary['cloud_parameters'] = cfg['cloud']
    summary['export_parameters'] = cfg['export']
    summary['output_sha256'] = {
        ext: digest(Path(out).with_suffix('.'+ext)) for ext in ('svg','pdf','png')
    }
    summary['style_parameters'] = {
        key:cfg['style'][key] for key in ('preset','density_overlay','density_opacity',
                                        'species_background')
    }
    report = Path(out).with_suffix('.provenance.json')
    if detail is not None:
        detail_cfg = copy.deepcopy(cfg)
        detail_cfg['style']['zoom_to_selected'] = True
        detail_cfg['style']['title'] = 'PhyloCloud  /  selected-genome neighbourhood'
        detail_cfg['style']['subtitle'] = 'Crop of the full-tree display coordinates (no second layout)'
        detail_out = str(out) + '_detail'
        detail_info = draw(graph, layout, meta, ids, detail_cfg, detail_out, focus_ids=detail)
        assert detail_info['foreground_original_edge_ids'] == summary['foreground_original_edge_ids']
        assert detail_info['coordinate_sha256'] == summary['coordinate_sha256']
        detail_info['input_sha256'] = {**summary['input_sha256'], 'detail_selected':digest(detail_selected)}
        detail_info['configuration'] = detail_cfg
        detail_info['validation'] = summary['validation']
        detail_info['output_sha256'] = {
            ext:digest(Path(detail_out).with_suffix('.'+ext)) for ext in ('svg','pdf','png')}
        Path(detail_out).with_suffix('.provenance.json').write_text(
            json.dumps(detail_info,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        from .panels import compose_preview
        composition = compose_preview(str(out)+'.png',detail_out+'.png',str(out)+'_overview_detail.png')
        summary['detail_panel'] = {
            'selected_tip_ids': detail,
            'highlighted_tip_ids': ids,
            'same_foreground_edge_set': True,
            'coordinate_sha256': detail_info['coordinate_sha256'],
            'view_bounds': detail_info['view_bounds'],
            'provenance_json': detail_out+'.provenance.json',
            'output_sha256': detail_info['output_sha256'],
            'full_tree_edges': detail_info['tree_edges'],
            'selected_subtree_edges': detail_info['foreground_edges'],
            'same_layout': True,
            'vector_detail_svg': detail_out+'.svg',
            'vector_detail_pdf': detail_out+'.pdf',
            **composition,
        }
    if species_panels is not None:
        from .species_panels import draw_species_panels
        summary['species_panels'] = draw_species_panels(
            graph, layout, meta, ids, str(out) + '_species_panels.png',
            group_by=cfg['cloud'].get('group_by', 'species'),
            max_panels=species_panels, style=cfg['style']['preset'],
            cloud_cfg=cfg['cloud'], species_colors=cfg['style']['species_colors'])
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
    plot.add_argument('--detail-selected',help='Subset of --selected to frame and label in a crop; preserves the full selected foreground')
    plot.add_argument('--style',choices=['publication','soft_cloud','cloud','canopy','constellation','river'])
    plot.add_argument('--cloud-group-by',help='Metadata column for native cloud colours and labels (default species)')
    plot.add_argument('--species-panels',type=int,metavar='N',
                      help='Write a companion PNG with 1–6 automatic reference-category neighbourhood panels')
    plot.add_argument('--length-mode',choices=['original','graphic'],
                      help='original branch lengths (default) or NON-METRIC graphical expansion')
    plot.add_argument('--out',required=True,help='Output stem (no file extension)')
    demo=sub.add_parser('demo',help='Create reproducible synthetic inputs and preview')
    demo.add_argument('--outdir',default='outputs/demo')
    demo.add_argument('--seed',type=int,default=47)
    demo.add_argument('--style',choices=['publication','soft_cloud','cloud','canopy','constellation','river'],default='cloud')
    demo.add_argument('--references',type=int,default=900)
    demo.add_argument('--length-mode',choices=['original','graphic'],default='original')
    args=parser.parse_args(argv)
    if args.command=='demo':
        paths=make_demo(args.outdir,args.seed,args.references)
        result=run_plot(paths['tree'],paths['metadata'],paths['selected'],paths['config'],
                        Path(args.outdir)/'phylocloud_demo',style=args.style,length_mode=args.length_mode)
    else:
        result=run_plot(args.tree,args.metadata,args.selected,args.config,args.out,
                        style=args.style,cloud_group_by=args.cloud_group_by,detail_selected=args.detail_selected,
                        length_mode=args.length_mode,species_panels=args.species_panels)
    print(json.dumps(result,indent=2))
    return result


def console_main():
    """Set the installed console-script exit code, keeping main()'s stats API.

    setuptools console_scripts wraps its target with sys.exit(...).
    Returning a result dictionary would print it as a stderr error and exit 1,
    even when plotting succeeded.
    """
    main()
    return 0


if __name__=='__main__':
    console_main()
