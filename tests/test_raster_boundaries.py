"""Synthetic boundary, scientific-invariant and hybrid-export regressions."""
import hashlib
import math
from types import SimpleNamespace
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
import numpy as np
import pytest

from phylocloud.cloud_layers import (
    _blur_float_counts, _density_grid, _multiscale_reference_atmosphere,
    compute_cloud_fields,
)
from phylocloud.cli import run_plot
from phylocloud.data import load_config
from phylocloud.geometry import TreeGraph, equal_arc_layout, connecting_edges


@pytest.mark.parametrize('shape', [(128,128),(128,900),(900,128)])
def test_padding_keeps_histogram_pixel_centres_and_physical_bandwidth(shape):
    bounds=(-3.,7.,-.1,.2)
    grid=_density_grid(bounds,shape,12.)
    pad=grid['padding_px_per_side']
    ny,nx=shape
    xmin,xmax,ymin,ymax=grid['raster_bounds']
    dx,dy=grid['cell_size_xy']
    assert (xmax-xmin)/(nx+2*pad)==pytest.approx(dx)
    assert (ymax-ymin)/(ny+2*pad)==pytest.approx(dy)
    assert xmin+(pad+.5)*dx==pytest.approx(bounds[0]+.5*dx)
    assert ymin+(pad+.5)*dy==pytest.approx(bounds[2]+.5*dy)
    assert grid['maximum_sigma_xy']==[12*dx,12*dy]


@pytest.mark.parametrize('sigma',[.1,.5,9.])
def test_sampled_kernel_matches_independent_discrete_gaussian(sigma):
    count=np.zeros((41,53))
    count[20,26]=1.
    result=_blur_float_counts(count,sigma)
    y,x=np.mgrid[:41,:53]
    expected=np.exp(-.5*(((y-20)/sigma)**2+((x-26)/sigma)**2))
    radius=math.ceil(6*sigma)
    expected[(abs(y-20)>radius)|(abs(x-26)>radius)]=0
    norm=np.exp(-.5*(np.arange(-radius,radius+1)/sigma)**2).sum()**2
    np.testing.assert_allclose(result,expected/norm,atol=1e-15)


@pytest.mark.parametrize('bandwidth',[.1,5.,13.])
def test_tip_fields_keep_all_corner_samples_and_fade_before_raster_edge(bandwidth):
    # Histogram-only geometry fixture: each corner is an observed reference,
    # with one nonmonophyletic metadata category; no tree or inferred grouping.
    coords={'a':(0.,0.),'b':(1.,0.),'c':(0.,1.),'d':(1.,1.)}
    graph=SimpleNamespace(tips={n:n for n in coords})
    layout=SimpleNamespace(coordinates=coords)
    metadata={n:{'species':'Mixed'} for n in coords}
    cfg=load_config(None)
    cfg['cloud'].update(resolution=128,bandwidth_px=bandwidth)
    fields,counts=compute_cloud_fields(graph,layout,metadata,list(coords),cfg['cloud'],{},(0,1,0,1))
    field=fields[0]
    alpha=field['rgba'][:,:,3]
    grid=field['raster']; pad=grid['padding_px_per_side']
    assert counts=={'Mixed':4}
    np.testing.assert_array_equal(field['points'],list(coords.values()))
    assert field['bounds']==(0,1,0,1)  # label domain is independent of raster
    assert min(alpha[pad,pad],alpha[pad,-pad-1],alpha[-pad-1,pad],alpha[-pad-1,-pad-1])>0
    assert max(alpha[0].max(),alpha[-1].max(),alpha[:,0].max(),alpha[:,-1].max())<1e-6
    if bandwidth>=5:
        assert alpha[pad-3,pad]>0  # real halo outside the old raster boundary
    assert layout.coordinates==coords


def test_padding_preserves_interior_field_of_previous_default_kernel():
    hist=np.zeros((128,180)); hist[2,3]=70; hist[80,155]=2
    sigma=13.
    # Independent copy of the PREVIOUS analytic-frequency implementation.
    old_pad=math.ceil(3.5*sigma)
    old_counts=np.pad(hist,old_pad)
    ky=np.fft.fftfreq(old_counts.shape[0])[:,None]
    kx=np.fft.rfftfreq(old_counts.shape[1])[None,:]
    old=np.maximum(0,np.fft.irfft2(np.fft.rfft2(old_counts)*
        np.exp(-2*np.pi**2*sigma**2*(kx*kx+ky*ky)),s=old_counts.shape))
    old=old[old_pad:-old_pad,old_pad:-old_pad]
    grid=_density_grid((0,1,0,1),hist.shape,sigma)
    pad=grid['padding_px_per_side']
    new=_blur_float_counts(np.pad(hist,pad),sigma)[pad:-pad,pad:-pad]
    np.testing.assert_allclose(new,old,rtol=0,atol=1e-9)


def mixed_tree(tmp_path):
    tree=tmp_path/'tree.nwk'
    tree.write_text('((A:0,B:0):.01,(C:.02,D:.03):.04,E:2,F:.4);')
    metadata=tmp_path/'metadata.tsv'
    metadata.write_text('genome_id\tspecies\tsource\tlabel\n'+''.join(
        f'{n}\t{group}\t{source}\t{n}\n' for n,group,source in [
            ('A','Mixed','selected'),('B','Mixed','reference'),
            ('C','Mixed','reference'),('D','Other','selected'),
            ('E','Sparse outlier','reference'),('F','Other','reference')]))
    selected=tmp_path/'selected.txt'; selected.write_text('A\nD\n')
    return tree,metadata,selected


def test_multiscale_render_does_not_mutate_heterogeneous_tree(tmp_path):
    tree_path,_,_=mixed_tree(tmp_path)
    graph=TreeGraph.from_newick(tree_path)
    layout=equal_arc_layout(graph)
    before_coords=dict(layout.coordinates); before_edges=list(layout.edges)
    before_graph={n:list(edges) for n,edges in graph.adjacency.items()}
    selection=connecting_edges(graph,['A','D'])
    meta={n:{'species':('Mixed' if n in 'ABC' else n)} for n in graph.tips}
    xy=np.asarray(list(layout.coordinates.values()))
    low=xy.min(axis=0); high=xy.max(axis=0)
    bounds=(low[0]-.001,high[0]+.001,low[1]-.001,high[1]+.001)
    cfg=load_config(None); cfg['cloud'].update(resolution=128,bandwidth_px=5)
    fig,ax=plt.subplots()
    fields,counts=_multiscale_reference_atmosphere(
        ax,graph,layout,meta,['B','C','E','F'],cfg['cloud'],{},bounds,'cloud')
    assert sum(counts.values())==4 and counts['Mixed']==2
    assert layout.coordinates==before_coords and layout.edges==before_edges
    assert graph.adjacency==before_graph and connecting_edges(graph,['A','D'])==selection
    assert any(length==0 for _,_,length in layout.edges)
    alpha=np.asarray(ax.images[0].get_array())[:,:,3]
    assert max(alpha[0].max(),alpha[-1].max(),alpha[:,0].max(),alpha[:,-1].max())<1e-6
    assert list(ax.images[0].get_extent())==fields[0]['raster']['raster_bounds']
    plt.close(fig)


@pytest.mark.parametrize('style,engine', [('cloud','multiscale'),('canopy','multiscale'),
                                         ('cloud','legacy'),('soft_cloud','multiscale')])
def test_hybrid_exports_and_raster_camera_provenance(tmp_path,style,engine):
    tree,meta,selected=mixed_tree(tmp_path)
    config=tmp_path/'config.yml'
    config.write_text(f'style:\n  preset: {style}\ncloud:\n  resolution: 128\n'
                      f'  bandwidth_px: 13\n  density_engine: {engine}\n'
                      'export:\n  width_inches: 7.1\n  height_inches: 5.5\n  dpi: 300\n')
    out=tmp_path/'figure'
    report=run_plot(tree,meta,selected,config,out)
    raster=report['density_raster']
    assert raster['outer_edge_max_alpha']<1e-6
    assert raster['raster_shape'][0]>raster['histogram_shape'][0]
    assert raster['kernel_discretization']=='normalized_sampled_gaussian'
    assert report['validation']['all_original_edges_retained']
    assert report['validation']['zero_length_edges']==2
    assert report['validation']['max_absolute_edge_length_error']<1e-10
    assert report['density_render_method']=='hybrid_vector_tree_raster_wash'
    view=report['view_bounds']; visible=raster['visible_bounds']
    assert view[0]<=visible[0] and view[1]>=visible[1]
    assert view[2]<=visible[2] and view[3]>=visible[3]
    svg=ET.parse(out.with_suffix('.svg'))
    ns={'svg':'http://www.w3.org/2000/svg'}
    assert svg.findall('.//svg:image',ns)
    assert svg.findall('.//svg:path',ns) and svg.findall('.//svg:text',ns)
    for gid,count in [('reference-tree-edges',report['tree_edges']),
                      ('selected-original-edges',report['foreground_edges'])]:
        group=svg.find(f".//svg:g[@id='{gid}']",ns)
        assert group is not None
        assert len(group.findall('svg:path',ns))==count
        assert not group.findall('.//svg:image',ns)
    pdf=out.with_suffix('.pdf').read_bytes()
    assert pdf.startswith(b'%PDF-') and b'/Font' in pdf and b'/Subtype /Image' in pdf
    assert out.with_suffix('.png').is_file()
    assert report['export_parameters']['dpi']==300
    for ext,expected in report['output_sha256'].items():
        assert hashlib.sha256(out.with_suffix('.'+ext).read_bytes()).hexdigest()==expected


def test_raster_budget_fails_before_allocating_large_layers():
    with pytest.raises(ValueError,match='reduce bandwidth'):
        _density_grid((0,1,0,1),(900,900),220,40)
    with pytest.raises(ValueError,match='max_density_groups'):
        _density_grid((0,1,0,1),(900,900),35,40)


def test_explicit_zoom_is_not_expanded_by_cloud_padding(tmp_path):
    tree,meta,selected=mixed_tree(tmp_path)
    views=[]
    for style in ('publication','cloud'):
        config=tmp_path/(style+'.yml')
        config.write_text(f'style:\n  preset: {style}\n  zoom_to_selected: true\n'
                          'cloud:\n  resolution: 128\nexport:\n  dpi: 75\n')
        report=run_plot(tree,meta,selected,config,tmp_path/style)
        assert report['density_camera_policy']=='explicit_selected_crop'
        views.append(report['view_bounds'])
    assert views[0]==views[1]
