#!/usr/bin/env python3
"""EXPLORATORY, not in PROTOCOL.md: the family's own procedure (habit tables from the
whole corpus, selection and scoring on the whole corpus) applied to the CLEAN target.
Separates the effect of parser cleaning from the effect of held-out scoring.

Usage: python insample_clean.py --repo ../.. --out results/
"""
import argparse, json, sys, random
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import critique_lib as AC   # verbatim copy of experiments/adversarial-critique/adversarial_critique.py (PR #10), kept here so this branch is self-contained
import clean_rerun as CR

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True); ap.add_argument('--out', required=True)
    args = ap.parse_args()
    corpus = Path(args.repo) / 'data/corpora/ZL3b-n.txt'
    out = {}
    for label, comma in (('S', True), ('M', False)):
        pages = AC.clean_load(corpus, comma_split=comma)
        triples = AC.as_triples(pages)
        words = [w for _, _, ws in triples for w in ws]
        real = AC.full_metrics(triples)
        res = {'real_all': real, 'models': {}}
        for name in ('M2', 'M3', 'M4', 'M5', 'M5b'):
            best = None
            for tag, gen in CR.model_grid(name, triples, words):   # tables from ALL words
                m = AC.full_metrics(gen)
                d = CR.composite(real, m)
                if best is None or d < best[0]:
                    best = (d, tag, m)
            d, tag, m = best
            mt = CR.matches(real, m)
            res['models'][name] = {'selected': tag, 'composite': d, 'metrics': m, 'matches': mt,
                                   'match_count': sum(1 for v in mt.values() if v)}
            print(f'[{label} in-sample clean] {name} {tag} composite={d} matches={res["models"][name]["match_count"]}/9', flush=True)
        out[label] = res
    (Path(args.out) / 'insample_clean.json').write_text(json.dumps(out, indent=1))

if __name__ == '__main__':
    main()
