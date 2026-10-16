"""Full-size complete-tree/Cloud/Canopy review on ONE synthetic LayoutMap.

Run: python scripts/review_structure_benchmark.py --outdir outputs/structure_review_v1
Large SVG/PDF/PNG remain ignored; review JPEGs are individual full-page images.
"""
import argparse
import copy
import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from phylocloud.benchmark import make_structure_benchmark
from phylocloud.data import load_config, load_metadata, load_selected, PRESETS
from phylocloud.geometry import TreeGraph, equal_arc_layout, connecting_edges
from phylocloud.render import draw


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def scientific_audit(graph, layout, selected):
    """Independent union-of-paths foreground oracle; exact original-edge audit."""
    original = {frozenset((a,b)):length for a, neighbours in graph.adjacency.items()
                for b,length in neighbours}
    displayed = {frozenset((a,b)):length for a,b,length in layout.edges}
    assert displayed == original
    assert len(layout.coordinates) == len(graph.adjacency)
    error = max(abs(math.dist(layout.coordinates[a],layout.coordinates[b])-length)
                for a,b,length in layout.edges)
    assert error < 1e-10
    start = graph.tips[selected[0]]; parents = {start:None}; distances = {start:0.}
    for node in (order := [start]):
        for other,length in graph.adjacency[node]:
            if other not in parents:
                parents[other] = node; distances[other] = distances[node]+length
                order.append(other)
    expected = set()
    for name in selected[1:]:
        node = graph.tips[name]
        while parents[node] is not None:
            parent = parents[node]; expected.add(frozenset((node,parent))); node=parent
    assert expected == connecting_edges(graph,selected)
    index = {n:i for i,n in enumerate(graph.adjacency)}
    # Compare exact graph identities rather than materializing every split.
    # Exact undirected edge identity equality above guarantees the same splits,
    # including zero-length edges, without an O(N^2) all-pairs matrix.
    coordinates = [[index[n],*layout.coordinates[n]] for n in graph.adjacency]
    foreground = sorted(sorted(index[n] for n in edge) for edge in expected)
    return dict(tips=len(graph.tips), original_edges=len(original),
                zero_length_edges=sum(length==0 for length in original.values()),
                exact_original_edge_identities_and_lengths=True,
                unrooted_splits_preserved_by_exact_graph_identity=True,
                max_absolute_edge_length_error=error,
                selected_original_edge_ids=foreground,
                selected_edge_oracle='independent union of paths from first focal tip',
                focal_patristic_distances_from_first={name:distances[graph.tips[name]] for name in selected},
                coordinate_sha256=hashlib.sha256(json.dumps(coordinates).encode()).hexdigest())


def render_review(out, paths, dpi=300, composition='publication'):
    graph=TreeGraph.from_newick(paths['tree']); metadata=load_metadata(paths['metadata'])
    selected=load_selected(paths['selected']); cfg=load_config(None)
    cfg['export'].update(width_inches=14,height_inches=11,dpi=dpi)
    cfg['layout'].update(rotation_degrees=19,angle_mode='tip_count',length_mode='original')
    # The layout is constructed ONCE, with NO style-specific geometry.
    layout=equal_arc_layout(graph,19,angle_mode='tip_count')
    audit=scientific_audit(graph,layout,selected)
    coords=dict(layout.coordinates); edges=list(layout.edges)
    held=[]; reports={}; configurations={}
    original_close=plt.close
    try:
        for preset in ('publication','cloud','canopy'):
            config=copy.deepcopy(cfg); config['style'].update(PRESETS[preset])
            config['style'].update(preset=preset,composition=composition,
                title={'publication':'Complete underlying phylogeny','cloud':'Cloud — structural stress test',
                       'canopy':'Canopy — structural stress test'}[preset],
                subtitle='6,500 synthetic tips · mixed taxonomy · one original-length layout')
            if composition=='publication':
                config['export']['width_inches']=12
                if preset=='publication':
                    config['style'].update(reference_color='warm_grey',reference_alpha=.85,
                                           reference_width=.28,halo_alpha=0.)
            configurations[preset]=config
            saves=[]; figures=[]
            # Defer export until all three views have a common camera.
            with patch('matplotlib.figure.Figure.savefig',lambda fig,*a,**kw:saves.append((a,kw))), \
                 patch('matplotlib.pyplot.close',lambda fig=None:figures.append(fig) if hasattr(fig,'axes') else None):
                reports[preset]=draw(graph,layout,metadata,selected,config,out/preset)
            held.append((preset,figures[-1],saves))
            assert layout.coordinates==coords and layout.edges==edges
            assert scientific_audit(graph,layout,selected)==audit
        bounds=[r['view_bounds'] for r in reports.values()]
        shared=[min(b[0] for b in bounds),max(b[1] for b in bounds),
                min(b[2] for b in bounds),max(b[3] for b in bounds)]
        axes_boxes=[fig.axes[0].get_position(original=True) for _,fig,_ in held]
        common_box=[max(b.x0 for b in axes_boxes),max(b.y0 for b in axes_boxes),
                    min(b.x1 for b in axes_boxes),min(b.y1 for b in axes_boxes)]
        transforms=[]
        for preset,fig,saves in held:
            ax=fig.axes[0]
            ax.set_position([common_box[0],common_box[1],common_box[2]-common_box[0],common_box[3]-common_box[1]])
            ax.set_xlim(*shared[:2]); ax.set_ylim(*shared[2:])
            fig.canvas.draw()
            transforms.append(ax.transData.get_affine().get_matrix().tolist())
            np.testing.assert_allclose(transforms[-1],transforms[0],atol=1e-10)

            if hasattr(fig,'_phylocloud_place_labels'):
                fig.canvas.draw(); fig._phylocloud_place_labels(); fig.canvas.draw()
                annotations=fig._phylocloud_annotation_check()
                assert annotations['text_box_overlaps']==annotations['clipped_text_boxes']==0
                reports[preset]['annotation_layout']=annotations
            for args,kwargs in saves:
                fig.savefig(*args,**kwargs)
            report=reports[preset]
            report.update(view_bounds=shared,coordinate_sha256=audit['coordinate_sha256'],
                          configuration=configurations[preset],input_sha256={k:digest(p) for k,p in paths.items()},
                          output_sha256={ext:digest((out/preset).with_suffix('.'+ext)) for ext in ('svg','pdf','png')})
            # Every original edge is still an SVG path, including zero lengths.
            ns={'s':'http://www.w3.org/2000/svg'}
            svg=ET.parse(out/(preset+'.svg'))
            for gid,n in [('reference-tree-edges',len(edges)),
                          ('selected-original-edges',report['foreground_edges'])]:
                group=svg.find(f".//s:g[@id='{gid}']",ns)
                assert len(group.findall('s:path',ns))==n
            with Image.open(out/(preset+'.png')) as im:
                preview=im.convert('RGB'); preview.thumbnail((2400,2400),Image.Resampling.LANCZOS)
                preview.save(out/(preset+'.jpg'),quality=90,optimize=True)
            (out/(preset+'.provenance.json')).write_text(json.dumps(report,indent=2)+'\n')
    finally:
        for _,fig,_ in held: original_close(fig)
    manifest=dict(scientific_audit=audit,shared_view_bounds=shared,
                  same_layout_object_for_all_styles=True,
                  same_data_to_display_transform_for_all_styles=True,
                  data_to_display_affine_at_figure_dpi=transforms[0],
                  dependencies={p:version(p) for p in ('numpy','matplotlib','biopython','Pillow')},
                  input_sha256={k:digest(p) for k,p in paths.items()},
                  source_sha256={str(p):digest(p) for p in [Path('scripts/review_structure_benchmark.py'),Path('src/phylocloud/benchmark.py'),
                                    Path('src/phylocloud/render.py'),Path('src/phylocloud/cloud_layers.py'),
                                    Path('src/phylocloud/composition.py')]},
                  preview_sha256={preset:digest(out/(preset+'.jpg')) for preset in reports},
                  views={preset:{k:r.get(k) for k in ('density_raster','native_cloud_labels','reference_group_counts',
                                     'foreground_edges','output_sha256','annotation_layout')} for preset,r in reports.items()})
    (out/'review.json').write_text(json.dumps(manifest,indent=2)+'\n')
    links=''.join(f'<section><h2>{p}</h2><p><a href="{p}.pdf">PDF</a> · <a href="{p}.svg">SVG</a> · <a href="{p}.png">Full PNG</a></p><img src="{p}.jpg" style="width:100%;max-width:1600px"></section>' for p in reports)
    (out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>PhyloCloud structure review</title><body style="font-family:sans-serif"><h1>6,500-tip synthetic structure review</h1><p>All original edges and lengths retained. Same coordinates and camera in every view. Synthetic metadata are not biological findings.</p>'+links)
    print(json.dumps(dict(output=str(out),tips=audit['tips'],edges=audit['original_edges'],
                          foreground_edges=len(audit['selected_original_edge_ids']),
                          zero_edges=audit['zero_length_edges'],shared_bounds=shared),indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--outdir',required=True)
    parser.add_argument('--dpi',type=int,default=300)
    parser.add_argument('--composition',choices=['legacy','publication'],default='publication')
    args=parser.parse_args(); out=Path(args.outdir); out.mkdir(parents=True,exist_ok=False)
    paths=make_structure_benchmark(out/'inputs')
    render_review(out,paths,args.dpi,args.composition)


if __name__=='__main__': main()
