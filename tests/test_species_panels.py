"""Data-derived species-panel selection and geometry safety regression."""
from phylocloud.synthetic import make_demo
from phylocloud.data import load_metadata, load_selected
from phylocloud.geometry import TreeGraph, equal_arc_layout
from phylocloud.species_panels import plan_species_panels, draw_species_panels
import json
import pytest


def test_windows_are_exact_metadata_groups_and_preserve_original_xy(tmp_path):
    files = make_demo(tmp_path / "demo", seed=47, reference_count=60)
    graph = TreeGraph.from_newick(files["tree"])
    metadata = load_metadata(files["metadata"])
    selected = load_selected(files["selected"])
    layout = equal_arc_layout(graph)
    original = dict(layout.coordinates)
    panels = plan_species_panels(graph, layout, metadata, selected, max_panels=3)
    assert len(panels) == 3
    assert any(len(p["selected_ids"]) >= 2 for p in panels)
    for panel in panels:
        assert panel["reference_ids"]
        assert all(metadata[n]["species"] == panel["group"] for n in panel["reference_ids"])
        assert all(metadata[n]["species"] == panel["group"] for n in panel["selected_ids"])
        assert panel["bounds"][1] > panel["bounds"][0]
        assert panel["bounds"][3] > panel["bounds"][2]
    assert layout.coordinates == original


def test_species_composition_emits_png_without_adding_tree_edges(tmp_path):
    files = make_demo(tmp_path / "demo", seed=38, reference_count=60)
    graph = TreeGraph.from_newick(files["tree"])
    metadata = load_metadata(files["metadata"])
    selected = load_selected(files["selected"])
    layout = equal_arc_layout(graph)
    original = dict(layout.coordinates)
    output = tmp_path / "species_panels.png"
    result = draw_species_panels(graph, layout, metadata, selected, output,
                                 max_panels=2, dpi=70)
    assert output.exists() and output.stat().st_size > 4000
    assert result["layout_shared"] is True
    assert result["original_edges"] == len(graph.adjacency) - 1
    assert all(n in graph.tips for p in result["panels"] for n in p["selected_ids"])
    assert layout.coordinates == original


def test_panel_limit_and_metadata_validation(tmp_path):
    files = make_demo(tmp_path / "demo", seed=4, reference_count=60)
    g = TreeGraph.from_newick(files["tree"])
    m = load_metadata(files["metadata"])
    ids = load_selected(files["selected"])
    l = equal_arc_layout(g)
    with pytest.raises(ValueError,match="max_panels"):
        plan_species_panels(g, l, m, ids, max_panels=0)
    with pytest.raises(ValueError,match="grouping column"):
        plan_species_panels(g, l, m, ids, group_by="missing_column")
