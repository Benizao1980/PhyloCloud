"""Topology-preserving, unrooted equal-arc tree geometry.

The tree's Newick root is only an input-serialization artifact: we treat the
phylogeny as an undirected weighted graph, pick a balanced internal display
centre and assign wedges proportional to terminal counts (Meacham equal-arc).
Every drawn edge has the original inferred length and each node is placed ONCE.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import cos, radians, sin
from pathlib import Path
from typing import Any
from Bio import Phylo


@dataclass
class TreeGraph:
    adjacency: dict[Any, list[tuple[Any, float]]]
    tips: dict[str, Any]
    root_from_file: Any

    @classmethod
    def from_newick(cls, path: str | Path) -> 'TreeGraph':
        tree = Phylo.read(str(path), 'newick')
        adj: dict[Any, list[tuple[Any, float]]] = {}
        tips: dict[str, Any] = {}
        stack = [tree.root]
        while stack:
            node = stack.pop()
            adj.setdefault(node, [])
            if node.is_terminal():
                if not node.name:
                    raise ValueError('Each terminal must have a nonempty identifier')
                if node.name in tips:
                    raise ValueError(f'Duplicate terminal name: {node.name!r}')
                tips[node.name] = node
            for child in node.clades:
                if child.branch_length is None:
                    raise ValueError(f'Missing branch length on edge to {child.name or "internal node"}')
                length = float(child.branch_length)
                if not (0 <= length < float('inf')):
                    raise ValueError(f'Branch length must be finite and nonnegative: {length}')
                adj.setdefault(child, [])
                adj[node].append((child, length))
                adj[child].append((node, length))
                stack.append(child)
        if len(tips) < 3:
            raise ValueError('At least three unique terminals are required')
        return cls(adj, tips, tree.root)


@dataclass
class Layout:
    coordinates: dict[Any, tuple[float, float]]
    edges: list[tuple[Any, Any, float]]  # directed away from display-centre, for indexing only
    centre: Any
    descendants: dict[Any, int]


def equal_arc_layout(graph: TreeGraph, rotate_degrees: float = 0.0) -> Layout:
    """Return unrooted equal-arc positions, with actual lengths and no tip rim.

    Equal-arc is the established initial layout used by PHYLIP's Drawtree.
    Wedges are proportional to terminal count; *no* radial/tip-distance
    normalisation, branch re-inference, or pruning is performed.
    """
    if not graph.adjacency:
        raise ValueError('Empty tree')
    # Tree centroid: choose an internal vertex whose largest side has the
    # fewest terminal genomes; this avoids sensitivity to arbitrary Newick root.
    start = next(iter(graph.adjacency))
    parents: dict[Any, Any | None] = {start: None}
    order = [start]
    for node in order:
        for neighbour, _ in graph.adjacency[node]:
            if neighbour not in parents:
                parents[neighbour] = node
                order.append(neighbour)
    if len(order) != len(graph.adjacency):
        raise ValueError('Disconnected tree')
    counts: dict[Any, int] = {}
    tip_nodes = set(graph.tips.values())
    for node in reversed(order):
        counts[node] = (1 if node in tip_nodes else 0) + sum(
            counts[n] for n, _ in graph.adjacency[node] if parents.get(n) is node
        )
    total = len(graph.tips)
    def worst_split(node: Any) -> int:
        return max((counts[n] if parents.get(n) is node else total - counts[node])
                   for n, _ in graph.adjacency[node])
    candidates = [n for n in order if len(graph.adjacency[n]) >= 3]
    if not candidates:
        candidates = [n for n in order if len(graph.adjacency[n]) >= 2]
    indices = {node: i for i, node in enumerate(order)}
    centre = min(candidates, key=lambda n: (worst_split(n), indices[n]))

    # Orient all original edges from centre, without editing topology or lengths.
    parents = {centre: None}
    order = [centre]
    edge_lengths: dict[tuple[Any, Any], float] = {}
    for node in order:
        for child, length in graph.adjacency[node]:
            if child not in parents:
                parents[child] = node
                order.append(child)
                edge_lengths[node, child] = length
    descendants = {}
    tip_nodes = set(graph.tips.values())
    for node in reversed(order):
        descendants[node] = (1 if node in tip_nodes else 0) + sum(
            descendants[ch] for ch, _ in graph.adjacency[node] if parents.get(ch) is node
        )
    coords: dict[Any, tuple[float, float]] = {centre: (0.0, 0.0)}
    edges: list[tuple[Any, Any, float]] = []
    # Wedge is the available angular interval for directions *away* from parent.
    # Child tips are not moved to a shared circumference.
    stack = [(centre, radians(rotate_degrees), radians(rotate_degrees + 360.0))]
    while stack:
        node, low, high = stack.pop()
        children = [(ch, length) for ch, length in graph.adjacency[node]
                    if parents.get(ch) is node]
        denom = sum(descendants[ch] for ch, _ in children)
        cursor = low
        jobs = []
        for child, length in children:
            width = (high - low) * descendants[child] / denom
            end = cursor + width
            angle = (cursor + end) * 0.5
            px, py = coords[node]
            coords[child] = (px + length * cos(angle), py + length * sin(angle))
            edges.append((node, child, length))
            jobs.append((child, cursor, end))
            cursor = end
        stack.extend(reversed(jobs))
    return Layout(coords, edges, centre, descendants)


def connecting_edges(graph: TreeGraph, selected_ids: list[str]) -> set[frozenset[Any]]:
    """Unique minimal connected edge set spanning selected *original* tips.

    Repeatedly peel unselected degree-one vertices. This exactly obtains the
    Steiner subtree in a tree without adding, collapsing or changing any edge.
    """
    if len(set(selected_ids)) != len(selected_ids):
        raise ValueError('Selected genome identifiers must be unique')
    missing = sorted(set(selected_ids) - graph.tips.keys())
    if missing:
        raise ValueError('Selected identifiers absent from Newick: ' + ', '.join(missing[:12]))
    if not selected_ids:
        raise ValueError('Select at least one genome')
    terminals = {graph.tips[name] for name in selected_ids}
    degrees = {n: len(edges) for n, edges in graph.adjacency.items()}
    removed: set[Any] = set()
    to_remove = deque(n for n, deg in degrees.items() if deg <= 1 and n not in terminals)
    while to_remove:
        node = to_remove.popleft()
        if node in removed or node in terminals:
            continue
        removed.add(node)
        for neighbour, _ in graph.adjacency[node]:
            if neighbour not in removed:
                degrees[neighbour] -= 1
                if degrees[neighbour] <= 1 and neighbour not in terminals:
                    to_remove.append(neighbour)
    return {frozenset((n, other)) for n, edges in graph.adjacency.items()
            for other, _ in edges if n not in removed and other not in removed}


def edge_taxa(layout: Layout, graph: TreeGraph, taxonomy: dict[str, str]) -> dict[frozenset[Any], str | None]:
    """Species for pure downstream branches; mixed edges are neutral."""
    name_for_tip = {v: k for k, v in graph.tips.items()}
    # Determine children using outward layout edges, avoiding Newick-root bias.
    children: dict[Any, list[Any]] = {n: [] for n in layout.coordinates}
    for parent, child, _ in layout.edges:
        children[parent].append(child)
    species = {}
    for node in reversed(list(layout.coordinates.keys())):
        if node in name_for_tip:
            species[node] = taxonomy.get(name_for_tip[node])
        else:
            labels = {species[ch] for ch in children[node]}
            species[node] = next(iter(labels)) if len(labels) == 1 else None
    return {frozenset((p, c)): species[c] for p, c, _ in layout.edges}
