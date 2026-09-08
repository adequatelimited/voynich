#!/usr/bin/env python3
"""Multilingual morphology controls: does ANY real language reach the
manuscript's word-ending discipline?

Motivation (contributor question): English barely marks word endings. Inflected
languages (Latin, Russian, Finnish, Greek...) carry case/number morphology —
maybe THEIR final-glyph entropy approaches the manuscript's 2.59 bits, and the
residue is just "a normal morphologically rich language".

Method: the same text (the Bible) in 9 languages (Christodoulopoulos & Steedman
bible-corpus, github.com/christos-c/bible-corpus) — identical content, so all
differences are language differences. Equal 35k-token sample per language
(matches the Voynich corpus size). Metrics: ttr, H1, H2|1, word-final char
entropy, word length.

Usage: python languages_control.py --corpus ../../data/corpora/ZL3b-n.txt \
  --bibles <dir-with-XMLs> --out results/
Stdlib only. Deterministic.
"""
import argparse, json, math, re
from collections import Counter
from pathlib import Path

SAMPLE_TOKENS = 35000

def load_voynich(path):
    words = []
    for line in open(path, encoding='utf-8', errors='replace'):
        m = re.match(r'<f\d+[rv]\d*\.\d+[^>]*>\s*(.*)$', line.rstrip('\n'))
        if not m:
            continue
        text = re.sub(r'<![^>]*>', '', m.group(1))
        text = re.sub(r'\{[^}]*\}', '', text)
        for w in re.split(r'[.\s]+', text):
            w = re.sub(r'\d', '', re.sub(r"[@,;!?'\"<>]", '', w))
            if w:
                words.append(w)
    return words

def load_bible(path):
    t = open(path, encoding='utf-8', errors='replace').read()
    t = re.sub(r'<[^>]+>', ' ', t)
    return re.findall(r"[\w'’\-]+", t, flags=re.UNICODE)

def metrics(words, label):
    n = len(words)
    types = len(set(words))
    text = ' '.join(words)
    h1 = -sum(c/len(text) * math.log2(c/len(text)) for c in Counter(text).values())
    bi = Counter(text[i:i+2] for i in range(len(text)-1))
    nb = sum(bi.values())
    h2 = -sum(c/nb * math.log2(c/nb) for c in bi.values())
    wf = -sum(c/n * math.log2(c/n) for c in Counter(w[-1] for w in words).values())
    return {
        'language': label, 'tokens': n, 'types': types, 'ttr': round(types/n, 4),
        'H1': round(h1, 3), 'H2_given_1': round(h2 - h1, 3),
        'wordfinal_char_H': round(wf, 3),
        'word_len_mean': round(sum(len(w) for w in words)/n, 2),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--corpus', required=True)
    ap.add_argument('--bibles', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    voy = load_voynich(args.corpus)
    out = {'voynich': metrics(voy, 'Voynich (ZL3b)'), 'sample_tokens': SAMPLE_TOKENS,
           'languages': {}}
    for xml in sorted(Path(args.bibles).glob('*.xml')):
        words = load_bible(xml)[:SAMPLE_TOKENS]
        if len(words) < 10000:
            print(f'skip {xml.name}: only {len(words)} tokens')
            continue
        out['languages'][xml.stem] = metrics(words, xml.stem)

    o = Path(args.out); o.mkdir(parents=True, exist_ok=True)
    (o/'results.json').write_text(json.dumps(out, indent=1))
    rows = [('Voynich (ZL3b)', out['voynich'])] + [(k, v) for k, v in out['languages'].items()]
    print(f"{'language':16s} {'types':>6} {'ttr':>6} {'H1':>5} {'H2|1':>5} {'wfH':>5} {'len':>5}")
    for name, m in sorted(rows, key=lambda r: r[1]['wordfinal_char_H']):
        print(f"{name:16s} {m['types']:6d} {m['ttr']:6.3f} {m['H1']:5.2f} {m['H2_given_1']:5.2f} {m['wordfinal_char_H']:5.2f} {m['word_len_mean']:5.2f}")

if __name__ == '__main__':
    main()
