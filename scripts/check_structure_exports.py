"""Independent publication export QA. Optional dependency: pypdf==6.20.1.

Run after review_structure_benchmark.py on a publication-composition directory.
"""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image
from pypdf import PdfReader
from pypdf.generic import ContentStream


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    args=parser.parse_args(); root=args.directory; results={}
    review=json.loads((root/'review.json').read_text())
    for name in ('publication','cloud','canopy'):
        report=json.loads((root/(name+'.provenance.json')).read_text())
        cfg=report['configuration']['export']; w,h=cfg['width_inches'],cfg['height_inches']
        svg=ET.parse(root/(name+'.svg')).getroot()
        assert abs(float(svg.get('width').removesuffix('pt'))-w*72)<1e-6
        assert abs(float(svg.get('height').removesuffix('pt'))-h*72)<1e-6
        reader=PdfReader(root/(name+'.pdf')); assert len(reader.pages)==1
        page=reader.pages[0]
        assert abs(float(page.mediabox.width)-w*72)<1e-6
        assert abs(float(page.mediabox.height)-h*72)<1e-6
        embedded=[]
        for ref in page['/Resources']['/Font'].values():
            font=ref.get_object()
            for child in font.get('/DescendantFonts',[font]):
                desc=child.get_object()['/FontDescriptor'].get_object()
                assert any(k in desc for k in ('/FontFile','/FontFile2','/FontFile3'))
            embedded.append(str(font['/BaseFont']))
        text=page.extract_text()
        assert all(f'F{i:02d}' in text for i in range(1,13))
        strokes=sum(op in (b'S',b's',b'B',b'B*',b'b',b'b*') for _,op in ContentStream(page.get_contents(),reader).operations)
        assert strokes>review['scientific_audit']['original_edges']
        if name!='publication': assert len(page.images)>0
        with Image.open(root/(name+'.png')) as image:
            assert image.size==(int(w*cfg['dpi']),int(h*cfg['dpi']))
            assert abs(image.info['dpi'][0]-cfg['dpi'])<.01
            size=image.size
            image.convert('L').save(root/(name+'-grayscale.png'))
        for ext,sha in report['output_sha256'].items():
            assert hashlib.sha256((root/(name+'.'+ext)).read_bytes()).hexdigest()==sha
        assert report['coordinate_sha256']==review['scientific_audit']['coordinate_sha256']
        assert report['view_bounds']==review['shared_view_bounds']
        assert report['annotation_layout']['text_box_overlaps']==0
        assert report['annotation_layout']['clipped_text_boxes']==0
        results[name]=dict(canvas_inches=[w,h],pdf_points=[w*72,h*72],
                           svg_points=[w*72,h*72],png_pixels=size,dpi=cfg['dpi'],
                           embedded_fonts=embedded,pdf_vector_strokes=strokes,
                           pdf_raster_images=len(page.images),extractable_focal_labels=12,
                           text_box_overlaps=0,clipped_text_boxes=0,
                           outer_raster_max_alpha=(report['density_raster'] or {}).get('outer_edge_max_alpha'))
    (root/'export_checks.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))


if __name__=='__main__': main()
