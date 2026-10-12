# Contributing

Contributions are welcome via pull requests. Rendering changes must include an explanation of the biological/scientific interpretation and a before/after synthetic preview.

Run tests and a synthetic example:

```bash
pip install -e '.[test]'
pytest -q
phylocloud demo --outdir outputs/preview --seed 47 --references 900
```

Review invariants: tree topology unchanged; branch lengths unchanged; selected foreground edges are exact original branches; output PDFs/SVGs have editable vector lines and legible labels.

Do not commit confidential metadata or unreleased GETcampy trees. Use generated artificial data in examples. We follow semantic version numbers, with alpha versions and draft GitHub releases while the visual design is under review.
