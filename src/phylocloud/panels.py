"""Optional comparative full-tree and fixed-coordinate detail presentation.

The two panels are produced from the SAME input graph and LayoutMap. The
contact sheet is intentionally raster; separate SVG/PDF outputs preserve the
original vector branches and text.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def compose_preview(overview: str | Path, detail: str | Path, out: str | Path) -> dict:
    """Create labelled overview/detail contact sheet; never modify tree geometry."""
    overview, detail, out = Path(overview), Path(detail), Path(out)
    with Image.open(overview).convert('RGB') as ov, Image.open(detail).convert('RGB') as dt:
        width, gap, pad, top, bottom = 2800, 26, 68, 170, 86
        panel_width = (width - pad * 2 - gap) // 2
        panel_height = 1160
        result = Image.new('RGB', (width, top + panel_height + bottom), '#F9F9F6')
        d = ImageDraw.Draw(result)
        try:
            title = ImageFont.truetype('DejaVuSans.ttf', 34)
            body = ImageFont.truetype('DejaVuSans.ttf', 19)
            subtitle = ImageFont.truetype('DejaVuSans.ttf', 16)
        except OSError:
            title = body = subtitle = ImageFont.load_default()
        d.text((pad, 32), 'PhyloCloud  |  full-tree context and local detail', fill='#2F2A26',font=title)
        d.text((pad, 93), 'Both views use the identical full-tree coordinates and branch lengths; the detail is a geometric crop.', fill='#716E66',font=body)
        for i, (im, label) in enumerate([(ov, 'A   Full reference phylogeny'), (dt, 'B   Selected-genome neighbourhood')]):
            x = pad + i * (panel_width + gap)
            d.rounded_rectangle((x,top,x+panel_width,top+panel_height),radius=14,fill='#FFFFFF',outline='#D8D6D0',width=2)
            d.text((x+26,top+21), label, font=body,fill='#344A48')
            thumb=im.copy()
            thumb.thumbnail((panel_width-32,panel_height-90),Image.Resampling.LANCZOS)
            ix=x+(panel_width-thumb.width)//2
            iy=top+65+(panel_height-85-thumb.height)//2
            result.paste(thumb,(ix,iy))
        d.text((pad,top+panel_height+29),'Display comparison only  |  Original SVG/PDF tree paths remain separately editable', font=subtitle,fill='#77736B')
        out.parent.mkdir(parents=True, exist_ok=True)
        result.save(out, optimize=True)
        return {'comparison_png':str(out), 'composition':'raster_contact_sheet', 'source_views':[str(overview),str(detail)]}
