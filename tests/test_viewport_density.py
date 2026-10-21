"""Opt-in zoom density: finite-support oracle and immutable scientific inputs."""
import json
import math
import numpy as np
import pytest
from phylocloud.cloud_layers import _viewport_density_grid, _blur_float_counts
from phylocloud.cli import run_plot
from phylocloud.synthetic import make_demo
from phylocloud.data import load_selected


@pytest.mark.parametrize('view', [(0.,1.,0.,1.),(-2.,3.,-.01,.01)])
def test_square_cells_and_outside_camera_samples_match_larger_domain(view):
    sigma=3.; grid=_viewport_density_grid(view,128,sigma)
    dx,dy=grid['cell_size_xy']; assert dx==pytest.approx(dy)
    lo,hi,bottom,top=grid['histogram_bounds']
    radius=math.ceil(6*sigma)
    assert min(view[0]-lo,hi-view[1],view[2]-bottom,top-view[3]) >= radius*dx
    ny,nx=grid['histogram_shape']
    # One sample just outside the camera contributes inside. Another lies beyond
    # the finite-support halo. Compare to an independently enlarged same-cell grid.
    ix=int((view[0]-lo)/dx)-1; iy=ny//2
    small=np.zeros((ny,nx)); small[iy,ix]=1
    margin=radius+8; large=np.pad(small,margin)
    large[margin+iy,0]=100
    actual=_blur_float_counts(small,sigma)
    expected=_blur_float_counts(large,sigma)[margin:-margin,margin:-margin]
    xcentres=lo+(np.arange(nx)+.5)*dx
    ycentres=bottom+(np.arange(ny)+.5)*dy
    mask=(ycentres[:,None]+dy/2>=view[2])&(ycentres[:,None]-dy/2<=view[3])&(xcentres[None,:]>=view[0])&(xcentres[None,:]<=view[1])
    np.testing.assert_allclose(actual[mask],expected[mask],atol=1e-15)
    assert actual[mask].max()>0


def test_viewport_allocation_guard():
    with pytest.raises(ValueError,match='too large'):
        _viewport_density_grid((0,1,0,1),900,220,8)


@pytest.mark.parametrize('preset',['cloud','canopy'])
def test_opt_in_detail_keeps_full_membership_edges_and_coordinates(tmp_path,preset):
    inputs=make_demo(tmp_path/'inputs',seed=51,reference_count=60)
    selected=load_selected(inputs['selected'])
    detail=tmp_path/'detail.txt'; detail.write_text('\n'.join(selected[:3])+'\n')
    config=tmp_path/'config.yml'
    config.write_text(f'style:\n  preset: {preset}\n  composition: publication\ncloud:\n'
                      '  resolution: 128\n  zoom_bandwidth_mode: viewport\nexport:\n'
                      '  width_inches: 12\n  height_inches: 10\n  dpi: 60\n')
    overview=run_plot(inputs['tree'],inputs['metadata'],inputs['selected'],config,tmp_path/'view',detail_selected=detail)
    zoom=json.loads((tmp_path/'view_detail.provenance.json').read_text())
    for key in ('coordinate_sha256','reference_membership_sha256','foreground_original_edge_ids','highlighted_tip_ids','reference_genomes'):
        assert zoom[key]==overview[key]
    assert overview['density_zoom_mode']=='overview'
    assert zoom['density_zoom_mode']=='viewport'
    raster=zoom['density_raster']
    assert raster['source_reference_tips']==overview['reference_genomes']==60
    assert raster['requested_viewport_bounds']==pytest.approx(zoom['view_bounds'])
    assert raster['normalization_domain']=='viewport_plus_finite_kernel_support'
    assert raster['cell_size_xy'][0]==pytest.approx(raster['cell_size_xy'][1])
    assert zoom['validation']['all_original_edges_retained']
    assert zoom['annotation_layout']['text_box_overlaps']==0
    # Opt-in must not affect overview bytes; camera remains precisely the same.
    config.write_text(config.read_text().replace('zoom_bandwidth_mode: viewport','zoom_bandwidth_mode: overview'))
    baseline=run_plot(inputs['tree'],inputs['metadata'],inputs['selected'],config,tmp_path/'baseline',detail_selected=detail)
    old_zoom=json.loads((tmp_path/'baseline_detail.provenance.json').read_text())
    assert zoom['view_bounds']==old_zoom['view_bounds']
    for ext in ('svg','pdf','png'):
        assert (tmp_path/f'view.{ext}').read_bytes()==(tmp_path/f'baseline.{ext}').read_bytes()
    assert all(a<b for a,b in zip(raster['maximum_sigma_xy'],baseline['density_raster']['maximum_sigma_xy']))
    config.write_text(config.read_text().replace('zoom_bandwidth_mode: overview','zoom_bandwidth_mode: viewport'))
    run_plot(inputs['tree'],inputs['metadata'],inputs['selected'],config,tmp_path/'repeat',detail_selected=detail)
    for ext in ('svg','pdf','png'):
        assert (tmp_path/f'view_detail.{ext}').read_bytes()==(tmp_path/f'repeat_detail.{ext}').read_bytes()




def test_unsupported_viewport_style_fails_before_export(tmp_path):
    inputs=make_demo(tmp_path/'inputs',reference_count=60)
    config=tmp_path/'invalid.yml'
    config.write_text('style:\n  preset: cloud\n  composition: legacy\n  zoom_to_selected: true\ncloud:\n  zoom_bandwidth_mode: viewport\n')
    with pytest.raises(ValueError,match='publication composition'):
        run_plot(inputs['tree'],inputs['metadata'],inputs['selected'],config,tmp_path/'invalid')
    assert not list(tmp_path.glob('invalid.*svg'))
