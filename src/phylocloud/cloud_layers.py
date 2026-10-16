"""Native cloud / canopy effects derived only from the original phylogeny.

No point is jittered. All dense fields are purely visual overlays, NOT
confidence regions, population prevalence, or inferred new branches.
"""
from __future__ import annotations
from collections import Counter, defaultdict
import hashlib
import math
import numpy as np
from matplotlib.colors import to_rgb
from .data import color

FALLBACK_COLOURS = ('sage', 'powder_blue', 'dusty_pink', 'lavender', 'mustard',
                    'teal', 'apricot', 'seafoam', 'burgundy')

RASTER_SUPPORT_SIGMA = 6.0
MAX_RASTER_CELLS = 4_000_000
MAX_LAYER_CELLS = 32_000_000


def reference_ids(graph, metadata, selected):
    """Match existing renderer's explicit source classification."""
    def is_ref(name):
        source = metadata[name].get('source', '').strip().lower()
        return source == 'gtdb' or 'reference' in source
    if any(metadata[n].get('source') for n in graph.tips):
        return [n for n in graph.tips if is_ref(n)]
    return [n for n in graph.tips if n not in selected]


def groups_for_references(graph, metadata, reference_names, group_by):
    if not metadata:
        raise ValueError('Empty genome metadata')
    if not any(group_by in row for row in metadata.values()):
        raise ValueError(f'Cloud grouping column not found in metadata: {group_by}')
    groups = defaultdict(list)
    for name in reference_names:
        value = metadata[name].get(group_by, '').strip() or 'Unassigned'
        groups[value].append(name)
    return dict(groups)


def colour_for_group(group, cloud_config, species_colors):
    overrides = cloud_config.get('colours', {})
    if group in overrides:
        return color(overrides[group])
    if group in species_colors:
        return color(species_colors[group])
    if group in ('Unassigned', 'Other reference categories'):
        return color('stone')
    digest = hashlib.sha256(group.encode('utf8')).digest()
    return color(FALLBACK_COLOURS[int.from_bytes(digest[:2], 'big') % len(FALLBACK_COLOURS)])


def _blur_float_counts(count, radius):
    """Float-precision padded Gaussian convolution; no blocky uint8 artefacts."""
    if not count.size or count.max() <= 0:
        return np.zeros_like(count, dtype=float)
    sigma = float(radius)
    if not math.isfinite(sigma) or sigma <= 0:
        raise ValueError('Gaussian bandwidth must be positive and finite')
    pad = int(math.ceil(RASTER_SUPPORT_SIGMA*sigma))
    padded = np.pad(count, ((pad,pad),(pad,pad)), mode='constant')
    # Transform a positive sampled kernel, rather than truncating its analytic
    # frequency response. The latter produces ringing at subpixel bandwidths,
    # whose non-Gaussian tails defeat a finite-support raster padding policy.
    kernels = []
    for size in padded.shape:
        offsets = np.arange(size)
        distances = np.minimum(offsets, size-offsets)
        kernel = np.exp(-.5*(distances/sigma)**2)
        kernel[distances > pad] = 0.
        kernels.append(kernel/kernel.sum())
    attenuation = np.fft.fft(kernels[0])[:,None] * np.fft.rfft(kernels[1])[None,:]
    result = np.fft.irfft2(np.fft.rfft2(padded)*attenuation,s=padded.shape)
    return np.maximum(0,result[pad:-pad,pad:-pad])


def _soft_tail(values, threshold):
    """Suppress numerical haze continuously, without a hard contour boundary."""
    t = np.clip(values / threshold, 0., 1.)
    return values * t * t * (3. - 2. * t)


def _density_grid(bounds, shape, maximum_sigma, layers=1):
    """Extend the visual raster, preserving the ORIGINAL histogram cell scale.

    Histogram first, then pad with empty cells: enlarging the histogram's range
    would rebin references and change the bandwidth in tree-coordinate units.
    Six widest-kernel sigmas make outer-edge alpha negligible after our tone
    curves. These are raster bounds, never new tree coordinates or clade bounds.
    """
    xmin, xmax, ymin, ymax = map(float, bounds)
    ny, nx = shape
    dx, dy = (xmax-xmin)/nx, (ymax-ymin)/ny
    sigma = float(maximum_sigma)
    if not all(math.isfinite(v) for v in (*bounds, dx, dy)) or min(dx, dy) <= 0:
        raise ValueError('Cloud extent must be finite and positive')
    if not math.isfinite(sigma) or sigma <= 0:
        raise ValueError('Gaussian bandwidth must be positive and finite')
    if RASTER_SUPPORT_SIGMA*sigma > math.sqrt(MAX_RASTER_CELLS):
        raise ValueError('Padded cloud raster too large; reduce bandwidth or resolution')
    pad = int(math.ceil(RASTER_SUPPORT_SIGMA*sigma))
    padded_shape = (ny+2*pad, nx+2*pad)
    cells = math.prod(padded_shape)
    if cells > MAX_RASTER_CELLS or cells*max(1, layers) > MAX_LAYER_CELLS:
        raise ValueError('Padded cloud raster too large; reduce bandwidth, resolution '
                         'or max_density_groups')
    return {'histogram_bounds': list(bounds), 'histogram_shape': [ny, nx],
            'raster_bounds': [xmin-pad*dx, xmax+pad*dx, ymin-pad*dy, ymax+pad*dy],
            'raster_shape': list(padded_shape), 'cell_size_xy': [dx, dy],
            'padding_px_per_side': pad, 'support_sigma': RASTER_SUPPORT_SIGMA,
            'kernel_discretization': 'normalized_sampled_gaussian',
            'maximum_sigma_px': sigma, 'maximum_sigma_xy': [sigma*dx, sigma*dy],
            'sampling': 'original_histogram_then_zero_pad',
            'max_raster_cells': MAX_RASTER_CELLS, 'max_layer_cells': MAX_LAYER_CELLS}


def compute_cloud_fields(graph, layout, metadata, reference_names, cloud_config,
                         species_colors, bounds):
    """Return tip-only RGBA grids with expanded, fixed-cell-scale raster bounds.

    Each real reference is counted once. The field's ``bounds`` retain the
    original label-placement domain; ``raster`` describes the visual wash extent.
    """
    group_by = cloud_config.get('group_by', 'species')
    groups = groups_for_references(graph, metadata, reference_names, group_by)
    xmin, xmax, ymin, ymax = bounds
    resolution = int(cloud_config.get('resolution', 500))
    if not 128 <= resolution <= 900:
        raise ValueError('cloud.resolution must be in 128..900')
    if xmax <= xmin or ymax <= ymin:
        raise ValueError('Cloud extent is empty')
    alpha_max = float(cloud_config.get('opacity', .48))
    bandwidth = float(cloud_config.get('bandwidth_px', 15))
    if not (0 <= alpha_max <= 1 and 0.1 <= bandwidth <= 100):
        raise ValueError('Cloud opacity/bandwidth out of range')
    ratio = (ymax-ymin)/(xmax-xmin)
    nx, ny = resolution, max(128, min(900, int(resolution * ratio)))
    coords = layout.coordinates
    fields = []
    tip_counts = Counter({k: len(v) for k, v in groups.items()})
    # Preserve all references while bounding the number of expensive texture
    # layers. Rare metadata groups share one neutral wash; their true tip
    # coordinates and exact full-tree edges still render individually.
    max_groups = int(cloud_config.get('max_density_groups', 12))
    if not 2 <= max_groups <= 40:
        raise ValueError('cloud.max_density_groups must be 2..40')
    ordered = sorted(groups, key=lambda k: (-len(groups[k]), k))
    if len(ordered) > max_groups:
        keep = ordered[:max_groups-1]
        remaining = [name for g in ordered[max_groups-1:] for name in groups[g]]
        groups = {g:groups[g] for g in keep}
        groups['Other reference categories'] = remaining
    raster = _density_grid(bounds, (ny, nx), bandwidth*2.2, len(groups))
    for group in sorted(groups, key=lambda k: (-len(groups[k]), k)):
        ids = groups[group]
        coords_for_group = np.asarray([coords[graph.tips[name]] for name in ids], dtype=float)
        hist, _, _ = np.histogram2d(coords_for_group[:,1], coords_for_group[:,0],
                                    bins=(ny,nx), range=((ymin,ymax),(xmin,xmax)))
        hist = np.pad(hist, raster['padding_px_per_side'])
        tight = _blur_float_counts(hist, bandwidth)
        broad = _blur_float_counts(hist, bandwidth*2.2)
        if tight.max() == 0:
            continue
        dense = .67*tight/max(float(tight.max()),1e-9) + .33*broad/max(float(broad.max()),1e-9)
        # Sparse taxa must not appear as equally rich clouds. One tip yields a
        # point-sized subdued halo, not a fabricated populous species clade.
        sample_factor = min(1.0, math.log1p(len(ids))/math.log1p(100))
        if len(ids) < 3:
            sample_factor *= .20
        alpha = np.clip((dense ** .83) * alpha_max * sample_factor, 0, .76)
        if cloud_config.get('motif') == 'canopy':
            alpha *= .82
        rgba = np.empty((*raster['raster_shape'],4), dtype=np.float32)
        rgba[:,:,:3] = to_rgb(colour_for_group(group, cloud_config, species_colors))
        rgba[:,:,3] = alpha
        fields.append({'group':group,'count':len(ids),'rgba':rgba,
                       'points':coords_for_group,'bounds':bounds,'raster':raster})
    return fields, dict(tip_counts)


def add_native_cloud(ax, graph, layout, metadata, reference_names, cfg, style):
    xy = np.asarray(list(layout.coordinates.values()), dtype=float)
    xmin, ymin = np.min(xy,axis=0)
    xmax, ymax = np.max(xy,axis=0)
    span = max(xmax-xmin, ymax-ymin)
    padding = max(1e-9,span*.03)
    bounds = (xmin-padding, xmax+padding, ymin-padding, ymax+padding)
    cloud_cfg = dict(cfg['cloud'])
    cloud_cfg['motif'] = style['preset']
    if style['preset'] in ('cloud','canopy') and cloud_cfg.get('density_engine','multiscale')=='multiscale':
        return _multiscale_reference_atmosphere(ax,graph,layout,metadata,
                 reference_names,cloud_cfg,style['species_colors'],bounds,style['preset'])
    fields,counts = compute_cloud_fields(graph,layout,metadata,reference_names,cloud_cfg,
                                         style['species_colors'],bounds)
    for field in fields:
        ax.imshow(field['rgba'],extent=field['raster']['raster_bounds'],
                  origin='lower',interpolation='bilinear',
                  zorder=0,rasterized=True)
    return fields, counts


def _point_to_segment_distance(point, segment):
    """Euclidean screen-plane distance to an ORIGINAL plotted edge."""
    p = np.asarray(point, dtype=float)
    a, b = (np.asarray(q, dtype=float) for q in segment)
    d = b-a
    length = float(d@d)
    t = np.clip(float((p-a)@d)/length,0.,1.) if length else 0.
    return float(np.linalg.norm(p-a-t*d))


def label_cloud_groups(ax, fields, cfg, style, excluded_xy=(), blocked_segments=()):
    """Place broad labels near real observed members, away from focal branches.

    All candidates are observed reference positions, their medians, or quantiles;
    no phylogenetic vertex/edge is moved. A skipped label retains its category
    in the legend and provenance report.
    """
    label_by = cfg['cloud'].get('label_by','same')
    if label_by == 'none':
        return []
    if label_by != 'same':
        raise ValueError('cloud.label_by currently supports same or none')
    min_refs = int(cfg['cloud'].get('min_label_references', 15))
    max_labels = int(cfg['cloud'].get('max_labels',7))
    anchors=[]
    occupied=[]
    for field in fields:
        if field['group'] == 'Other reference categories' or field['count'] < min_refs or len(anchors) >= max_labels:
            continue
        points=field['points']
        width=field['bounds'][1]-field['bounds'][0]
        height=field['bounds'][3]-field['bounds'][2]
        candidates=[np.median(points,axis=0)]
        candidates.extend([np.quantile(points,q,axis=0) for q in (.20,.35,.65,.80)])
        candidates.extend(points[::max(1,len(points)//20)][:20])
        centroid=np.median(points,axis=0)
        candidates=sorted(candidates,key=lambda p:float(np.linalg.norm(p-centroid)))
        chosen=None
        for anchor in candidates:
            if any(abs(anchor[0]-x) < width*.105 and abs(anchor[1]-y) < height*.043 for x,y in occupied):
                continue
            if any(math.dist(anchor,p) < width*.038 for p in excluded_xy):
                continue
            if any(_point_to_segment_distance(anchor,edge)<min(width,height)*.023 for edge in blocked_segments):
                continue
            chosen=anchor
            break
        if chosen is None:
            continue
        label=field['group'].replace('Campylobacter_D ', 'C_D. ').replace('Campylobacter ', 'C. ')
        x,y = float(chosen[0]),float(chosen[1])
        ax.text(x,y,label,ha='center',va='center',
                fontsize=style.get('cloud_label_font_size',9.4),
                color=style.get('cloud_label_color','#343C38'),
                fontstyle='italic' if cfg['cloud'].get('group_by')=='species' else 'normal',
                weight='medium',alpha=.94,zorder=3.7,
                bbox={'facecolor':style.get('background','#FFFFFF'),
                      'alpha':.83,'edgecolor':'none','boxstyle':'round,pad=0.42'})
        anchors.append({'group':field['group'],'count':field['count'],
                        'x':x,'y':y,'placement':'reference_position_or_quantile'})
        occupied.append((x,y))
    return anchors


def _multiscale_reference_atmosphere(
        ax, graph, layout, metadata, reference_names, cloud_cfg,
        species_colors, bounds, motif):
    """Multiscale, shared-normalization soft colour washes from ORIGINAL geometry.

    All tree edges are still rendered separately as vector lines by render.py.
    This function only creates an additional visual underlay: one sampled point
    per reference tip, plus downweighted points ON eligible reference-bearing,
    metadata-homogeneous original edge segments. Interior samples are not tips.
    Density is not ecological prevalence, ancestry probability or uncertainty.
    """
    from .geometry import edge_taxa
    group_by = cloud_cfg.get('group_by', 'species')
    true_groups = groups_for_references(graph, metadata, reference_names, group_by)
    counts = {k: len(v) for k,v in true_groups.items()}
    max_groups = int(cloud_cfg.get('max_density_groups',12))
    if not 2 <= max_groups <= 40:
        raise ValueError('cloud.max_density_groups must be 2..40')
    ordered = sorted(true_groups, key=lambda x:(-len(true_groups[x]),x))
    if len(ordered)>max_groups:
        keep=set(ordered[:max_groups-1])
        groups={g:true_groups[g] for g in ordered if g in keep}
        groups['Other reference categories']=[
            name for category in ordered if category not in keep
            for name in true_groups[category]]
    else:
        groups={g:true_groups[g] for g in ordered}
    xmin,xmax,ymin,ymax=bounds
    res=int(cloud_cfg.get('resolution',600))
    if not 128<=res<=900: raise ValueError('cloud.resolution must be in 128..900')
    nx=res
    ny=max(128,min(900,int(res*(ymax-ymin)/(xmax-xmin))))
    bw=float(cloud_cfg.get('bandwidth_px',13))
    opacity=float(cloud_cfg.get('opacity',.72))
    if not .1<=bw<=100 or not 0<=opacity<=1:
        raise ValueError('cloud bandwidth or opacity out of range')
    raster = _density_grid(bounds, (ny,nx), max(.5,bw*.65,bw*2.2), len(groups))
    # Determine species/group purity on the exact ORIGINAL tree. An edge only
    # supplies cloud texture if its descendant side includes a reference tip.
    # The edges keep their original coordinates and branch lengths.
    by_tip={node:name for name,node in graph.tips.items()}
    children=defaultdict(list)
    for parent,child,length in layout.edges:
        children[parent].append(child)
    node_group={}
    ref_tips=set(reference_names)
    reference_descendants={}
    for node in reversed(list(layout.coordinates)):
        if node in by_tip:
            name=by_tip[node]
            node_group[node]=metadata[name].get(group_by,'').strip() or 'Unassigned'
            reference_descendants[node]=int(name in ref_tips)
        else:
            labels={node_group[c] for c in children[node]}
            node_group[node]=next(iter(labels)) if len(labels)==1 else None
            reference_descendants[node]=sum(reference_descendants[c] for c in children[node])
    segments=defaultdict(list)
    for parent,child,length in layout.edges:
        group=node_group[child]
        if group not in groups or reference_descendants[child]==0 or length<=0:
            continue
        a=np.asarray(layout.coordinates[parent],float)
        b=np.asarray(layout.coordinates[child],float)
        for t in (.25,.5,.75):
            segments[group].append(a+(b-a)*t)
    densities=[]
    fields=[]
    for group, ids in groups.items():
        tips=np.asarray([layout.coordinates[graph.tips[name]] for name in ids],dtype=float)
        hist,_,_=np.histogram2d(tips[:,1],tips[:,0],bins=(ny,nx),
                                range=((ymin,ymax),(xmin,xmax)))
        if segments[group]:
            pts=np.asarray(segments[group],dtype=float)
            edge_hist,_,_=np.histogram2d(pts[:,1],pts[:,0],bins=(ny,nx),
                                         range=((ymin,ymax),(xmin,xmax)))
            hist+=edge_hist*.10  # 3 samples, total density 0.30 / original edge
        hist=np.pad(hist,raster['padding_px_per_side'])
        fine=_blur_float_counts(hist,max(.5,bw*.65))
        broad=_blur_float_counts(hist,bw*2.2)
        density=(.74*fine + .26*broad).astype(np.float32)
        weight=min(1.0,math.log1p(len(ids))/math.log1p(180))
        if len(ids)<3:weight*=.18
        density*=weight
        peak=float(density.max())
        if peak:
            density = _soft_tail(density, peak*.0025)
        densities.append((group,density,tips))
        fields.append({'group':group,'count':len(ids),'points':tips,'bounds':bounds,
                       'raster':raster})
    global_peak=max((float(a.max()) for _,a,_ in densities),default=0.)
    scale=max(global_peak*.055,1e-9)
    rgb_total=np.zeros((*raster['raster_shape'],3),dtype=np.float32)
    weight_total=np.zeros(raster['raster_shape'],dtype=np.float32)
    for group,density,tip_xy in densities:
        strength=(1-np.exp(-1.25*np.sqrt(np.maximum(0,density/scale)))).astype(np.float32)
        if len(tip_xy)<3: strength*=.24
        if motif=='canopy':strength*=.72
        rgb=to_rgb(colour_for_group(group,cloud_cfg,species_colors))
        # Warm, luminous wash; not hard species-specific boundary polygons.
        soft_rgb=np.asarray(rgb,dtype=np.float32)*.82+.18
        rgb_total+=strength[:,:,None]*soft_rgb
        weight_total+=strength
    image=np.empty((*raster['raster_shape'],4),dtype=np.float32)
    image[:,:,:3]=rgb_total/np.maximum(weight_total[:,:,None],1e-8)
    image[:,:,3]=np.minimum(opacity*.84,
                            opacity*(1-np.exp(-weight_total*1.14)))
    image[:,:,3] *= _soft_tail(weight_total, .045) / np.maximum(weight_total, 1e-8)
    ax.imshow(image,extent=raster['raster_bounds'],origin='lower',interpolation='bilinear',
              zorder=0,rasterized=True)
    return fields,counts
