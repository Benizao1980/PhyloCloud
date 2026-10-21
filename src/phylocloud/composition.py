"""Measured publication annotations; moves text and camera, never tree vertices."""
from __future__ import annotations
from collections import Counter
import math
import textwrap

from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.transforms import Bbox

from .cloud_layers import colour_for_group
from .data import color


def _pack_vertical(targets, heights, lower, upper, gap):
    """Order-preserving deterministic packing in display units, with hard limits."""
    if not targets:
        return []
    if sum(heights)+gap*(len(heights)-1)>upper-lower:
        raise ValueError('Focal labels do not fit; increase export height or reduce label_font_size')
    packed=[]
    for i,(target,height) in enumerate(zip(targets,heights)):
        floor=lower+height/2 if i==0 else packed[-1]+(heights[i-1]+height)/2+gap
        packed.append(max(target,floor))
    packed[-1]=min(packed[-1],upper-heights[-1]/2)
    for i in range(len(packed)-2,-1,-1):
        packed[i]=min(packed[i],packed[i+1]-(heights[i]+heights[i+1])/2-gap)
    return packed


def focus_crop_bounds(points):
    """Existing publication camera policy; no tree coordinate is modified."""
    xs, ys = zip(*points)
    xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
    span = max(xmax-xmin, ymax-ymin)
    if span <= 0:
        raise ValueError('Selected genomes have coincident plotted positions; cannot zoom')
    pad = span*.035
    return [xmin-pad, xmax+pad, ymin-pad, ymax+pad]


def publication_composition(fig, ax, graph, layout, metadata, selected, references,
                            context, cfg, density_raster, original_bounds, *, focus_ids=None):
    """Draw margin callouts, a separate metadata key, and measured page regions.

    Coincident tips share an explicitly disclosed callout; their true markers
    and original zero-length edges are preserved. Disjoint taxonomic categories
    are listed in a key, never given a single supposed clade/region label.
    """
    focus = selected if focus_ids is None else focus_ids
    s=cfg['style']; ink=color(s.get('foreground_color','ink'))
    bg=s.get('background','#FFFFFF'); point=fig.dpi/72
    fw,fh=fig.bbox.width,fig.bbox.height
    if fw/point<360 or fh/point<360:
        raise ValueError('Publication composition requires a canvas at least 5 inches per side')
    title=fig.text(22*point/fw,1-22*point/fh,s['title'],fontsize=16,weight='bold',
                   ha='left',va='top',color=ink)
    subtitle=fig.text(22*point/fw,1-46*point/fh,s.get('subtitle',''),fontsize=9,
                      ha='left',va='top',color=color('warm_grey'))
    field=cfg['cloud'].get('group_by','species')
    counts=Counter(metadata.get(n,{}).get(field) or 'Unassigned' for n in references)
    categories=sorted(counts,key=lambda k:(-counts[k],k))
    # Fixed typographic bands use points, not data-coordinate approximations.
    # Long category labels wrap and the row height follows measured extents.
    fig.canvas.draw(); renderer=fig.canvas.get_renderer()
    columns=3
    colwidth=(fw-44*point)/columns
    category_art=[]; category_height=0.
    for i,name in enumerate(categories):
        label=f'{name}  (n={counts[name]:,})'
        label=textwrap.fill(label,width=max(14,int(colwidth/(4.4*point))))
        artist=fig.text(0,0,label,fontsize=8.2,ha='left',va='bottom',color=ink)
        category_art.append(artist)
        category_height=max(category_height,artist.get_window_extent(renderer).height)
    rowheight=category_height+7*point
    rows=math.ceil(len(categories)/columns)
    category_bottom=47*point
    for i,artist in enumerate(category_art):
        row,col=divmod(i,columns)
        x=31*point+col*colwidth; y=category_bottom+(rows-1-row)*rowheight
        artist.set_position((x/fw,y/fh))
        group=categories[i]
        dot=Line2D([(x-8*point)/fw],[(y+4*point)/fh],transform=fig.transFigure,
                   marker='s',ms=5,linestyle='None',color=colour_for_group(group,cfg['cloud'],s['species_colors']))
        fig.add_artist(dot)
    semantic_y=category_bottom+rows*rowheight+15*point
    semantic=[]
    keys=[('Original reference edges',color(s.get('reference_color','stone'))),
          ('Exact focal connecting edges',ink),
          (f'Focal genomes: {len(selected)}'+(f' ({len(focus)} labelled)' if len(focus)!=len(selected) else ''),ink)]
    for col,(label,c) in enumerate(keys):
        x=22*point+col*colwidth
        fig.add_artist(Line2D([x/fw,(x+16*point)/fw],[semantic_y/fh]*2,
                             transform=fig.transFigure,color=c,lw=1.4,
                             marker='o' if col==2 else None,ms=3))
        semantic.append(fig.text((x+22*point)/fw,semantic_y/fh,label,fontsize=8.3,
                                  va='center',ha='left',color=ink))
    nonmetric=getattr(layout,'length_mode','original')!='original'
    method=('Non-metric graphic lengths' if nonmetric else 'Original branch lengths')
    angle=cfg['layout'].get('angle_mode','tip_count')
    method+=' · '+('equal-arc' if angle=='tip_count' else 'experimental phylogenetic-spread angles')
    method+=' · one shared layout'
    if s.get('zoom_to_selected',False): method='Geometric crop; global counts · '+method
    if density_raster and density_raster.get('normalization_domain')=='viewport_plus_finite_kernel_support':
        method=('Crop; global counts · '+method.split('Geometric crop; global counts · ')[-1]
                .replace(' · one shared layout','')+' · local wash normalization')
    footer=[fig.text(22*point/fw,27*point/fh,method,fontsize=7.5,color=color('warm_grey')),
            fig.text(22*point/fw,14*point/fh,'Reference sampling density is not prevalence; metadata colours do not define clades.',
                     fontsize=7.5,color=color('warm_grey'))]
    # Build callouts at true positions; no nearest-neighbour collapsing/jitter.
    groups={}
    for name in focus:
        xy=layout.coordinates[graph.tips[name]]
        groups.setdefault(xy,[]).append(name)
    entries=[]
    for xy,names in groups.items():
        labels=[metadata.get(n,{}).get('label') or n for n in names]
        label=' / '.join(labels)
        if len(names)>1: label+='\n(coincident tips)'
        label='\n'.join(textwrap.fill(line,width=34) for line in label.splitlines())
        entries.append(dict(ids=names,xy=xy,label=label))
    for name in context:
        xy=layout.coordinates[graph.tips[name]]
        ax.scatter([xy[0]],[xy[1]],s=45,facecolors='white',edgecolors=color('burgundy'),zorder=7)
        entries.append(dict(ids=[name],xy=xy,label=textwrap.fill(name,width=34)))
    texts=[]
    for entry in entries:
        t=fig.text(0,0,entry['label'],fontsize=s['label_font_size'],ha='left',va='center',
                   color=ink,weight='normal',linespacing=1.35,
                   bbox={'facecolor':bg,'edgecolor':'none','pad':2})
        texts.append(t)
    fig.canvas.draw(); renderer=fig.canvas.get_renderer()
    dimensions=[t.get_window_extent(renderer) for t in texts]
    rail=max((b.width for b in dimensions),default=0.)+38*point
    bottom=(semantic_y+24*point)/fh; top=1-72*point/fh
    if 2*rail>fw*.66 or top-bottom<.3:
        raise ValueError('Publication annotations do not fit; increase canvas dimensions')
    ax.set_position([rail/fw,bottom,1-2*rail/fw,top-bottom])
    xmin,xmax,ymin,ymax=original_bounds
    if s.get('zoom_to_selected',False):
        pad=max(xmax-xmin,ymax-ymin)*.035
        view=focus_crop_bounds([layout.coordinates[graph.tips[n]] for n in focus+context])
    else:
        if density_raster and density_raster['visible_bounds']:
            wash=density_raster['visible_bounds']
            xmin,xmax,ymin,ymax=min(xmin,wash[0]),max(xmax,wash[1]),min(ymin,wash[2]),max(ymax,wash[3])
        pad=max(xmax-xmin,ymax-ymin)*.035
        view=[xmin-pad,xmax+pad,ymin-pad,ymax+pad]
    ax.set_xlim(*view[:2]); ax.set_ylim(*view[2:]); ax.set_aspect('equal',adjustable='box'); ax.axis('off')
    if s.get('zoom_to_selected',False):
        ax.add_patch(Rectangle((0,0),1,1,transform=ax.transAxes,fill=False,
                               edgecolor=color('warm_grey'),linewidth=.6,zorder=12,
                               clip_on=False,gid='geometric-crop-frame'))
    fig.canvas.draw(); renderer=fig.canvas.get_renderer()
    # Limits/camera may be replaced by a matched-review script before export.
    # A draw callback keeps callouts attached under that shared camera change.
    def place(event=None):
        bounds=ax.get_window_extent(); cx=layout.coordinates[layout.centre][0]
        for side in (-1,1):
            indices=[i for i,e in enumerate(entries) if (1 if e['xy'][0]>=cx else -1)==side]
            indices.sort(key=lambda i:(ax.transData.transform(entries[i]['xy'])[1],entries[i]['ids']))
            heights=[dimensions[i].height+4*point for i in indices]
            ys=[ax.transData.transform(entries[i]['xy'])[1] for i in indices]
            positions=_pack_vertical(ys,heights,bounds.y0+6*point,bounds.y1-6*point,5*point)
            x=bounds.x1+14*point if side==1 else bounds.x0-14*point
            for i,y in zip(indices,positions):
                texts[i].set_position((x/fw,y/fh)); texts[i].set_ha('left' if side==1 else 'right')
                start=ax.transData.transform(entries[i]['xy'])
                elbow=x-side*8*point
                leaders[i].set_data([start[0]/fw,elbow/fw,(x-side*4*point)/fw],
                                    [start[1]/fh,y/fh,y/fh])
    leaders=[]
    for entry in entries:
        leader=Line2D([],[],transform=fig.transFigure,color=color('warm_grey'),lw=.55,
                      alpha=.75,linestyle=(0,(2,2)),zorder=4)
        fig.add_artist(leader); leaders.append(leader)
    scale=s.get('scale_bar')
    scale_text=[]
    if scale:
        length=float(scale['length'])
        if not math.isfinite(length) or length<=0:
            raise ValueError('scale_bar.length must be positive and finite')
        ox,oy=view[0]+pad*.5,view[2]+pad*.5
        ax.plot([ox,ox+length],[oy,oy],color=ink,lw=1.,zorder=11)
        scale_text.append(ax.text(ox,oy+pad*.25,f"{length:g} {scale.get('units','branch-length units')}",
                                  fontsize=7.5,ha='left',va='bottom',color=ink))
    place()
    fig._phylocloud_place_labels=place
    fig.canvas.draw()
    all_text=[title,subtitle,*texts,*category_art,*semantic,*footer,*scale_text]
    def inspect():
        renderer=fig.canvas.get_renderer()
        boxes=[t.get_window_extent(renderer).expanded(1.01,1.05) for t in all_text if t.get_text()]
        collisions=sum(a.overlaps(b) for i,a in enumerate(boxes) for b in boxes[i+1:])
        canvas=Bbox.from_bounds(0,0,fw,fh)
        clipped=sum(not (canvas.contains(b.x0,b.y0) and canvas.contains(b.x1,b.y1)) for b in boxes)
        return dict(mode='publication',text_box_overlaps=int(collisions),clipped_text_boxes=int(clipped),
                    label_groups=[dict(ids=e['ids'],anchor_xy=list(e['xy']),text=e['label']) for e in entries],
                    coincident_tip_policy='shared disclosed callout; original markers and edges unchanged',
                    taxonomy_labels='separate metadata key, no implied single clade',
                    reference_group_counts=dict(counts),view_bounds=[*ax.get_xlim(),*ax.get_ylim()],
                    canvas_inches=list(fig.get_size_inches()),font_family='DejaVu Sans',
                    minimum_text_size_pt=min(7.5,s['label_font_size']))
    result=inspect()
    if result['text_box_overlaps'] or result['clipped_text_boxes']:
        raise ValueError('Publication annotations overlap or clip; increase canvas dimensions')
    # Used by the matched-review runner after it installs a common camera.
    fig._phylocloud_annotation_check=inspect
    return result
