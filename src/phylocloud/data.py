"""Strict input and style loaders."""
from __future__ import annotations
import csv
import json
from pathlib import Path
import yaml

MASTER = {
    'white': '#FFFFFF', 'ink': '#2F2A26', 'stone': '#B8B0A5',
    'light_grey': '#DDD7CE', 'warm_grey': '#8B847C',
    'sage': '#6F8F73', 'powder_blue': '#8FB7C7', 'dusty_pink': '#D899A5',
    'lavender': '#B6A1C4', 'mustard': '#D7A928', 'teal': '#3E7C78',
    'burgundy': '#8C2943', 'seafoam': '#80AD9B', 'apricot': '#E9A46B',
}
# Values and names matched to Ben-style data/master.json, data/presets.json,
# inspected 2026-10-12. No dependency on a live GitHub connection.
SPECIES_COLORS = {
    'Campylobacter infans': 'sage',
    'Campylobacter_D jejuni': 'powder_blue',
    'Campylobacter jejuni': 'powder_blue',
    'Campylobacter coli': 'dusty_pink',
    'Campylobacter upsaliensis': 'lavender',
    'Campylobacter fetus': 'mustard',
    'Campylobacter_D sp934718785': 'teal',
    'Campylobacter_D coli': 'dusty_pink',
    'Campylobacter_D coli_A': 'mustard',
    'Campylobacter_D coli_B': 'apricot',
    'Campylobacter_D upsaliensis': 'lavender',
    'Campylobacter_D lari': 'seafoam',
}

DEFAULT_CONFIG = {
    'layout': {'rotation_degrees': 10.0, 'angle_mode': 'tip_count'},
    'style': {
        'species_background': True,
        'preset': 'publication',
        'reference_alpha': 0.23,
        'reference_width': 0.42,
        'halo_alpha': 0.045,
        'halo_width': 2.4,
        'density_overlay': False,
        'zoom_to_selected': False,
        'density_opacity': 0.11,
        'density_sigma_px': 9.0,
        'foreground_width': 1.8,
        'foreground_color': 'ink',
        'mag_size': 64,
        'label_font_size': 9.2,
        'title': 'PhyloCloud | two-layer unrooted diversity',
        'subtitle': '',
        'species_colors': SPECIES_COLORS.copy(),
    },
    'cloud': {
        'group_by': 'species', 'label_by': 'same', 'colours': {},
        'opacity': 0.72, 'bandwidth_px': 13, 'resolution': 600,
        'density_engine': 'multiscale',
        'max_density_groups': 12,
        'min_label_references': 15, 'max_labels': 7,
    },
    'export': {'width_inches': 13, 'height_inches': 10.5, 'dpi': 400},
}


def load_metadata(path: str | Path) -> dict[str, dict[str, str]]:
    path = Path(path)
    with path.open(newline='', encoding='utf8') as handle:
        first_line = handle.readline()
        handle.seek(0)
        reader = csv.DictReader(handle, delimiter='\t' if path.suffix.lower() == '.tsv' else ',')
        if not reader.fieldnames or not {'genome_id', 'species'}.issubset(reader.fieldnames):
            raise ValueError('Metadata needs genome_id and species columns')
        result = {}
        for row in reader:
            name = row['genome_id'].strip()
            if not name or name in result:
                raise ValueError(f'Blank/duplicate metadata genome_id: {name!r}')
            result[name] = {k: (v or '').strip() for k,v in row.items()}
    return result


def load_selected(path: str | Path) -> list[str]:
    with Path(path).open(encoding='utf8') as f:
        result = [line.strip() for line in f if line.strip() and not line.lstrip().startswith('#')]
    if not result:
        raise ValueError('Selected-genomes file is empty')
    return result


def load_config(path: str | Path | None) -> dict:
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    # Read once so presets are applied before individual overrides.
    override = yaml.safe_load(Path(path).read_text(encoding='utf8')) or {} if path else {}
    if not isinstance(override, dict):
        raise ValueError('Config must be a mapping')
    preset = (override.get('style', {}) or {}).get('preset', cfg['style']['preset'])
    if preset not in PRESETS:
        raise ValueError(f'Unknown style preset {preset!r}; choose {sorted(PRESETS)}')
    cfg['style'].update(PRESETS[preset])
    if path:
        def deep_merge(base, changes):
            for k,v in changes.items():
                if isinstance(v, dict) and isinstance(base.get(k),dict):
                    deep_merge(base[k],v)
                else:
                    base[k] = v
        deep_merge(cfg, override)
    return cfg


PRESETS = {
    'publication': {
        'species_background': False, 'density_overlay': False, 'reference_alpha': 0.25,
        'reference_width': 0.42, 'halo_alpha': 0.014,
        'halo_width': 1.25, 'foreground_width': 1.55,
        'mag_size': 38, 'label_font_size': 8.5,
    },
    'cloud': {
        'species_background': True, 'density_overlay': False, 'reference_alpha': .28,
        'reference_width': .38, 'halo_alpha': .032, 'halo_width': 3.4,
        'foreground_width': 2.0, 'mag_size': 52, 'label_font_size': 8.8,
        'background': '#FCFCFA',
    },
    'canopy': {
        'species_background': True, 'density_overlay': False, 'reference_alpha': .36,
        'reference_width': .34, 'halo_alpha': .045, 'halo_width': 3.2,
        'foreground_width': 1.85, 'mag_size': 52, 'label_font_size': 8.8,
        'background': '#FCFCFA',
    },
    'constellation': {
        'species_background': True, 'density_overlay': False, 'reference_alpha': .35,
        'reference_width': .45, 'halo_alpha': .08, 'halo_width': 3.1,
        'foreground_width': 1.9, 'mag_size': 48, 'label_font_size': 9,
        'background': '#111C2A', 'foreground_color': '#F1F0E8',
        'cloud_label_color': '#F2F3EB',
    },
    'river': {
        'species_background': True, 'density_overlay': False, 'reference_alpha': .22,
        'reference_width': .72, 'halo_alpha': .042, 'halo_width': 10.2,
        'foreground_width': 1.9, 'mag_size': 50, 'label_font_size': 8.8,
        'background': '#FCFCFA',
    },
    'soft_cloud': {
        'species_background': True, 'density_overlay': True, 'density_opacity': 0.20,
        'reference_alpha': 0.18,
        'reference_width': 0.40, 'halo_alpha': 0.045,
        'halo_width': 3.3, 'foreground_width': 1.7,
        'mag_size': 47, 'label_font_size': 8.7,
    },
}


def color(name: str) -> str:
    return MASTER.get(name, name)
