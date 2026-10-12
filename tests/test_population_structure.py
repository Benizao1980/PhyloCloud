"""Fidelity checks: no prettier layout may replace the actual population structure."""
from io import StringIO
from itertools import combinations
from math import hypot

import pytest
from Bio import Phylo

from phylocloud.geometry import TreeGraph, connecting_edges, equal_arc_layout


# Deliberately unbalanced sampling, divergent long tips, and mixed clades.
TREE = (
    "(((A:0.01,B:0.015):0.02,(C:0.018,D:0.011):0.023):0.09,"
    "((E:0.02,F:0.022):0.03,G:0.045):0.17,"
    "(H:0.9,(I:0.03,J:0.035):0.02):0.08);"
)


def fixture(tmp_path):
    path = tmp_path / "population_structure.nwk"
    path.write_text(TREE)
    return TreeGraph.from_newick(path), Phylo.read(StringIO(TREE), "newick")


def distance_on_graph(graph, name1, name2):
    """Compute original patristic distance without using plotted coordinates."""
    target = graph.tips[name2]
    stack = [(graph.tips[name1], None, 0.0)]
    while stack:
        node, parent, dist = stack.pop()
        if node is target:
            return dist
        stack.extend((neighbor, node, dist + length)
                     for neighbor, length in graph.adjacency[node] if neighbor is not parent)
    raise AssertionError("Graph disconnected")


def edge_splits(graph, edges):
    """Return canonical unrooted bipartitions induced by provided original edges."""
    universe = frozenset(graph.tips)
    tip_name = {node: name for name, node in graph.tips.items()}
    splits = set()
    for a, b in edges:
        seen = {a}
        stack = [a]
        while stack:
            node = stack.pop()
            for neighbor, _ in graph.adjacency[node]:
                if (node is a and neighbor is b) or (node is b and neighbor is a):
                    continue
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        side = frozenset(tip_name[n] for n in seen if n in tip_name)
        other = universe - side
        if len(side) > 1 and len(other) > 1:
            splits.add(min((side, other), key=lambda s: (len(s), tuple(sorted(s)))))
    return splits


def test_all_original_unrooted_splits_retained(tmp_path):
    graph, _ = fixture(tmp_path)
    original = {frozenset((u, v)) for u, nbrs in graph.adjacency.items()
                for v, _ in nbrs}
    expected = edge_splits(graph, ((tuple(e)[0], tuple(e)[1]) for e in original))
    for angle in (0, 37, 177):
        layout = equal_arc_layout(graph, angle)
        displayed = {(p, c) for p, c, _ in layout.edges}
        assert {frozenset(e) for e in displayed} == original
        assert edge_splits(graph, displayed) == expected
        assert len(layout.coordinates) == len(graph.adjacency)


def test_patristic_distances_and_relative_divergence(tmp_path):
    graph, source = fixture(tmp_path)
    layout = equal_arc_layout(graph, 27)
    # Every original edge is still drawn at its original linear length.
    for parent, child, branch_length in layout.edges:
        x1, y1 = layout.coordinates[parent]
        x2, y2 = layout.coordinates[child]
        assert hypot(x2 - x1, y2 - y1) == pytest.approx(branch_length, abs=1e-11)
    for first, second in combinations(sorted(graph.tips), 2):
        assert distance_on_graph(graph, first, second) == pytest.approx(
            source.distance(first, second))
    assert distance_on_graph(graph, "A", "B") < distance_on_graph(graph, "A", "H")
    assert distance_on_graph(graph, "I", "J") < distance_on_graph(graph, "I", "H")


def test_foreground_only_original_edges(tmp_path):
    graph, _ = fixture(tmp_path)
    layout = equal_arc_layout(graph)
    all_edges = {frozenset((p, c)) for p, c, _ in layout.edges}
    selected = connecting_edges(graph, ["A", "D", "H", "J"])
    assert selected <= all_edges
    assert selected
    for node in [graph.tips[name] for name in ("A", "D", "H", "J")]:
        assert any(node in edge for edge in selected)
