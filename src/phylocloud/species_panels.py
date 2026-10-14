"""Deterministic overview and taxonomic neighbourhood panels from one tree layout.

A panel is a camera crop, not a pruned tree or separately laid-out phylogeny.
Cloud fields represent reference sampling density, NOT natural abundance.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from pathlib import Path
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgb
import numpy as np

from .geometry import connecting_edges
from .data import color


def plan_species_panels(graph, layout, metadata, selected_ids, group_by="species",
                        max_panels=3, min_references=12):
    """Prioritise abundant references and at least one focal-rich group."""
    if not 1 <= max_panels <= 6:
        raise ValueError("max_panels must be in 1..6")
    if not any(group_by in row for row in metadata.values()):
        raise ValueError(f"Missing metadata grouping column: {group_by}")
    missing = set(graph.tips) - set(metadata)
    if missing:
        raise ValueError(f"Missing metadata for {len(missing)} tree tips")
    if not set(selected_ids) <= set(graph.tips):
        raise ValueError("Unknown selected genome ID")
    source_present = any(row.get("source", "").strip() for row in metadata.values())
    selected = set(selected_ids)
    refs, focal = defaultdict(list), defaultdict(list)
    for name in graph.tips:
        group = metadata[name].get(group_by, "").strip() or "Unassigned"
        source = metadata[name].get("source", "").strip().lower()
        is_reference = ((source == "gtdb" or "reference" in source)
                        if source_present else name not in selected)
        if is_reference:
            refs[group].append(name)
        if name in selected:
            focal[group].append(name)
    ranked = sorted((g for g in refs if len(refs[g]) >= min_references),
                    key=lambda g: (-len(refs[g]), g))
    chosen = ranked[:max_panels]
    focal_rich = sorted((g for g in focal if len(focal[g]) >= 2),
                        key=lambda g: (-len(focal[g]), -len(refs[g]), g))
    if focal_rich and focal_rich[0] not in chosen:
        if len(chosen) == max_panels:
            chosen[-1] = focal_rich[0]
        else:
            chosen.append(focal_rich[0])
    for group in sorted(focal, key=lambda g: (-len(focal[g]), -len(refs[g]), g)):
        if len(chosen) >= max_panels:
            break
        if group not in chosen:
            chosen.append(group)
    coords = np.asarray(list(layout.coordinates.values()), float)
    full_extent = float(max(np.ptp(coords, axis=0)))
    windows = []
    for group in chosen:
        member_names = refs[group] + focal[group]
        xy = np.asarray([layout.coordinates[graph.tips[name]]
                         for name in member_names], float)
        low, high = xy.min(axis=0), xy.max(axis=0)
        widths = np.maximum(high - low, max(full_extent * 1e-6, 1e-12))
        center = (low + high) * .5
        extents = widths * .68  # 18% margin on each side
        bounds = (float(center[0]-extents[0]), float(center[0]+extents[0]),
                  float(center[1]-extents[1]), float(center[1]+extents[1]))
        windows.append({"group": group, "reference_ids": tuple(refs[group]),
                        "selected_ids": tuple(focal[group]), "bounds": bounds})
    return windows


def _gaussian_reference_wash(ax, xy, bounds, rgb, *, alpha=.65, bandwidth=12):
    """Float Gaussian of actual reference-tip positions, with zero-padding."""
    if len(xy) < 2:
        return
    xmin, xmax, ymin, ymax = bounds
    points = np.asarray(xy, float)
    bins = 300
    hist, _, _ = np.histogram2d(points[:,1], points[:,0],
        bins=(bins, bins), range=((ymin, ymax), (xmin, xmax)))
    if hist.max() == 0:
        return
    sigma = float(bandwidth)
    pad = int(math.ceil(3*sigma))
    padded = np.pad(hist, pad_width=pad)
    frequencies_y = np.fft.fftfreq(padded.shape[0])[:,None]
    frequencies_x = np.fft.rfftfreq(padded.shape[1])[None,:]
    gauss = np.exp(-2*np.pi**2*sigma**2*(frequencies_x**2+frequencies_y**2))
    result = np.fft.irfft2(np.fft.rfft2(padded)*gauss, s=padded.shape)
    smoothed = np.maximum(0, result[pad:-pad,pad:-pad])
    if smoothed.max() == 0:
        return
    strength = np.sqrt(smoothed/smoothed.max())
    support = min(1.,math.log1p(len(points))/math.log1p(110))
    rgba = np.empty((bins,bins,4),dtype=np.float32)
    rgba[...,:3] = np.asarray(to_rgb(rgb),dtype=np.float32)
    rgba[...,3] = np.minimum(.8,strength*alpha*support)
    ax.imshow(rgba,extent=bounds,origin="lower",interpolation="bilinear",zorder=0)


def draw_species_panels(graph, layout, metadata, selected_ids, out,
                        group_by="species", max_panels=3, style="cloud", cloud_cfg=None, species_colors=None,
                        dpi=160, title="Phylogenetic diversity in context"):
    """Write a single PNG overview plus data-faithful group-specific crops.

    The original per-figure SVG/PDF remain the editable scientific exports.
    """
    from .cloud_layers import colour_for_group
    from .data import DEFAULT_CONFIG
    windows = plan_species_panels(graph, layout, metadata, selected_ids,
                                 group_by=group_by, max_panels=max_panels)
    if not windows:
        raise ValueError("No eligible metadata groups")
    selected_edges = connecting_edges(graph, selected_ids)
    coords = layout.coordinates
    edges = [[coords[a],coords[b]] for a,b,_ in layout.edges]
    foreground = [[coords[a],coords[b]] for a,b,_ in layout.edges
                  if frozenset((a,b)) in selected_edges]
    groups = defaultdict(list)
    selected = set(selected_ids)
    source_present = any(m.get("source","").strip() for m in metadata.values())
    for name in graph.tips:
        source = metadata[name].get("source","").strip().lower()
        ref = (source == "gtdb" or "reference" in source) if source_present else name not in selected
        if ref:
            groups[metadata[name].get(group_by,"").strip() or "Unassigned"].append(name)
    species_colors = (species_colors if species_colors is not None
                      else DEFAULT_CONFIG['style']['species_colors'])
    cloud_cfg = cloud_cfg if cloud_cfg is not None else DEFAULT_CONFIG['cloud']
    palette = lambda group: colour_for_group(group,cloud_cfg,species_colors)
    dark = style == "constellation"
    background = "#17202A" if dark else "#FFFFFF"
    ink = "#F1F0ED" if dark else "#2F2A26"
    muted = "#B7C4C8" if dark else "#676862"
    fine = "#92A6B5" if dark else "#A8A198"
    fig = plt.figure(figsize=(17,10.6),facecolor=background)
    fig.text(.05,.96,title,fontsize=22,color=ink,va="top",weight="medium")
    length_mode = getattr(layout, 'length_mode', 'original')
    display_note = ('ORIGINAL EVOLUTIONARY EDGE LENGTHS' if length_mode == 'original'
                    else 'NON-METRIC GRAPHIC DISPLAY LENGTHS')
    fig.text(.05,.918,
             f"{len(graph.tips):,} genomes · {len(groups):,} metadata categories · "
             f"{display_note} · shared layout with independently scaled crops",
             fontsize=10.0,color=muted)
    fig.text(.05,.87,"01   COMPLETE REFERENCE CONTEXT",
             fontsize=10,color=muted,weight="bold")
    xy = np.asarray(list(coords.values()),float)
    low,high=xy.min(axis=0),xy.max(axis=0)
    span=np.maximum(high-low,1e-12)
    overview=(float(low[0]-.05*span[0]),float(high[0]+.05*span[0]),
              float(low[1]-.05*span[1]),float(high[1]+.05*span[1]))
    ax=fig.add_axes([.04,.165,.565,.665],facecolor=background)
    def draw_edges(axes,bounds,group=None):
        axes.add_collection(LineCollection(edges,colors=fine,alpha=.12 if group is None else .25,
                                           linewidths=.35 if group is None else .45,zorder=1))
        if group is None:
            for taxon in sorted(groups,key=lambda k:(-len(groups[k]),k))[:7]:
                ids=groups[taxon]
                if len(ids)<12:
                    continue
                xy_tips=[coords[graph.tips[n]] for n in ids]
                _gaussian_reference_wash(axes,xy_tips,bounds,palette(taxon),
                                         alpha=.28,bandwidth=6)
        else:
            ids=groups[group]
            xy_tips=[coords[graph.tips[n]] for n in ids]
            _gaussian_reference_wash(axes,xy_tips,bounds,palette(group),
                                     alpha=.74,bandwidth=14)
        axes.add_collection(LineCollection(foreground,colors=ink,alpha=.93,
                                           linewidths=1.4,zorder=4,capstyle="round"))
        if group is None:
            markers=selected_ids
        else:
            markers=next(w["selected_ids"] for w in windows if w["group"]==group)
        for name in markers:
            x,y=coords[graph.tips[name]]
            taxon=metadata[name].get(group_by,"Unassigned")
            axes.scatter([x],[y],s=31,c=[palette(taxon)],
                         edgecolors=ink,linewidths=.85,zorder=6)
        if group is not None:
            # Reserve a right-hand label gutter; never relocate the actual tips.
            # Sort labels by their ORIGINAL vertical positions so leader lines
            # remain ordered rather than crossing arbitrarily.
            names = sorted(markers, key=lambda n: (
                -coords[graph.tips[n]][1], coords[graph.tips[n]][0], n))
            for idx, name in enumerate(names):
                p = coords[graph.tips[name]]
                label = metadata[name].get("label", "").strip() or name
                if len(label) > 26:
                    label = label.replace("GETCAMPY_", "").split("_Campylobacter")[0]
                if len(label) > 28:
                    label = label[:25] + "…"
                row_y = .84 - idx * (.68 / max(1, len(names)-1))
                axes.annotate(label, xy=p, xycoords="data",
                    xytext=(.985, row_y), textcoords="axes fraction",
                    ha="right", va="center",
                    fontsize=6.8 if len(names) > 5 else 7.4, color=ink,
                    arrowprops={"arrowstyle":"-", "lw":.6,
                                "color":palette(group), "alpha":.78},
                    bbox={"facecolor":background, "edgecolor":"none",
                          "alpha":.88, "pad":.9},
                    zorder=8, annotation_clip=False)
            xspan = bounds[1] - bounds[0]
            axes.set_xlim(bounds[0], bounds[1] + .31*xspan)
        else:
            axes.set_xlim(bounds[0], bounds[1])
        axes.set_ylim(bounds[2],bounds[3])
        axes.set_aspect("equal",adjustable="box");axes.axis("off")
    draw_edges(ax,overview)
    side_x=.65;panel_top=.835;gap=.022
    height=(.68-gap*(len(windows)-1))/len(windows)
    for i,window in enumerate(windows):
        top=panel_top-i*(height+gap)
        group=window["group"]
        fig.text(side_x,top+.008,f"{i+2:02d}   {group}",fontsize=9.3,
                 color=ink,weight="medium",va="bottom")
        fig.text(side_x,top-.013,
                 f'{len(window["reference_ids"]):,} references · '
                 f'{len(window["selected_ids"])} selected genomes',
                 fontsize=8.3,color=muted,va="top")
        detail=fig.add_axes([side_x,top-height,.29,height-.033],facecolor=background)
        draw_edges(detail,window["bounds"],group=group)
    fig.text(.05,.071,
             f'{sum(map(len,groups.values())):,} reference genomes · '
             f'{len(selected_ids)} focal tips · {len(layout.edges):,} original edges',
             fontsize=9,color=ink)
    fig.text(.05,.046,"Visual density reflects the reference sample, not natural prevalence. "
             "Detail views have independent camera magnifications, not new phylogenies.",
             fontsize=7.8,color=muted)
    path=Path(out);path.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(path,dpi=dpi,facecolor=background,bbox_inches="tight",pad_inches=.15)
    plt.close(fig)
    return {"png":str(path),"group_by":group_by,
            "layout_shared":True,"original_edges":len(layout.edges),
            "length_mode":length_mode, "display_distances_are_evolutionary":length_mode=='original',
            "selected_original_edges":len(selected_edges),
            "panels":[{"group":w["group"],"references":len(w["reference_ids"]),
                       "selected_ids":list(w["selected_ids"]),
                       "bounds":list(w["bounds"])} for w in windows],
            "density_interpretation":"sampled_reference_tip_visual_only"}
