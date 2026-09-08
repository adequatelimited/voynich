#!/usr/bin/env python3
"""Controls extension: entry-structure metrics across real reference genres.

Motivation (contributor question): the manuscript's 30% entry-private vocabulary
is 10x a real scholarly encyclopedia (Culpeper, 2.8%) — but is that just because
Culpeper is dense professional prose? Add two more real controls:
  - Devil's Dictionary (PG 972): a dictionary — shortest real "entries" with a
    headword each, 974 entries parsed at "HEADWORD, pos." lines.
  - The Wonder Book of Knowledge (PG 41111, 1921): a popular/children's
    encyclopedia — ~160 Q&A entries parsed at question-style headings.
Same metric suite and same Voynich corpus as pilots 2-4 for one consistent table.

Usage: python controls_entry.py --corpus ../../data/corpora/ZL3b-n.txt \
  --culpeper ../../data/corpora/pg49513.txt --alice ../../data/corpora/pg11.txt \
  --devil ../../data/corpora/pg972.txt --wonder ../../data/corpora/pg41111.txt \
  --out results/
Stdlib only. Deterministic.
"""
import argparse, json, math, random, re
from collections import Counter
from pathlib import Path

def load_pages(path):
    pages, order = {}, []
    for line in open(path, encoding='utf-8', errors='replace'):
        line = line.rstrip('\n')
        if line.startswith('#') or not line.strip():
            continue
        m = re.match(r'<(f(\d+)[rv]\d*)\.\d+[^>]*>\s*(.*)$', line)
        if not m:
            continue
        page, fnum, text = m.group(1), int(m.group(2)), m.group(3)
        text = re.sub(r'<![^>]*>', '', text)
        text = re.sub(r'\{[^}]*\}', '', text)
        ws = [re.sub(r"[@,;!?'\"<>]", '', w) for w in re.split(r'[.\s]+', text)]
        ws = [w for w in (re.sub(r'\d', '', w) for w in ws) if w]
        if not ws:
            continue
        if page not in pages:
            pages[page] = []
            order.append(page)
        pages[page].extend(ws)
    return [(int(re.match(r'f(\d+)', p).group(1)), p, pages[p]) for p in order]

def pg_body(path):
    t = open(path, encoding='utf-8', errors='replace').read()
    s = t.find('*** START OF'); e = t.find('*** END OF')
    return t[s:e] if s >= 0 and e > s else t

def words_en(text):
    return [w.lower() for w in re.findall(r"[A-Za-z']+", text) if len(w) > 1]

def culpeper_entries(path):
    body = pg_body(path)
    marks = list(re.finditer(r"\n\n\s+([A-Z][A-Z' \-]{2,40})\.\n\n_", body))
    entries = []
    for i, m in enumerate(marks):
        end = marks[i+1].start() if i+1 < len(marks) else len(body)
        entries.append((i, m.group(1).title(), words_en(body[m.end():end])))
    return [(i, n, ws) for i, n, ws in entries if len(ws) >= 40]

def devil_entries(path):
    body = pg_body(path)
    marks = list(re.finditer(r"\n([A-Z][A-Z '\-]{1,40}), (?:n|v|adj|adv|prep|conj)\.", body))
    entries = []
    for i, m in enumerate(marks):
        end = marks[i+1].start() if i+1 < len(marks) else len(body)
        entries.append((i, m.group(1).title(), words_en(body[m.end():end])))
    return [(i, n, ws) for i, n, ws in entries if len(ws) >= 8]

def wonder_entries(path):
    body = pg_body(path)
    marks = list(re.finditer(r"\n\s*([A-Z][^?\n]{10,90}\?)\s*\n", body))
    entries = []
    for i, m in enumerate(marks):
        end = marks[i+1].start() if i+1 < len(marks) else len(body)
        entries.append((i, m.group(1)[:40], words_en(body[m.end():end])))
    return [(i, n, ws) for i, n, ws in entries if len(ws) >= 40]

def alice_chunks(path, chunk=155):
    ws = words_en(pg_body(path))
    return [(i, f'chunk{i}', ws[i*chunk:(i+1)*chunk]) for i in range(len(ws)//chunk)]

def entry_metrics(pages, seed=7):
    words = [w for _, _, ws in pages for w in ws]
    n = len(words); types = len(set(words))
    psets = {pid: set(ws) for _, pid, ws in pages}
    pnums = [f for f, _, _ in pages]
    ids = [pid for _, pid, _ in pages]
    def jac(a, b): return len(a & b) / max(len(a | b), 1)
    adj = [jac(psets[ids[i]], psets[ids[i+1]]) for i in range(len(ids)-1)]
    rng = random.Random(seed)
    far = []
    for i, pid in enumerate(ids):
        cands = [q for j, q in enumerate(ids) if abs(pnums[j]-pnums[i]) > 20]
        if cands: far.append(jac(psets[pid], psets[rng.choice(cands)]))
    df = Counter()
    for pid in ids:
        for w in psets[pid]: df[w] += 1
    uniq = [sum(1 for w in psets[pid] if df[w] == 1)/max(len(psets[pid]),1) for pid in ids]
    lens = [len(ws) for _, _, ws in pages]
    return {
        'entries': len(ids),
        'tokens': n, 'types': types, 'ttr': round(types/n, 4),
        'entry_tokens_mean': round(sum(lens)/max(len(lens),1), 1),
        'jaccard_adjacent': round(sum(adj)/max(len(adj),1), 4),
        'jaccard_distant': round(sum(far)/max(len(far),1), 4) if far else None,
        'entry_unique_share': round(sum(uniq)/max(len(uniq),1), 4),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--corpus', required=True)
    ap.add_argument('--culpeper', required=True)
    ap.add_argument('--alice', required=True)
    ap.add_argument('--devil', required=True)
    ap.add_argument('--wonder', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    out = {
        'voynich': entry_metrics(load_pages(args.corpus)),
        'culpeper_encyclopedia': entry_metrics(culpeper_entries(args.culpeper)),
        'alice_narrative_chunks': entry_metrics(alice_chunks(args.alice)),
        'devils_dictionary': entry_metrics(devil_entries(args.devil)),
        'wonder_book_kids_encyclopedia': entry_metrics(wonder_entries(args.wonder)),
    }
    o = Path(args.out); o.mkdir(parents=True, exist_ok=True)
    (o/'results.json').write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))

if __name__ == '__main__':
    main()
