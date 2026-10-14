"""Matplotlib backend: lightweight, editable paths and text in SVG/PDF."""
from __future__ import annotations
from collections import defaultdict
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
from .cloud_layers import add_native_cloud, label_cloud_groups, colour_for_group, reference_ids


def add_reference_density_overlay(ax, graph, layout, reference_ids, style):
    """Render a display-only soft density field from *actual* reference tips.

    This map is an optional raster underlay, **never** an inferred branch or a
    population-frequency estimate. The overlaid tree edges and text stay vector
    in exported SVG/PDF. Sampling counts are not normalised by species.
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
    # Each observed reference genome contributes exactly one point. This can
    # look very concentrated if the Newick contains many zero-length branches,
    # which is correct and should be disclosed rather than jittered away.
    size = 460
    count, _, _ = np.histogram2d(ty, tx, bins=(size,size),
                                 range=((ymin,ymax),(xmin,xmax)))
    # Compressive intensity is visual-only. Use a deterministic Gaussian blur
    # from Pillow, without modifying original branch coordinates.
    raw = 255 * np.log1p(count) / max(1e-12, np.log1p(float(count.max())))
    luminance = Image.fromarray(np.asarray(raw,dtype=np.uint8),mode='L')
    blur = luminance.filter(ImageFilter.GaussianBlur(radius=float(style['density_sigma_px'])))
    blurred = np.asarray(blur,dtype=float) / 255
    alpha = np.clip((blurred / max(1e-12, blurred.max()))**0.65 * float(style['density_opacity']),0,1)
    # Warm neutral haze rather than species-dependent invented polygons.
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
    motif = s['preset']
    length_mode = getattr(layout,'length_mode','original')
    if length_mode == 'graphic' and s.get('scale_bar'):
        raise ValueError('Scale bars are invalid for non-metric graphic mode')
    native = motif in ('cloud', 'canopy', 'constellation', 'river')
    dark = motif == 'constellation'
    background = s.get('background', '#FFFFFF')
    ink = '#F3F2EC' if dark else color('ink')
    path = Path(output_stem)
    path.parent.mkdir(parents=True,exist_ok=True)
    fig, ax = plt.subplots(figsize=(exp['width_inches'], exp['height_inches']))
    fig.patch.set_facecolor(background); ax.set_facecolor(background)
    plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none',
                         'svg.hashsalt':'phylocloud-v0.1', 'pdf.fonttype':42})
    # Reference classification must not silently count unselected MAGs as GTDB.
    reference_names = reference_ids(graph, metadata, selected_ids)
    native_fields, group_counts, cloud_labels = [], {}, []
    if native and motif != 'constellation':
        native_fields, group_counts = add_native_cloud(ax,graph,layout,metadata,
                                                       reference_names,config,s)
    elif native:
        from .cloud_layers import groups_for_references
        group_counts = {k:len(v) for k,v in groups_for_references(
            graph,metadata,reference_names,config['cloud'].get('group_by','species')).items()}
    elif s.get('density_overlay', False):
        add_reference_density_overlay(ax, graph, layout, reference_names, s)
    paths=[]; branch_colours=[]
    for parent, child, length in layout.edges:
        paths.append([layout.coordinates[parent], layout.coordinates[child]])
        taxon = taxonomy_by_edge[frozenset((parent,child))]
        if s['species_background'] and taxon and (taxon in species_colors or native):
            branch_colours.append(colour_for_group(taxon, config['cloud'], species_colors) if native else color(species_colors[taxon]))
        else:
            branch_colours.append(color('stone'))
    # Two thin, translucent vector stroke passes produce a soft background.
    halo = [to_rgba(c, float(s['halo_alpha'])) for c in branch_colours]
    core = [to_rgba(c, float(s['reference_alpha'])) for c in branch_colours]
    ax.add_collection(LineCollection(paths, colors=halo, linewidths=s['halo_width'], zorder=1))
    ax.add_collection(LineCollection(paths, colors=core, linewidths=s['reference_width'], zorder=2))
    if motif == 'river':
        ax.add_collection(LineCollection(paths,colors=[to_rgba(c,.055) for c in branch_colours],
                                         linewidths=4.2,zorder=1.5,capstyle='round'))
    if native:
        # Tip points follow observed original genomic coordinates. No jitter and
        # no invented branches/tips; Canopy uses them as fine foliage texture.
        ref_coords = np.array([layout.coordinates[graph.tips[name]] for name in reference_names])
        ref_colours = [colour_for_group(metadata[name].get(config['cloud']['group_by'],'') or 'Unassigned',
                                        config['cloud'],species_colors) for name in reference_names]
        if len(ref_coords):
            if motif == 'constellation':
                ax.scatter(ref_coords[:,0],ref_coords[:,1],s=18,c=ref_colours,
                           alpha=.13,zorder=3,rasterized=True,linewidths=0)
                ax.scatter(ref_coords[:,0],ref_coords[:,1],s=3.5,c=ref_colours,
                           alpha=.88,zorder=3.2,rasterized=True,linewidths=0)
            else:
                ax.scatter(ref_coords[:,0],ref_coords[:,1],s=3.8 if motif=='canopy' else 2.2,
                           c=ref_colours,alpha=.45 if motif=='canopy' else .40,
                           zorder=3,rasterized=True,linewidths=0)

    fg = [[layout.coordinates[p],layout.coordinates[c]]
          for p,c,_ in layout.edges if frozenset((p,c)) in selected_edges]
    if fg:
        ax.add_collection(LineCollection(fg, colors=color(s['foreground_color']),
                                         linewidths=s['foreground_width'],alpha=.9,
                                         capstyle='round',joinstyle='round',zorder=4))
    # Group captions use actual reference coordinates and avoid highlighted
    # original branches. A zoom suppresses labels outside the crop.
    if native_fields and not s.get('zoom_to_selected',False):
        cloud_labels = label_cloud_groups(ax,native_fields,config,s,
            [layout.coordinates[graph.tips[n]] for n in selected_ids],
            blocked_segments=fg)

    # Dot overprinted at each highlighted terminal; directly labelled.
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
        face=(colour_for_group(species or 'Unassigned',config['cloud'],species_colors)
              if native else color(species_colors.get(species,'warm_grey')))
        ax.scatter([x],[y],s=s['mag_size'],c=[face],edgecolors=ink,
                   linewidths=.8,zorder=6)
        plotted.append((name,x,y,face))
    # Layout size is data-driven; do not impose a common outer radius.
    xx=[p[0] for p in coords.values()]; yy=[p[1] for p in coords.values()]
    lowx,highx=min(xx),max(xx); lowy,highy=min(yy),max(yy)
    # Geometric crop: use *exactly the existing full-tree coordinates*, without
    # pruning/repositioning any node or converting branch lengths.
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
    # Offset labels in their local tip direction; text stays horizontal.
    # Collision avoidance in data space is label-only, never moves tips/edges.
    center_x,center_y=coords[layout.centre]
    label_spacing=0.038*spread
    positions={}
    for name,x,y,face in plotted:
        vx,vy=x-center_x,y-center_y
        norm=math.hypot(vx,vy) or 1
        side=1 if vx>=0 else -1
        tx=x+side*0.032*spread
        ty=y+vy/norm*0.027*spread
        positions[name]=[tx,ty,side]
    # Simple deterministic relaxation within left and right margins.
    for side in [-1,1]:
        group=sorted([name for name in selected_ids if positions[name][2]==side],
                     key=lambda n:positions[n][1])
        if not group: continue
        # Only close labels are separated; leader lines retain original xy.
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
        elbow=tx-side*0.013*spread
        ax.plot([x,elbow,tx-side*0.006*spread],[y,ty,ty],color=face,
                alpha=.70,linewidth=.68,zorder=5,solid_capstyle='round')
        ax.text(tx,ty,label,fontsize=s['label_font_size'],color=ink,
                ha='left' if side==1 else 'right',va='center',weight='medium',
                zorder=8, bbox={'facecolor':background,'alpha':.56,
                               'edgecolor':'none','pad':.65})
    # Content bounds plus deliberately generous margins for direct labels.
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
                color=ink,lw=1.5,zorder=11)
        ax.text(origin_x+length/2,origin_y+0.015*spread,
                f"{length:g} {scale.get('units','branch-length units')}",
                fontsize=8,va='bottom',ha='center',color=ink,zorder=11)
    ax.set_aspect('equal',adjustable='box');ax.axis('off')
    fig.text(.055,.965,s['title'],fontsize=19,ha='left',va='top',
             fontweight='semibold',color=ink)
    if s.get('subtitle'):
        fig.text(.055,.929,s['subtitle'],ha='left',va='top',
                 fontsize=10,color='#B4C1C5' if dark else color('warm_grey'))
    handles=[Line2D([0],[0],color=color('stone'),lw=2,alpha=.65,label=f'Reference genomes (n={len(reference_names):,})'),
             Line2D([0],[0],color=ink,lw=2,label='Minimum connecting subtree'),
             Line2D([0],[0],color=color('sage'),marker='o',linestyle='None',markersize=7,
                    markeredgecolor=color('ink'),label=f'Selected genomes (n={len(selected_ids)})')]
    if context_ids:
        handles.append(Line2D([0],[0],marker='o',markerfacecolor='white',
                              markeredgecolor=color('burgundy'),linestyle='None',
                              label=f'Context references (n={len(context_ids)})'))
    leg=fig.legend(handles=handles,ncol=4 if context_ids else 3,frameon=False,loc='lower center',bbox_to_anchor=(.5,.015),fontsize=9)
    if dark:
        for text in leg.get_texts():text.set_color(ink)
    caption_mode = {'tip_count': 'UNROOTED EQUAL-ARC',
                    'phylogenetic_spread': 'UNROOTED / PHYLOGENETIC-SPREAD ANGLES'}[
                        config['layout'].get('angle_mode', 'tip_count')]
    footer = ('GEOMETRIC CROP OF FULL TREE  ·  ' if s.get('zoom_to_selected',False) else '') + caption_mode + ('  ·  ORIGINAL EVOLUTIONARY BRANCH LENGTHS' if length_mode == 'original' else '  ·  NON-METRIC GRAPHIC LENGTHS') + '  ·  SINGLE SHARED LAYOUT'
    fig.text(.055,.045,footer,
             size=8,color='#B4C1C5' if dark else color('warm_grey'))
    fig.subplots_adjust(left=.025,right=.98,bottom=.11,top=.86)
    for ext in ['svg','pdf','png']:
        metadata = ({'Date': None, 'Creator': f'PhyloCloud v{__version__}'} if ext == 'svg' else
                    {'CreationDate': None, 'ModDate': None, 'Creator': f'PhyloCloud v{__version__}'}
                    if ext == 'pdf' else {'Software': f'PhyloCloud v{__version__}'})
        fig.savefig(path.with_suffix('.'+ext),dpi=exp['dpi'],facecolor=background,
                    bbox_inches='tight',pad_inches=.18,metadata=metadata)
    plt.close(fig)
    return {'tips':len(graph.tips),'selected':len(selected_ids),
            'tree_edges':len(layout.edges),'foreground_edges':len(fg),
            'output_stem':str(path),
            'layout_mode':config['layout'].get('angle_mode', 'tip_count'),
             'length_mode':length_mode,
            'style_preset':s['preset'],
            'density_overlay':bool(s.get('density_overlay',False)),
            'geometric_zoom':bool(s.get('zoom_to_selected',False)),
            'cloud_group_by':config['cloud'].get('group_by','species') if native else None,
            'cloud_label_by':config['cloud'].get('label_by','same') if native else None,
            'reference_group_counts':group_counts,
            'native_cloud_labels':cloud_labels,
            'density_type':('reference_tip_and_pure_original_edge_multiscale_visual'
                             if motif in ('cloud','canopy') and config['cloud'].get('density_engine','multiscale')=='multiscale'
                             else 'reference_tip_gaussian_visual') if native and native_fields else None,
            'density_parameters':{k:config['cloud'][k] for k in (
                'opacity','bandwidth_px','resolution')} if native and native_fields else None,
            'reference_genomes':len(reference_names),
            'context_references':len(context_ids)}
