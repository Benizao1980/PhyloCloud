"""Matplotlib backend: lightweight, editable paths and text in SVG/PDF."""
from __future__ import annotations
from collections import defaultdict
from pathlib import Path
import math
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D
import numpy as np
from .data import color
from . import __version__
from .geometry import Layout, TreeGraph, connecting_edges, edge_taxa
from .cloud_layers import add_native_cloud, label_cloud_groups, colour_for_group, reference_ids
from .cloud_layers import _blur_float_counts, _density_grid

DENSITY_VISIBLE_ALPHA = .001


def _density_display_info(images, raster):
    """Bound visible raster pixels for the overview camera, never move the tree."""
    if raster is None:
        return None
    info = dict(raster)
    visible = []
    outer_alpha = 0.
    for image in images:
        alpha = np.asarray(image.get_array())[:, :, 3]
        outer_alpha = max(outer_alpha, float(max(alpha[0].max(), alpha[-1].max(),
                                               alpha[:, 0].max(), alpha[:, -1].max())))
        rows, cols = np.nonzero(alpha >= DENSITY_VISIBLE_ALPHA)
        if not len(rows):
            continue
        xmin, xmax, ymin, ymax = image.get_extent()
        ny, nx = alpha.shape
        dx, dy = (xmax-xmin)/nx, (ymax-ymin)/ny
        visible.append((xmin+cols.min()*dx, xmin+(cols.max()+1)*dx,
                        ymin+rows.min()*dy, ymin+(rows.max()+1)*dy))
    info['visible_bounds'] = ([float(min(b[0] for b in visible)),
                               float(max(b[1] for b in visible)),
                               float(min(b[2] for b in visible)),
                               float(max(b[3] for b in visible))] if visible else None)
    info['visibility_alpha_threshold'] = DENSITY_VISIBLE_ALPHA
    info['outer_edge_max_alpha'] = outer_alpha
    return info


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
    # Keep the historical log-count compression, but convolve in float
    # precision. An 8-bit intermediate erased faint tails and made terraces.
    bandwidth = float(style['density_sigma_px'])
    raster = _density_grid((xmin,xmax,ymin,ymax), count.shape, bandwidth)
    padded = np.pad(np.log1p(count), raster['padding_px_per_side'])
    blurred = _blur_float_counts(padded, bandwidth)
    alpha = np.clip((blurred / max(1e-12, blurred.max()))**0.65 * float(style['density_opacity']),0,1)
    # Warm neutral haze rather than species-dependent invented polygons.
    rgb = np.array(to_rgba(color('stone'))[:3],dtype=float)
    image = np.empty((*raster['raster_shape'],4),dtype=float)
    image[:,:,:3] = rgb
    image[:,:,3] = alpha
    ax.imshow(image, extent=raster['raster_bounds'],origin='lower',
              interpolation='bilinear',zorder=0,rasterized=True)
    return {'resolution': size, 'bandwidth_px': float(style['density_sigma_px']),
            'opacity': float(style['density_opacity']), 'source': 'reference_tips',
            'sample_weight': 'one_per_reference', 'count_transform': 'log1p',
            'alpha_power': .65, 'bounds': raster['raster_bounds'], 'raster': raster}


def draw(graph: TreeGraph, layout: Layout, metadata: dict, selected_ids: list[str],
         config: dict, output_stem: str | Path, *, focus_ids: list[str] | None = None) -> dict:
    selected_edges = connecting_edges(graph, selected_ids)
    focus = list(selected_ids if focus_ids is None else focus_ids)
    if not focus or len(set(focus)) != len(focus) or not set(focus).issubset(selected_ids):
        raise ValueError('Focus identifiers must be a nonempty unique subset of selected tips')
    index = {node:i for i,node in enumerate(graph.adjacency)}
    coordinate_hash = hashlib.sha256(json.dumps(
        [[index[n],*layout.coordinates[n]] for n in graph.adjacency]).encode()).hexdigest()
    foreground_ids = sorted(sorted(index[n] for n in edge) for edge in selected_edges)
    taxonomy = {k:v.get('species', '') for k,v in metadata.items()}
    taxonomy_by_edge = edge_taxa(layout, graph, taxonomy)
    s = config['style']; exp = config['export']; species_colors=s['species_colors']
    composition = s.get('composition', 'legacy')
    if composition not in ('legacy', 'publication'):
        raise ValueError('style.composition must be legacy or publication')
    modern = composition == 'publication'
    annotation_layout = None
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
    legacy_density = None
    if native and motif != 'constellation':
        native_fields, group_counts = add_native_cloud(ax,graph,layout,metadata,
                                                       reference_names,config,s)
    elif native:
        from .cloud_layers import groups_for_references
        group_counts = {k:len(v) for k,v in groups_for_references(
            graph,metadata,reference_names,config['cloud'].get('group_by','species')).items()}
    elif s.get('density_overlay', False):
        legacy_density = add_reference_density_overlay(ax, graph, layout, reference_names, s)
    density_raster = _density_display_info(
        ax.images, native_fields[0]['raster'] if native_fields else
        (legacy_density['raster'] if legacy_density else None))
    paths=[]; branch_colours=[]
    for parent, child, length in layout.edges:
        paths.append([layout.coordinates[parent], layout.coordinates[child]])
        taxon = taxonomy_by_edge[frozenset((parent,child))]
        if s['species_background'] and taxon and (taxon in species_colors or native):
            branch_colours.append(colour_for_group(taxon, config['cloud'], species_colors) if native else color(species_colors[taxon]))
        else:
            branch_colours.append(color(s.get('reference_color','stone')))
    # Two thin, translucent vector stroke passes produce a soft background.
    halo = [to_rgba(c, float(s['halo_alpha'])) for c in branch_colours]
    core = [to_rgba(c, float(s['reference_alpha'])) for c in branch_colours]
    ax.add_collection(LineCollection(paths, colors=halo, linewidths=s['halo_width'], zorder=1,
                                     gid='reference-tree-halo'))
    ax.add_collection(LineCollection(paths, colors=core, linewidths=s['reference_width'], zorder=2,
                                     gid='reference-tree-edges'))
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
                                         capstyle='round',joinstyle='round',zorder=4,
                                         gid='selected-original-edges'))
    # Group captions use actual reference coordinates and avoid highlighted
    # original branches. A zoom suppresses labels outside the crop.
    if native_fields and not modern and not s.get('zoom_to_selected',False):
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
        if name in focus:
            plotted.append((name,x,y,face))
    # Layout size is data-driven; do not impose a common outer radius.
    xx=[p[0] for p in coords.values()]; yy=[p[1] for p in coords.values()]
    lowx,highx=min(xx),max(xx); lowy,highy=min(yy),max(yy)
    # Geometric crop: use *exactly the existing full-tree coordinates*, without
    # pruning/repositioning any node or converting branch lengths.
    if s.get('zoom_to_selected', False):
        xs=[coords[graph.tips[name]][0] for name in focus+context_ids]
        ys=[coords[graph.tips[name]][1] for name in focus+context_ids]
        lowx,highx=min(xs),max(xs); lowy,highy=min(ys),max(ys)
        span=max(highx-lowx,highy-lowy)
        if span <= 0:
            raise ValueError('Selected genomes have coincident plotted positions; cannot zoom')
        spread=span*2.2
    else:
        spread=max(highx-lowx,highy-lowy)
    if modern:
        from .composition import publication_composition
        annotation_layout = publication_composition(
            fig,ax,graph,layout,metadata,selected_ids,reference_names,context_ids,
            config,density_raster,(lowx,highx,lowy,highy),focus_ids=focus)
        view = annotation_layout['view_bounds']
        group_counts = annotation_layout['reference_group_counts']
    else:
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
            group=sorted([name for name in focus if positions[name][2]==side],
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
        ymin=min([lowy]+[positions[n][1] for n in focus]); ymax=max([highy]+[positions[n][1] for n in focus])
        xmargin=(.85 if s.get('zoom_to_selected',False) else .19)*spread
        ymargin=(.22 if s.get('zoom_to_selected',False) else .15)*spread
        view = [lowx-xmargin,highx+xmargin,ymin-ymargin,ymax+ymargin]
        # A full overview must include the visible haze as well as tree/label bounds.
        # Explicit selected-tip zooms remain intentional camera crops of this scene.
        if not s.get('zoom_to_selected', False) and density_raster and density_raster['visible_bounds']:
            wash = density_raster['visible_bounds']
            view = [min(view[0],wash[0]),max(view[1],wash[1]),
                    min(view[2],wash[2]),max(view[3],wash[3])]
        ax.set_xlim(*view[:2]); ax.set_ylim(*view[2:])
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
                    bbox_inches=None if modern else 'tight',
                    pad_inches=0 if modern else .18,metadata=metadata)
    plt.close(fig)
    return {'tips':len(graph.tips),'selected':len(selected_ids),
            'highlighted_tip_ids':list(selected_ids), 'labelled_tip_ids':focus,
            'crop_tip_ids':focus+context_ids if s.get('zoom_to_selected',False) else None,
            'coordinate_sha256':coordinate_hash,
            'foreground_original_edge_ids':foreground_ids,
            'edge_identity_scheme':'input_graph_node_insertion_indices',
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
                             else 'reference_tip_gaussian_visual') if native and native_fields else
                             ('reference_tip_log_count_float_gaussian_visual' if s.get('density_overlay',False) else None),
            'density_render_method': 'hybrid_vector_tree_raster_wash' if ax.images else 'vector_tree',
            'density_kernel': 'padded_float_fft_gaussian' if ax.images else None,
            'density_parameters':{k:config['cloud'][k] for k in (
                'opacity','bandwidth_px','resolution')} if native and native_fields else legacy_density,
            'density_raster': density_raster,
            'view_bounds': view,
            'annotation_layout': annotation_layout,
            'density_camera_policy': 'explicit_selected_crop' if s.get('zoom_to_selected',False)
                                     else 'include_visible_density',
            'reference_genomes':len(reference_names),
            'context_references':len(context_ids)}
