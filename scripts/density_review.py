"""Reproduce synthetic before/after exports; run from the repository root.

Uses the committed cc5beb4 renderer as baseline, never private inputs.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import types

from PIL import Image, ImageDraw
import phylocloud.cli as cli
from phylocloud.synthetic import make_demo

out = Path('examples/outputs/density_review')
out.mkdir(parents=True, exist_ok=True)
paths = make_demo(out/'inputs', seed=47, reference_count=900)
paths['config'].write_text('export:\n  width_inches: 10\n  height_inches: 8\n  dpi: 150\n')

def baseline_module(name):
    module = types.ModuleType('phylocloud.'+name)
    module.__package__ = 'phylocloud'
    source = subprocess.check_output(
        ['git','show','cc5beb4:src/phylocloud/'+name+'.py'], text=True)
    exec(compile(source, '<baseline '+name+'>', 'exec'), module.__dict__)
    return module

old_cloud = baseline_module('cloud_layers')
old_render = baseline_module('render')
old_render.add_native_cloud = old_cloud.add_native_cloud
new_draw = cli.draw
reports = {}
for style in ('soft_cloud','cloud'):
    for version, draw in [('before',old_render.draw),('after',new_draw)]:
        cli.draw = draw
        reports[style+'_'+version] = cli.run_plot(
            paths['tree'],paths['metadata'],paths['selected'],paths['config'],
            out/(style+'_'+version),style=style)
    images = [Image.open(out/(style+'_'+v+'.png')).convert('RGB')
              for v in ('before','after')]
    canvas = Image.new('RGB',(sum(i.width for i in images),max(i.height for i in images)+40),'white')
    pen = ImageDraw.Draw(canvas)
    x = 0
    for label, image in zip(('Before','After'),images):
        pen.text((x+20,10),style+' / '+label,fill='black')
        canvas.paste(image,(x,40))
        x += image.width
    canvas.save(out/(style+'_comparison.jpg'),quality=90)
cli.draw = new_draw
for style in ('soft_cloud','cloud'):
    a,b = (reports[style+'_'+v] for v in ('before','after'))
    for key in ('validation','input_sha256','tree_edges','foreground_edges','reference_genomes'):
        assert a[key] == b[key], (style,key)
manifest = {'baseline_commit':'cc5beb4', 'synthetic_seed':47,
            'scientific_before_after_equal':True,
            'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in sorted(out.iterdir()) if p.suffix in ('.png','.svg','.pdf','.jpg')}}
(out/'comparison_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Synthetic exports and matched scientific audits:', out)
