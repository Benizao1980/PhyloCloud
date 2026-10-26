"""Full-size detail review: one synthetic graph/layout, unchanged focal edges."""
import argparse
import copy
import json
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from phylocloud.benchmark import make_structure_benchmark
from phylocloud.data import load_config, load_metadata, load_selected, PRESETS
from phylocloud.geometry import TreeGraph, equal_arc_layout
from phylocloud.render import draw
from review_structure_benchmark import digest, scientific_audit


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--outdir',required=True)
    parser.add_argument('--tight',action='store_true',help='Omit reference context to expose tight-zoom wash limitations')
    args=parser.parse_args(); out=Path(args.outdir); out.mkdir(parents=True,exist_ok=False)
    inputs=make_structure_benchmark(out/'inputs')
    graph=TreeGraph.from_newick(inputs['tree']); metadata=load_metadata(inputs['metadata'])
    selected=load_selected(inputs['selected']); focus=selected[:6]
    layout=equal_arc_layout(graph,19); audit=scientific_audit(graph,layout,selected)
    cfg=load_config(None); cfg['layout']['rotation_degrees']=19
    cfg['export'].update(width_inches=12,height_inches=11,dpi=300)
    # Context is selected geometrically from two explicitly synthetic populations,
    # not inferred as nearest relatives. Include their extremal original tips so
    # the crop contains local reference structure, not only the focal endpoints.
    candidates=[n for n,r in metadata.items() if r['group']=='reference' and r['population'] in ('P01','P02')]
    context=sorted({extreme(candidates,key=lambda n:layout.coordinates[graph.tips[n]][axis])
                    for axis in (0,1) for extreme in (min,max)})
    if args.tight: context=[]
    original_close=plt.close; held=[]; reports={}
    cases=[('overview','cloud',selected,None,False),
           ('before_subset','cloud',focus,None,True),
           ('detail_tree','publication',selected,focus,True),
           ('detail_cloud','cloud',selected,focus,True),
           ('detail_canopy','canopy',selected,focus,True)]
    try:
        for name,preset,highlighted,labels,zoom in cases:
            config=copy.deepcopy(cfg); config['style'].update(PRESETS[preset])
            config['style'].update(preset=preset,composition='publication',zoom_to_selected=zoom,
                title={'overview':'Cloud — complete-tree context','before_subset':'Before — subset foreground',
                       'detail_tree':'Detail — complete underlying tree','detail_cloud':'Detail — Cloud',
                       'detail_canopy':'Detail — Canopy'}[name],
                subtitle='6,500 synthetic tips · original coordinates · geometric crop' if zoom else
                         '6,500 synthetic tips · original coordinates · full overview')
            if zoom: config['style']['context_reference_ids']=context
            if preset=='publication':
                config['style'].update(reference_color='warm_grey',reference_alpha=.85,
                                       reference_width=.28,halo_alpha=0.)
            saves=[]; figures=[]
            with patch('matplotlib.figure.Figure.savefig',lambda fig,*a,**kw:saves.append((a,kw))), \
                 patch('matplotlib.pyplot.close',lambda fig=None:figures.append(fig) if hasattr(fig,'axes') else None):
                report=draw(graph,layout,metadata,highlighted,config,out/name,focus_ids=labels)
            held.append((name,figures[-1],saves)); reports[name]=report
            assert scientific_audit(graph,layout,selected)==audit
            report.update(configuration=config,input_sha256={k:digest(p) for k,p in inputs.items()})
        details=[(n,f,s) for n,f,s in held if n!='overview']
        bounds=[reports[n]['view_bounds'] for n,_,_ in details]
        shared=[min(b[0] for b in bounds),max(b[1] for b in bounds),
                min(b[2] for b in bounds),max(b[3] for b in bounds)]
        boxes=[f.axes[0].get_position(original=True) for _,f,_ in details]
        box=[max(b.x0 for b in boxes),max(b.y0 for b in boxes),min(b.x1 for b in boxes),min(b.y1 for b in boxes)]
        transform=None
        for name,fig,saves in held:
            ax=fig.axes[0]
            if name!='overview':
                ax.set_position([box[0],box[1],box[2]-box[0],box[3]-box[1]])
                ax.set_xlim(*shared[:2]); ax.set_ylim(*shared[2:]); fig.canvas.draw()
                current=ax.transData.get_affine().get_matrix()
                if transform is not None: np.testing.assert_allclose(current,transform,atol=1e-10)
                transform=current
                reports[name]['view_bounds']=shared
            fig.canvas.draw(); fig._phylocloud_place_labels(); fig.canvas.draw()
            annotation=fig._phylocloud_annotation_check()
            assert annotation['text_box_overlaps']==annotation['clipped_text_boxes']==0
            reports[name]['annotation_layout']=annotation
            for a,kw in saves: fig.savefig(*a,**kw)
            report=reports[name]
            report['output_sha256']={ext:digest(out/(name+'.'+ext)) for ext in ('svg','pdf','png')}
            ns={'s':'http://www.w3.org/2000/svg'}; svg=ET.parse(out/(name+'.svg'))
            for gid,count in [('reference-tree-edges',audit['original_edges']),
                              ('selected-original-edges',report['foreground_edges'])]:
                group=svg.find(f".//s:g[@id='{gid}']",ns)
                assert len(group.findall('s:path',ns))==count
            with Image.open(out/(name+'.png')) as im:
                preview=im.convert('RGB'); preview.thumbnail((2400,2400),Image.Resampling.LANCZOS)
                preview.save(out/(name+'.jpg'),quality=90,optimize=True)
            (out/(name+'.provenance.json')).write_text(json.dumps(report,indent=2)+'\n')
        for name in ('detail_tree','detail_cloud','detail_canopy'):
            assert reports[name]['foreground_original_edge_ids']==reports['overview']['foreground_original_edge_ids']
            assert reports[name]['coordinate_sha256']==reports['overview']['coordinate_sha256']
        assert reports['detail_cloud']['density_raster']==reports['overview']['density_raster']
        summary=dict(scientific_audit=audit,focus_tip_ids=focus,context_reference_ids=context,shared_detail_bounds=shared,
                     same_foreground_edges_in_overview_and_details=True,
                     same_detail_data_to_display_transform=True,
                     before_foreground_edges=reports['before_subset']['foreground_edges'],
                     after_foreground_edges=reports['detail_cloud']['foreground_edges'],
                     source_sha256={str(p):digest(p) for p in [Path('scripts/review_fixed_selection_detail.py'),Path('src/phylocloud/render.py'),
                                     Path('src/phylocloud/composition.py'),Path('src/phylocloud/cli.py')]},
                     views={n:{k:r[k] for k in ('output_sha256','view_bounds','foreground_edges',
                              'coordinate_sha256','labelled_tip_ids','highlighted_tip_ids','annotation_layout')}
                            for n,r in reports.items()})
        (out/'review.json').write_text(json.dumps(summary,indent=2)+'\n')
        print(json.dumps({k:v for k,v in summary.items() if k in ('before_foreground_edges','after_foreground_edges','shared_detail_bounds')},indent=2))
    finally:
        for _,fig,_ in held: original_close(fig)


if __name__=='__main__': main()
