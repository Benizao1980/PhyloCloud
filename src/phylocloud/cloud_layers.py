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
    pad = int(math.ceil(3.5*sigma))
    padded = np.pad(count, ((pad,pad),(pad,pad)), mode='constant')
    ky = np.fft.fftfreq(padded.shape[0])[:,None]
    kx = np.fft.rfftfreq(padded.shape[1])[None,:]
    attenuation = np.exp(-2*np.pi**2*sigma**2*(kx**2 + ky**2))
    result = np.fft.irfft2(np.fft.rfft2(padded)*attenuation,s=padded.shape)
    return np.maximum(0,result[pad:-pad,pad:-pad])


def compute_cloud_fields(graph, layout, metadata, reference_names, cloud_config,
                         species_colors, bounds):
    """Return group-aware RGBA grids with exact tree-data coordinate bounds.

    Each real reference is counted once. Canopy also uses original-edge interior
    samples solely to create a soft *edge* density; those are NOT genome points.
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
    for group in sorted(groups, key=lambda k: (-len(groups[k]), k)):
        ids = groups[group]
        coords_for_group = np.asarray([coords[graph.tips[name]] for name in ids], dtype=float)
        hist, _, _ = np.histogram2d(coords_for_group[:,1], coords_for_group[:,0],
                                    bins=(ny,nx), range=((ymin,ymax),(xmin,xmax)))
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
        rgba = np.empty((ny,nx,4), dtype=np.float32)
        rgba[:,:,:3] = to_rgb(colour_for_group(group, cloud_config, species_colors))
        rgba[:,:,3] = alpha
        fields.append({'group':group,'count':len(ids),'rgba':rgba,
                       'points':coords_for_group,'bounds':bounds})
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
    fields,counts = compute_cloud_fields(graph,layout,metadata,reference_names,cloud_cfg,
                                         style['species_colors'],bounds)
    for field in fields:
        ax.imshow(field['rgba'],extent=bounds,origin='lower',interpolation='bilinear',
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
