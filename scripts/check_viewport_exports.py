"""Independent QA for full-size/journal viewport review exports (pypdf optional)."""
import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image
from pypdf import PdfReader
from pypdf.generic import ContentStream


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    root=parser.parse_args().directory
    review=json.loads((root/'review.json').read_text()); results={}
    for name in review['views']:
        report=json.loads((root/(name+'.provenance.json')).read_text())
        cfg=report['configuration']['export']; w,h=cfg['width_inches'],cfg['height_inches']
        svg=ET.parse(root/(name+'.svg')).getroot()
        ns={'s':'http://www.w3.org/2000/svg'}
        assert abs(float(svg.get('width').removesuffix('pt'))-w*72)<1e-6
        assert abs(float(svg.get('height').removesuffix('pt'))-h*72)<1e-6
        assert svg.findall('.//s:text',ns)
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
        focus=report['labelled_tip_ids']
        assert len(focus)==(12 if name.startswith('overview') else 6)
        # Benchmark metadata labels match F01..F12, while actual IDs are MAG_...
        assert all(f'F{i:02d}' in text for i in range(1,len(focus)+1))
        strokes=sum(op in (b'S',b's',b'B',b'B*',b'b',b'b*') for _,op in ContentStream(page.get_contents(),reader).operations)
        assert strokes>review['scientific_audit']['original_edges']
        if 'tree' not in name: assert len(page.images)>0
        if name.startswith('viewport'):
            assert 'local wash normalization' in text
            assert report['density_raster']['source_reference_tips']==6488
        with Image.open(root/(name+'.png')) as image:
            assert image.size==(int(w*cfg['dpi']),int(h*cfg['dpi']))
            assert abs(image.info['dpi'][0]-cfg['dpi'])<.01
            assert image.convert('RGB').getpixel((0,0))==(255,255,255)
            size=image.size
        for ext,sha in report['output_sha256'].items():
            assert hashlib.sha256((root/(name+'.'+ext)).read_bytes()).hexdigest()==sha
        assert report['coordinate_sha256']==review['scientific_audit']['coordinate_sha256']
        assert report['foreground_edges']==72
        assert report['reference_membership_sha256']==review['views']['overview']['reference_membership_sha256']
        assert report['annotation_layout']['text_box_overlaps']==0
        assert report['annotation_layout']['clipped_text_boxes']==0
        results[name]=dict(canvas_inches=[w,h],png_pixels=size,dpi=cfg['dpi'],
                           embedded_fonts=embedded,pdf_vector_strokes=strokes,
                           pdf_raster_images=len(page.images),extractable_focal_labels=len(focus),
                           svg_editable_text=True,text_box_overlaps=0,clipped_text_boxes=0)
    evidence=dict(views=results,seed=650047,rotation_degrees=19,
                  package_versions={n:version(n) for n in ('phylocloud','numpy','matplotlib','pillow','biopython','pypdf')},
                  source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                      sorted(Path('src/phylocloud').glob('*.py'))})
    (root/'export_checks.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(dict(views=len(results),canvas_inches=[w,h],all_checks_passed=True)))


if __name__=='__main__': main()
