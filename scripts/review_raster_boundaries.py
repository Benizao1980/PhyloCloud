"""Matched synthetic exports against merged PR #22; large files stay in outputs/.

Run from the repository root. Only the compact JPEG/summary need be committed.
"""
import argparse
import copy
import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
import subprocess
import types
from unittest.mock import patch

import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from phylocloud.data import load_config, load_metadata, load_selected, PRESETS
from phylocloud.geometry import TreeGraph, equal_arc_layout, connecting_edges
from phylocloud.render import draw
from phylocloud.synthetic import make_demo

BASELINE = '74b49b65d19c90728df83ddaa6d93c110070363b'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def baseline_module(name):
    module=types.ModuleType('phylocloud.'+name)
    module.__package__='phylocloud'
    source=subprocess.check_output(
        ['git','show',f'{BASELINE}:src/phylocloud/{name}.py'],text=True)
    exec(compile(source,'<PR22 baseline '+name+'>','exec'),module.__dict__)
    return module


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--outdir',default='outputs/raster_boundaries_v1')
    args=parser.parse_args()
    out=Path(args.outdir)
    out.mkdir(parents=True,exist_ok=False)  # never overwrite prior review outputs
    paths=make_demo(out/'inputs',seed=47,reference_count=900)
    graph=TreeGraph.from_newick(paths['tree'])
    metadata=load_metadata(paths['metadata']); selected=load_selected(paths['selected'])
    cfg=load_config(None)
    cfg['export'].update(width_inches=7.1,height_inches=5.5,dpi=300)
    cfg['style'].update(title='Synthetic reference cloud',subtitle='')
    layout=equal_arc_layout(graph,rotate_degrees=cfg['layout']['rotation_degrees'])
    coords=dict(layout.coordinates); edges=list(layout.edges)
    adjacency={n:list(v) for n,v in graph.adjacency.items()}
    selection=connecting_edges(graph,selected)
    old_cloud=baseline_module('cloud_layers'); old_render=baseline_module('render')
    old_render.add_native_cloud=old_cloud.add_native_cloud
    old_render.label_cloud_groups=old_cloud.label_cloud_groups
    old_render._blur_float_counts=old_cloud._blur_float_counts
    real_close=plt.close
    reports={}
    configurations={}
    for style in ('cloud','canopy','soft_cloud'):
        style_cfg=copy.deepcopy(cfg)
        style_cfg['style'].update(PRESETS[style]); style_cfg['style']['preset']=style
        configurations[style]=style_cfg
        for label,renderer in [('before',old_render.draw),('after',draw)]:
            metrics={}
            def capture_close(fig=None):
                if hasattr(fig,'axes'):
                    images=fig.axes[0].images
                    metrics['outer_edge_max_alpha']=max((
                        float(max(a[0].max(),a[-1].max(),a[:,0].max(),a[:,-1].max()))
                        for im in images for a in [np.asarray(im.get_array())[:,:,3]]),default=0.)
                return real_close(fig)
            stem=out/(style+'_'+label)
            with patch('matplotlib.pyplot.close',capture_close):
                report=renderer(graph,layout,metadata,selected,style_cfg,stem)
            assert layout.coordinates==coords and layout.edges==edges
            assert graph.adjacency==adjacency and connecting_edges(graph,selected)==selection
            report['output_sha256']={ext:digest(stem.with_suffix('.'+ext)) for ext in ('svg','pdf','png')}
            report['input_sha256']={k:digest(paths[k]) for k in ('tree','metadata','selected')}
            report['configuration']=style_cfg
            report['boundary_check']=metrics
            reports[style+'_'+label]=report
            stem.with_suffix('.provenance.json').write_text(json.dumps(report,indent=2)+'\n')
        before,after=(reports[style+'_'+label] for label in ('before','after'))
        for key in ('tree_edges','foreground_edges','reference_genomes','native_cloud_labels'):
            assert before[key]==after[key],(style,key)
        assert after['boundary_check']['outer_edge_max_alpha']<1e-6

    width,height=640,500
    preview=Image.new('RGB',(2*width,3*height),'white')
    pen=ImageDraw.Draw(preview)
    font=ImageFont.truetype(font_manager.findfont('DejaVu Sans'),16)
    for row,style in enumerate(('cloud','canopy','soft_cloud')):
        for col,label in enumerate(('before','after')):
            with Image.open(out/(style+'_'+label+'.png')) as source:
                image=source.convert('RGB')
            image.thumbnail((width,height-36),Image.Resampling.LANCZOS)
            preview.paste(image,(col*width+(width-image.width)//2,row*height+36))
            pen.text((col*width+18,row*height+8),f'{style} / {label}',font=font,fill='#2F2A26')
    preview.save(out/'comparison.jpg',quality=82,optimize=True)
    index={n:i for i,n in enumerate(graph.adjacency)}
    def edge_ids(es):
        return sorted(sorted(index[n] for n in e) for e in es)
    original_edges={frozenset((n,nb)) for n,neighbours in adjacency.items() for nb,_ in neighbours}
    assert {frozenset((p,c)) for p,c,_ in edges}==original_edges
    max_error=max(abs(math.dist(coords[p],coords[c])-length) for p,c,length in edges)
    assert max_error<1e-10
    manifest={
        'baseline_commit':BASELINE,'synthetic_seed':47,'references':900,'selected_tips':selected,
        'scientific_before_after_equal':True,'tree_edges':len(edges),
        'selected_original_edges':edge_ids(selection),
        'edge_identity_scheme':'input_graph_node_insertion_indices',
        'node_coordinate_sha256':hashlib.sha256(json.dumps(
            [(index[n],xy) for n,xy in coords.items()]).encode()).hexdigest(),
        'input_sha256':{k:digest(paths[k]) for k in ('tree','metadata','selected')},
        'configurations':configurations,
        'validation':{'all_original_edges_retained':True,
                      'coordinates_and_selected_edges_unchanged':True,
                      'max_absolute_edge_length_error':max_error},
        'source_sha256':{p:digest(p) for p in ('src/phylocloud/cloud_layers.py',
                                             'src/phylocloud/render.py','src/phylocloud/data.py')},
        'dependencies':{p:version(p) for p in ('numpy','matplotlib','biopython','Pillow')},
        'comparisons':{style:{label:{
            'outer_edge_max_alpha':reports[style+'_'+label]['boundary_check']['outer_edge_max_alpha'],
            'density_raster':reports[style+'_'+label].get('density_raster'),
            'output_sha256':reports[style+'_'+label]['output_sha256']}
            for label in ('before','after')} for style in ('cloud','canopy','soft_cloud')},
        'preview_sha256':digest(out/'comparison.jpg'),
        'render_method':'vector_tree_and_text_with_embedded_raster_wash',
    }
    (out/'summary.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'outdir':str(out),'preview_bytes':(out/'comparison.jpg').stat().st_size,
                      'scientific_before_after_equal':True,
                      'boundaries':{k:r['boundary_check'] for k,r in reports.items()}},indent=2))


if __name__=='__main__':
    main()
