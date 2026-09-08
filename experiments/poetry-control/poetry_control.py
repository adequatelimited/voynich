#!/usr/bin/env python3
"""Poetry control: line-end discipline in real rhymed verse vs the manuscript.

Motivation: the manuscript's strongest surviving anomaly is word-ending
predictability (final-char entropy 2.59 bits) plus known line-position effects.
Rhymed metrical verse is REAL language with artificially constrained line endings
(rhyme). If verse shows similarly reduced line-final entropy, part of the
manuscript's residue is versification-like discipline, not necessarily content.

Sources:
  - Voynich corpus (real lines from IVTFF loci)
  - Shakespeare's Sonnets (PG 1041): 154 sonnets, strict rhyme — real lines
  - Culpeper herbal + Alice (prose pseudo-lines of the Voynich mean length)

Metrics per source: word-final char entropy (all words), line-final word's
final-char entropy, line-initial word's first-char entropy, top-5 line-final
word share (rhyme concentration).

Usage: python poetry_control.py --corpus ../../data/corpora/ZL3b-n.txt \
  --sonnets ../../data/corpora/pg1041.txt --culpeper ../../data/corpora/pg49513.txt \
  --alice ../../data/corpora/pg11.txt --out results/
Stdlib only. Deterministic.
"""
import argparse, json, math, re
from collections import Counter
from pathlib import Path

ROMAN = re.compile(r'^\s*(X?I{0,3}|IV|V|VI{0,3}|IX|X{1,2})\s*$')

def load_voynich_lines(path):
    lines = []
    for line in open(path, encoding='utf-8', errors='replace'):
        line = line.rstrip('\n')
        m = re.match(r'<f\d+[rv]\d*\.\d+[^>]*>\s*(.*)$', line)
        if not m:
            continue
        text = re.sub(r'<![^>]*>', '', m.group(1))
        text = re.sub(r'\{[^}]*\}', '', text)
        ws = [re.sub(r"[@,;!?'\"<>]", '', w) for w in re.split(r'[.\s]+', text)]
        ws = [w for w in (re.sub(r'\d', '', w) for w in ws) if w]
        if ws:
            lines.append(ws)
    return lines

def load_sonnets(path):
    t = open(path, encoding='utf-8', errors='replace').read()
    s = t.find('*** START OF'); e = t.find('*** END OF')
    t = t[s:e]
    sonnets, cur = [], []
    for raw in t.splitlines():
        if ROMAN.match(raw):
            if cur:
                sonnets.append(cur)
            cur = []
            continue
        ws = [w.lower() for w in re.findall(r"[A-Za-z']+", raw) if len(w) > 1]
        if ws:
            cur.append(ws)
    if cur:
        sonnets.append(cur)
    return sonnets

def words_en(text):
    return [w.lower() for w in re.findall(r"[A-Za-z']+", text) if len(w) > 1]

def pg_words(path):
    t = open(path, encoding='utf-8', errors='replace').read()
    s = t.find('*** START OF'); e = t.find('*** END OF')
    return words_en(t[s:e])

def pseudo_lines(words, n):
    return [words[i:i+n] for i in range(0, len(words)-n, n)]

def ent(vals):
    n = len(vals)
    return -sum(c/n * math.log2(c/n) for c in Counter(vals).values())

def line_metrics(lines, label):
    words = [w for ws in lines for w in ws]
    final_words = [ws[-1] for ws in lines if ws]
    first_words = [ws[0] for ws in lines if ws]
    top5 = Counter(final_words).most_common(5)
    return {
        'source': label,
        'lines': len(lines),
        'tokens': len(words),
        'mean_line_words': round(len(words)/max(len(lines),1), 2),
        'wordfinal_char_H_all': round(ent([w[-1] for w in words]), 3),
        'linefinal_wordfinal_char_H': round(ent([w[-1] for w in final_words]), 3),
        'lineinitial_firstchar_H': round(ent([w[0] for w in first_words]), 3),
        'top5_linefinal_words': [(w, round(c/len(final_words), 3)) for w, c in top5],
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--corpus', required=True)
    ap.add_argument('--sonnets', required=True)
    ap.add_argument('--culpeper', required=True)
    ap.add_argument('--alice', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    voy = load_voynich_lines(args.corpus)
    mean_len = round(sum(len(ws) for ws in voy) / len(voy))
    out = {
        'voynich_real_lines': line_metrics(voy, 'voynich'),
        'sonnets_rhymed_verse': line_metrics([ln for s in load_sonnets(args.sonnets) for ln in s], 'sonnets'),
        'culpeper_pseudo_lines': line_metrics(pseudo_lines(pg_words(args.culpeper), mean_len), 'culpeper'),
        'alice_pseudo_lines': line_metrics(pseudo_lines(pg_words(args.alice), mean_len), 'alice'),
        'note': f'prose pseudo-lines use the Voynich mean line length ({mean_len} words)',
    }
    o = Path(args.out); o.mkdir(parents=True, exist_ok=True)
    (o/'results.json').write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))

if __name__ == '__main__':
    main()
