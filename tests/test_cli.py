from phylocloud.cli import run_plot
from phylocloud.synthetic import make_demo


def test_small_end_to_end_render(tmp_path):
    inputs=make_demo(tmp_path/'data',seed=7,reference_count=60)
    out=tmp_path/'figure'/'preview'
    stats=run_plot(inputs['tree'],inputs['metadata'],inputs['selected'],inputs['config'],out)
    assert stats['tips']==69
    assert stats['selected']==9
    assert stats['foreground_edges']>0
    for ext in ('svg','pdf','png'):
        assert out.with_suffix('.'+ext).stat().st_size>2000
    assert '<svg' in out.with_suffix('.svg').read_text()[:1000]
    assert out.with_suffix('.pdf').read_bytes()[:4]==b'%PDF'


def test_svg_is_reproducible_for_same_tree(tmp_path):
    inputs=make_demo(tmp_path/'data',seed=47,reference_count=60)
    a=tmp_path/'a';b=tmp_path/'b'
    run_plot(inputs['tree'],inputs['metadata'],inputs['selected'],inputs['config'],a)
    run_plot(inputs['tree'],inputs['metadata'],inputs['selected'],inputs['config'],b)
    assert a.with_suffix('.svg').read_bytes()==b.with_suffix('.svg').read_bytes()
