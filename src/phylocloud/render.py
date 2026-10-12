"""Matplotlib backend: lightweight, editable paths and text in SVG/PDF."""
from __future__ import annotations
from pathlib import Path
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D
import numpy as np
from PIL import Image, ImageFilter
from .data import color
from . import __version__
from .geometry import Layout, TreeGraph, connecting_edges, edge_taxa


def add_reference_density_overlay(ax, graph, layout, reference_ids, style):
    """Blur observed reference-tip coordinates as a display-only underlay.

    This is not an inferred branch, confidence area, or natural population
    prevalence estimate. Every original branch stays vector/editable above it.
    """
    coords = layout.coordinates
    x = np.array([p[0] for p in coords.values()], dtype=float)
    y = np.array([p[1] for p in coords.values()], dtype=float)
    xmin, xmax = float(x.min()), float(x.max())
    ymin, ymax = float(y.min()), float(y.max())
    extent = max(xmax-xmin, ymax-ymin)
    pad = max(1e-12, extent*0.024)
    xmin -= pad; xmax += pad; ymin -= pad; ymax += pad
    tips = [graph.tips[name] for name in reference_ids]
    if not tips:
        return
    tx = np.array([coords[n][0] for n in tips])
    ty = np.array([coords[n][1] for n in tips])
    size = 460
    count, _, _ = np.histogram2d(ty, tx, bins=(size,size),
                                 range=((ymin,ymax),(xmin,xmax)))
    raw = 255 * np.log1p(count) / max(1e-12, np.log1p(float(count.max())))
    luminance = Image.fromarray(np.asarray(raw,dtype=np.uint8),mode='L')
    blur = luminance.filter(ImageFilter.GaussianBlur(radius=float(style['density_sigma_px'])))
    blurred = np.asarray(blur,dtype=float) / 255
    alpha = np.clip((blurred / max(1e-12, blurred.max()))**0.65 * float(style['density_opacity']),0,1)
    rgb = np.array(to_rgba(color('stone'))[:3],dtype=float)
    image = np.empty((size,size,4),dtype=float)
    image[:,:,:3] = rgb
    image[:,:,3] = alpha
    ax.imshow(image, extent=(xmin,xmax,ymin,ymax),origin='lower',
              interpolation='bilinear',zorder=0,rasterized=True)


def draw(graph: TreeGraph, layout: Layout, metadata: dict, selected_ids: list[str],
         config: dict, output_stem: str | Path) -> dict:
    selected_edges = connecting_edges(graph, selected_ids)
    taxonomy = {k:v.get('species', '') for k,v in metadata.items()}
    taxonomy_by_edge = edge_taxa(layout, graph, taxonomy)
    s = config['style']; exp = config['export']; species_colors=s['species_colors']
    path = Path(output_stem)
    path.parent.mkdir(parents=True,exist_ok=True)
    fig, ax = plt.subplots(figsize=(exp['width_inches'], exp['height_inches']))
    fig.patch.set_facecolor('white'); ax.set_facecolor('white')
    plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none',
                         'svg.hashsalt':'phylocloud-v0.1', 'pdf.fonttype':42})
    def is_reference(name):
        src = metadata.get(name,{}).get('source','').strip().lower()
        return src == 'gtdb' or 'reference' in src
    if any(metadata.get(name,{}).get('source') for name in graph.tips):
        reference_ids = [name for name in graph.tips if is_reference(name)]
    else:
        reference_ids = [name for name in graph.tips if name not in selected_ids]
    if s.get('density_overlay', False):
        add_reference_density_overlay(ax, graph, layout, reference_ids, s)
    paths=[]; branch_colours=[]
    for parent, child, length in layout.edges:
        paths.append([layout.coordinates[parent], layout.coordinates[child]])
        taxon = taxonomy_by_edge[frozenset((parent,child))]
        if s['species_background'] and taxon in species_colors:
            branch_colours.append(color(species_colors[taxon]))
        else:
            branch_colours.append(color('stone'))
    halo = [to_rgba(c, float(s['halo_alpha'])) for c in branch_colours]
    core = [to_rgba(c, float(s['reference_alpha'])) for c in branch_colours]
    ax.add_collection(LineCollection(paths, colors=halo, linewidths=s['halo_width'], zorder=1))
    ax.add_collection(LineCollection(paths, colors=core, linewidths=s['reference_width'], zorder=2))
    fg = [[layout.coordinates[p],layout.coordinates[c]]
          for p,c,_ in layout.edges if frozenset((p,c)) in selected_edges]
    if fg:
        ax.add_collection(LineCollection(fg, colors=color(s['foreground_color']),
                                         linewidths=s['foreground_width'],alpha=.9,
                                         capstyle='round',joinstyle='round',zorder=4))
    coords = layout.coordinates
    context_ids = s.get('context_reference_ids', [])
    if not isinstance(context_ids,list):
        raise ValueError('context_reference_ids must be a list of exact tree tip IDs')
    if any(name not in graph.tips or name in selected_ids for name in context_ids):
        raise ValueError('Context reference IDs must be nonselected tips in the full tree')
    plotted=[]
    for name in selected_ids:
        x,y = coords[graph.tips[name]]
        species=taxonomy.get(name)
        face=color(species_colors.get(species,'warm_grey'))
        ax.scatter([x],[y],s=s['mag_size'],c=[face],edgecolors=color('ink'),
                   linewidths=.8,zorder=6)
        plotted.append((name,x,y,face))
    xx=[p[0] for p in coords.values()]; yy=[p[1] for p in coords.values()]
    lowx,highx=min(xx),max(xx); lowy,highy=min(yy),max(yy)
    if s.get('zoom_to_selected', False):
        xs=[coords[graph.tips[name]][0] for name in selected_ids+context_ids]
        ys=[coords[graph.tips[name]][1] for name in selected_ids+context_ids]
        lowx,highx=min(xs),max(xs); lowy,highy=min(ys),max(ys)
        span=max(highx-lowx,highy-lowy)
        if span <= 0:
            raise ValueError('Selected genomes have coincident plotted positions; cannot zoom')
        spread=span*2.2
    else:
        spread=max(highx-lowx,highy-lowy)
    center_x,center_y=coords[layout.centre]
    label_spacing=0.055*spread
    positions={}
    for name,x,y,face in plotted:
        vx,vy=x-center_x,y-center_y
        norm=math.hypot(vx,vy) or 1
        side=1 if vx>=0 else -1
        tx=x+side*0.032*spread
        ty=y+vy/norm*0.027*spread
        positions[name]=[tx,ty,side]
    for side in [-1,1]:
        group=sorted([name for name in selected_ids if positions[name][2]==side],
                     key=lambda n:positions[n][1])
        if not group: continue
        for i in range(1,len(group)):
            last,now=group[i-1],group[i]
            if positions[now][1]<positions[last][1]+label_spacing:
                positions[now][1]=positions[last][1]+label_spacing
    for name in context_ids:
        x,y=coords[graph.tips[name]]
        ax.scatter([x],[y],s=67,facecolors='white',edgecolors=color('burgundy'),
                   linewidths=1.5,zorder=7)
        ax.annotate(name.removeprefix('GTDB_'), (x,y),
                    xytext=(12,20),textcoords='offset points',
                    fontsize=8.4,color=color('burgundy'),weight='semibold',
                    arrowprops={'color':color('burgundy'),'lw':0.75},zorder=8)
    for name,x,y,face in plotted:
        tx,ty,side=positions[name]
        label=metadata.get(name,{}).get('label') or name
        ax.plot([x,tx-side*0.009*spread],[y,ty],color=face,
                alpha=.62,linewidth=.75,zorder=5)
        ax.text(tx,ty,label,fontsize=s['label_font_size'],color=color('ink'),
                ha='left' if side==1 else 'right',va='center',weight='semibold',zorder=8)
    ymin=min([lowy]+[positions[n][1] for n in selected_ids]); ymax=max([highy]+[positions[n][1] for n in selected_ids])
    xmargin=(.85 if s.get('zoom_to_selected',False) else .19)*spread
    ymargin=(.22 if s.get('zoom_to_selected',False) else .15)*spread
    ax.set_xlim(lowx-xmargin,highx+xmargin); ax.set_ylim(ymin-ymargin,ymax+ymargin)
    scale = s.get('scale_bar')
    if scale:
        length=float(scale['length'])
        if not math.isfinite(length) or length<=0:
            raise ValueError('scale_bar.length must be positive and finite')
        origin_x=lowx-xmargin*0.70
        origin_y=ymin-ymargin*0.65
        ax.plot((origin_x,origin_x+length),(origin_y,origin_y),
                color=color('ink'),lw=1.5,zorder=11)
        ax.text(origin_x+length/2,origin_y+0.015*spread,
                f"{length:g} {scale.get('units','branch-length units')}",
                fontsize=8,va='bottom',ha='center',color=color('ink'),zorder=11)
    ax.set_aspect('equal',adjustable='box');ax.axis('off')
    fig.text(.055,.965,s['title'],fontsize=19,ha='left',va='top',
             fontweight='semibold',color=color('ink'))
    if s.get('subtitle'):
        fig.text(.055,.929,s['subtitle'],ha='left',va='top',
                 fontsize=10,color=color('warm_grey'))
    handles=[Line2D([0],[0],color=color('stone'),lw=2,alpha=.65,label=f'Reference genomes (n={len(reference_ids):,})'),
             Line2D([0],[0],color=color('ink'),lw=2,label='Minimum connecting subtree'),
             Line2D([0],[0],color=color('sage'),marker='o',linestyle='None',markersize=7,
                    markeredgecolor=color('ink'),label=f'Selected genomes (n={len(selected_ids)})')]
    if context_ids:
        handles.append(Line2D([0],[0],marker='o',markerfacecolor='white',
                              markeredgecolor=color('burgundy'),linestyle='None',
                              label=f'Context references (n={len(context_ids)})'))
    fig.legend(handles=handles,ncol=4 if context_ids else 3,frameon=False,loc='lower center',bbox_to_anchor=(.5,.015),fontsize=9)
    caption_mode = {'tip_count': 'UNROOTED EQUAL-ARC',
                    'phylogenetic_spread': 'UNROOTED / PHYLOGENETIC-SPREAD ANGLES'}[
                        config['layout'].get('angle_mode', 'tip_count')]
    footer = ('GEOMETRIC CROP OF FULL TREE  ·  ' if s.get('zoom_to_selected',False) else '') + caption_mode + '  ·  ORIGINAL EDGE LENGTHS  ·  SINGLE SHARED LAYOUT'
    fig.text(.055,.045,footer, size=8,color=color('warm_grey'))
    fig.subplots_adjust(left=.025,right=.98,bottom=.11,top=.86)
    for ext in ['svg','pdf','png']:
        metadata = ({'Date': None, 'Creator': f'PhyloCloud v{__version__}'} if ext == 'svg' else
                    {'CreationDate': None, 'ModDate': None, 'Creator': f'PhyloCloud v{__version__}'}
                    if ext == 'pdf' else {'Software': f'PhyloCloud v{__version__}'})
        fig.savefig(path.with_suffix('.'+ext),dpi=exp['dpi'],facecolor='white',
                    bbox_inches='tight',pad_inches=.18,metadata=metadata)
    plt.close(fig)
    return {'tips':len(graph.tips),'selected':len(selected_ids),
            'tree_edges':len(layout.edges),'foreground_edges':len(fg),
            'output_stem':str(path),
            'layout_mode':config['layout'].get('angle_mode', 'tip_count'),
            'style_preset':s['preset'],
            'density_overlay':bool(s.get('density_overlay',False)),
            'geometric_zoom':bool(s.get('zoom_to_selected',False)),
            'reference_genomes':len(reference_ids),
            'context_references':len(context_ids)}
