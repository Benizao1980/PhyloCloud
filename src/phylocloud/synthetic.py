"""Reproducible synthetic fixture; not derived from GTDB or clinical samples."""
from __future__ import annotations
import csv
from pathlib import Path
import random
from Bio.Phylo.Newick import Tree, Clade
from Bio import Phylo

SPECIES=[
 ('Campylobacter infans','INF',210,3),
 ('Campylobacter_D jejuni','JEJ',200,2),
 ('Campylobacter coli','COL',160,1),
 ('Campylobacter upsaliensis','UPS',135,1),
 ('Campylobacter fetus','FET',105,1),
 ('Campylobacter_D sp934718785','SPX',90,1),
]


def make_demo(output_dir: str | Path, seed: int=47, reference_count: int=900):
    """Construct a branching cloud containing 9 focal tips."""
    if reference_count < 60:
        raise ValueError('At least 60 reference tips required for synthetic cloud')
    rng = random.Random(seed)
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    metadata=[];selected=[]

    def grow(labels:list[str],depth:int=0)->Clade:
        if len(labels)==1:
            length = max(.009,rng.lognormvariate(-2.50,.61))
            return Clade(name=labels[0],branch_length=length)
        split=int(round(len(labels)*rng.uniform(.25,.73)))
        split=max(1,min(len(labels)-1,split))
        rng.shuffle(labels)
        a,b=grow(labels[:split],depth+1),grow(labels[split:],depth+1)
        return Clade(branch_length=max(.010,rng.lognormvariate(-2.28+.12*(depth<3),.52)),clades=[a,b])

    clades=[]; counters=0
    total_reference_fraction=sum(s[2] for s in SPECIES)
    refs_assigned=0
    for index,(species,short,weight,nmag) in enumerate(SPECIES):
        nref=(round(reference_count*weight/total_reference_fraction) if index<5
              else reference_count-refs_assigned)
        refs_assigned+=nref
        tip_ids=[]
        for j in range(nref):
            k=f'REF_{short}_{j+1:04d}';tip_ids.append(k)
            metadata.append({'genome_id':k,'species':species,'source':'synthetic reference',
                             'label':k,'group':'reference'})
        for j in range(nmag):
            counters+=1;k=f'MAG_SYN_{counters:02d}';tip_ids.append(k);selected.append(k)
            metadata.append({'genome_id':k,'species':species,'source':'synthetic MAG',
                             'label':f'MAG {counters:02d}  ·  {species.replace("Campylobacter ","C. ")}',
                             'group':'selected'})
        subtree=grow(tip_ids)
        subtree.branch_length=rng.uniform(.48,.98) + (0.28 if index in (1,4) else 0)
        clades.append(subtree)
    tree=Tree(root=Clade(clades=clades),rooted=False)
    treepath=out/'synthetic_tree.nwk'
    Phylo.write(tree,str(treepath),'newick')
    metapath=out/'synthetic_metadata.tsv'
    with metapath.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['genome_id','species','source','label','group'],delimiter='\t')
        writer.writeheader();writer.writerows(metadata)
    selpath=out/'selected_genomes.txt'
    selpath.write_text('\n'.join(selected)+'\n',encoding='utf-8')
    config=out/'config.yml'
    config.write_text('''# Synthetic demonstration; Ben-style species preset (2026-10-12)
layout:
  rotation_degrees: 19
style:
  preset: soft_cloud
  title: "PhyloCloud  /  diversity in context"
  subtitle: "Synthetic illustration  ·  reference phylogeny + highlighted genomes"
  species_background: true
  reference_alpha: 0.23
  foreground_width: 2.05
export:
  width_inches: 14
  height_inches: 11
  dpi: 400
''',encoding='utf-8')
    return {'tree':treepath,'metadata':metapath,'selected':selpath,'config':config,
            'reference_count':refs_assigned,'selected_count':len(selected)}
