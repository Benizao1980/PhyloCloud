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
from .data import color
from .geometry import Layout, TreeGraph, connecting_edges, edge_taxa


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
        for i in range(1,len(group)):
            last,now=group[i-1],group[i]
            if positions[now][1]<positions[last][1]+label_spacing:
                positions[now][1]=positions[last][1]+label_spacing
    for name,x,y,face in plotted:
        tx,ty,side=positions[name]
        label=metadata.get(name,{}).get('label') or name
        ax.plot([x,tx-side*0.009*spread],[y,ty],color=face,
                alpha=.62,linewidth=.75,zorder=5)
        ax.text(tx,ty,label,fontsize=s['label_font_size'],color=color('ink'),
                ha='left' if side==1 else 'right',va='center',weight='semibold',zorder=8)
    ymin=min([lowy]+[positions[n][1] for n in selected_ids]); ymax=max([highy]+[positions[n][1] for n in selected_ids])
    xmargin=.19*spread; ymargin=.15*spread
    ax.set_xlim(lowx-xmargin,highx+xmargin); ax.set_ylim(ymin-ymargin,ymax+ymargin)
    ax.set_aspect('equal',adjustable='box');ax.axis('off')
    fig.text(.055,.965,s['title'],fontsize=19,ha='left',va='top',
             fontweight='semibold',color=color('ink'))
    if s.get('subtitle'):
        fig.text(.055,.929,s['subtitle'],ha='left',va='top',
                 fontsize=10,color=color('warm_grey'))
    handles=[Line2D([0],[0],color=color('stone'),lw=2,alpha=.65,label=f'Reference branches (n={len(graph.tips)-len(selected_ids):,})'),
             Line2D([0],[0],color=color('ink'),lw=2,label='Minimum connecting subtree'),
             Line2D([0],[0],color=color('sage'),marker='o',linestyle='None',markersize=7,
                    markeredgecolor=color('ink'),label=f'Selected genomes (n={len(selected_ids)})')]
    fig.legend(handles=handles,ncol=3,frameon=False,loc='lower center',bbox_to_anchor=(.5,.015),fontsize=9)
    fig.text(.055,.045,'UNROOTED EQUAL-ARC  ·  ORIGINAL EDGE LENGTHS  ·  SINGLE SHARED LAYOUT',
             size=8,color=color('warm_grey'))
    fig.subplots_adjust(left=.025,right=.98,bottom=.11,top=.86)
    for ext in ['svg','pdf','png']:
        meta = ({'Date': None, 'Creator': 'PhyloCloud v0.1.0a0'} if ext == 'svg' else
                    {'CreationDate': None, 'ModDate': None, 'Creator': 'PhyloCloud v0.1.0a0'}
                    if ext == 'pdf' else {'Software': 'PhyloCloud v0.1.0a0'})
        fig.savefig(path.with_suffix('.'+ext),dpi=exp['dpi'],facecolor='white',
                    bbox_inches='tight',pad_inches=.18,metadata=meta)
    plt.close(fig)
    return {'tips':len(graph.tips),'selected':len(selected_ids),
            'tree_edges':len(layout.edges),'foreground_edges':len(fg),
            'output_stem':str(path)}
