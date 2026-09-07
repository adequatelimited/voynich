#!/usr/bin/env python3
"""EXPLORATORY, not in PROTOCOL.md: T1b and the positive control with the K most frequent
word types of each corpus removed from every set before similarity is computed
(a symmetric 'function-word' filter that needs no knowledge of the language).
Usage: python exploratory_contentwords.py --repo ../.. --lab <lab> --out results/
"""
import argparse, json, random, sys
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / 'adversarial-critique'))
import adversarial_critique as AC
import discriminating_tests as D

def strip_top(items, K):
    c = Counter()
    for it in items:
        for w in it['all_words']: c[w] += 1
    top = set(w for w, _ in c.most_common(K))
    for it in items:
        it['words'] = set(it['all_words']) - top
    return items

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True); ap.add_argument('--lab', required=True); ap.add_argument('--out', required=True)
    args = ap.parse_args()
    corpus = Path(args.repo) / 'data/corpora/ZL3b-n.txt'
    pages = D.load_annotated(corpus, True)
    entries = AC.culpeper_entries(Path(args.lab) / 'pg49513.txt')
    out = {}
    logs = []
    def log(s): print(s, flush=True); logs.append(s)
    for K in (0, 25, 50, 100, 200):
        voy = [{'id': p['id'], 'fnum': p['fnum'], 'lang': p['meta'].get('L', '?'), 'names': D.name_tokens(p['plant_id'], D.STOP),
                'all_words': D.page_words(p)} for p in pages if p['plant_id'] and p['meta'].get('I') == 'H']
        cul = [{'id': f'{i}:{name}', 'fnum': i, 'lang': 'en', 'names': D.name_tokens(name, D.STOP_CULP),
                'all_words': AC.letters_only(ws)} for i, name, ws in entries]
        r_voy = D.similarity_test(strip_top(voy, K), random.Random(D.SEED), log, f'T1b top{K} removed')
        r_cul = D.similarity_test(strip_top(cul, K), random.Random(D.SEED), log, f'control top{K} removed')
        out[K] = {'voynich': {k: v for k, v in r_voy.items() if k not in ('similar_pairs', 'name_tokens')},
                  'control': {k: v for k, v in r_cul.items() if k not in ('similar_pairs', 'name_tokens')}}
    (Path(args.out) / 'exploratory_contentwords.json').write_text(json.dumps(out, indent=1), encoding='utf-8')

if __name__ == '__main__':
    main()
