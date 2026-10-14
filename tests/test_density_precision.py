"""Density-only changes must retain the full heterogeneous synthetic tree."""
import numpy as np
import matplotlib.pyplot as plt
from phylocloud.cloud_layers import _blur_float_counts, _soft_tail
from phylocloud.render import add_reference_density_overlay
from phylocloud.geometry import TreeGraph, equal_arc_layout, connecting_edges
from phylocloud.data import load_config


def test_float_gaussian_retains_faint_tails_and_is_deterministic():
    counts = np.zeros((129,129))
    counts[64,64] = 1
    before = counts.copy()
    result = _blur_float_counts(counts, 9)
    np.testing.assert_array_equal(counts, before)
    np.testing.assert_array_equal(result, _blur_float_counts(counts, 9))
    assert result[64,90] > 0
    assert len(np.unique(result[64,64:91])) == 27
    assert np.isclose(result.sum(), 1, atol=1e-6)
    assert np.isclose(result[64,70], result[70,64])
    edge = np.zeros_like(counts)
    edge[64,0] = 1
    assert _blur_float_counts(edge,9)[64,-1] < 1e-12


def test_tail_taper_is_continuous_at_old_cutoff():
    threshold = .045
    values = np.array([0, threshold*(1-1e-6), threshold, threshold*(1+1e-6)])
    result = _soft_tail(values, threshold)
    assert result[0] == 0
    assert np.all(np.diff(result) > 0)
    assert abs(result[2]-result[1]) < 1e-7
    assert result[2] == values[2]


def test_legacy_overlay_preserves_zero_edges_outliers_and_selection(tmp_path):
    path = tmp_path/'mixed.nwk'
    path.write_text('((A:0,B:0):0.01,(C:0.02,D:0.03):0.04,E:2);')
    graph = TreeGraph.from_newick(path)
    layout = equal_arc_layout(graph)
    coords = dict(layout.coordinates)
    edges = list(layout.edges)
    selected = connecting_edges(graph,['A','D'])
    style = load_config(None)['style']
    fig, ax = plt.subplots()
    params = add_reference_density_overlay(ax,graph,layout,['B','C','E'],style)
    rgba = np.asarray(ax.images[0].get_array())
    assert np.isfinite(rgba).all() and rgba[:,:,3].max() > 0
    assert len(np.unique(rgba[:,:,3])) > 256
    assert params['sample_weight'] == 'one_per_reference'
    assert layout.coordinates == coords and layout.edges == edges
    assert connecting_edges(graph,['A','D']) == selected
    assert any(length == 0 for _,_,length in edges)
    plt.close(fig)
