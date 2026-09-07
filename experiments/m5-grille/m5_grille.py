#!/usr/bin/env python3
"""M5: weighted table-and-grille generator (Rugg 2004 / Zandbergen 2021 mechanism).

The Cardan-grille hypothesis: the scribe had a table of word fragments in three
columns and a grille with three holes; each word = left + middle + right fragment
(some empty). Zandbergen (2021) showed a table+grille can reproduce a real page
(f9v) exactly. We ask the statistical question: does a corpus-derived weighted
table reproduce the corpus' global + page-level fingerprint — in particular the
residuals every previous doodler missed (H2|1, final-char entropy, Zipf slope)?

Construction (documented, no hand tuning):
  - Parse every corpus word into (left, core, right) via Stolfi (2000a) layers:
    locate the core letter (core {t p k f cth cph ckh cfh}, else mantle, else
    first letter); left = everything before it, right = everything after.
  - Table columns = the K most frequent left/core/right fragments, with their
    corpus frequencies as weights (the "weighted table").
  - Word = one draw from each column, concatenated. Embedded in the entry engine
    from pilot 2 (topic carry-over + preferential reuse + occasional fresh draw).

Usage: python m5_grille.py --corpus ../../data/corpora/ZL3b-n.txt --out results/
Stdlib only. Deterministic under --seed.
"""
import argparse, json, math, random, re
from collections import Counter
from pathlib import Path

CORE   = ['cth','cph','ckh','cfh','t','p','k','f']
MANTLE = ['ch','sh','ee']

def split_word(w):
    """Stolfi-layer parse -> (left, core, right)."""
    for pool in (CORE, MANTLE):
        best = None
        for g in pool:
            i = w.find(g)
            if i >= 0 and (best is None or i < best[0]):
                best = (i, g)
        if best:
            i, g = best
            return w[:i], g, w[i+len(g):]
    if w:
        return '', w[0], w[1:]
    return '', '', ''

def build_table(corpus_words, K):
    left, core, right = Counter(), Counter(), Counter()
    for w in corpus_words:
        l, c, r = split_word(w)
        left[l] += 1; core[c] += 1; right[r] += 1
    def topk(C):
        items = C.most_common(K)
        return [g for g, _ in items], [n for _, n in items]
    return topk(left), topk(core), topk(right)

# ---------------------------------------------------------------- metrics ---
# (same suite as pilots 2-3)

def char_stats(words):
    text = ' '.join(words)
    n = len(text)
    h1 = -sum(c/n * math.log2(c/n) for c in Counter(text).values())
    bi = Counter(text[i:i+2] for i in range(len(text)-1))
    nb = sum(bi.values())
    h2 = -sum(c/nb * math.log2(c/nb) for c in bi.values())
    return h1, h2 - h1

def zipf_slope(words):
    freqs = sorted(Counter(words).values(), reverse=True)
    pts = [(r, f) for r, f in enumerate(freqs, 1) if 10 <= r <= 1000 and f > 0]
    if len(pts) < 10: return None
    xs = [math.log10(r) for r, _ in pts]; ys = [math.log10(f) for _, f in pts]
    mx, my = sum(xs)/len(xs), sum(ys)/len(ys)
    den = sum((x-mx)**2 for x in xs)
    return sum((x-mx)*(y-my) for x, y in zip(xs, ys)) / den

def all_metrics(pages, seed=7):
    words = [w for _, _, ws in pages for w in ws]
    n = len(words); types = len(set(words))
    lens = [len(w) for w in words]
    h1, h2c = char_stats(words)
    last_h = -sum(c/n * math.log2(c/n) for c in Counter(w[-1] for w in words).values())
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
    return {
        'tokens': n, 'types': types, 'ttr': round(types/n, 4),
        'H1': round(h1, 3), 'H2_given_1': round(h2c, 3),
        'zipf_slope': round(zipf_slope(words), 3) if zipf_slope(words) else None,
        'word_len_mean': round(sum(lens)/len(lens), 2),
        'last_char_H': round(last_h, 3),
        'jaccard_adjacent': round(sum(adj)/max(len(adj),1), 4),
        'jaccard_distant': round(sum(far)/max(len(far),1), 4) if far else None,
        'page_unique_share': round(sum(uniq)/max(len(uniq),1), 4),
    }

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

# ------------------------------------------------------------------ M5 ------

def gen_m5(pages, table, seed, carry, p_reuse, p_swap, topic_size=60, prime=2):
    """Grille words inside the entry engine. 'Grille swap' = resample a random
    fragment of a recent word (Zandbergen: swapping grilles drives variety)."""
    rng = random.Random(seed)
    (Lg, Lw), (Cg, Cw), (Rg, Rw) = table
    def grille_word():
        return rng.choices(Lg, Lw)[0] + rng.choices(Cg, Cw)[0] + rng.choices(Rg, Rw)[0]
    def resample_fragment(w):
        # replace one third of the word with a fresh column draw
        third = max(1, len(w)//3)
        i = rng.randrange(0, len(w), third) if len(w) > third else 0
        frag = rng.choice((rng.choices(Lg, Lw)[0], rng.choices(Cg, Cw)[0], rng.choices(Rg, Rw)[0]))
        out = w[:i] + frag + w[i+third:]
        return out if out else w
    global_types, global_set, out_pages, prev_topic = [], set(), [], []
    for fnum, pid, real_ws in pages:
        recent = global_types[-500:]
        topic = [resample_fragment(t) if rng.random() < 0.3 else t
                 for t in prev_topic if rng.random() < carry]
        while len(topic) < topic_size:
            if recent and rng.random() < 0.8:
                topic.append(resample_fragment(recent[rng.randrange(len(recent))]))
            else:
                topic.append(grille_word())
        prev_topic = list(topic)
        counts = Counter(topic * prime)
        types_seen = list(dict.fromkeys(topic))
        ws = []
        for _ in range(len(real_ws)):
            r = rng.random()
            if r < p_reuse:
                bag = list(counts.items())
                tot = sum(c for _, c in bag)
                x = rng.randrange(tot); acc = 0; w = bag[-1][0]
                for t, c in bag:
                    acc += c
                    if acc > x: w = t; break
            elif r < p_reuse + p_swap:
                w = resample_fragment(rng.choice(types_seen))
            else:
                w = grille_word()
            ws.append(w)
            if w not in counts: types_seen.append(w)
            counts[w] += 1
        for t in types_seen:
            if t not in global_set:
                global_set.add(t); global_types.append(t)
        out_pages.append((fnum, pid, ws))
    return out_pages

def build_rows(corpus_words, K):
    """Zandbergen's actual device: ROWS of (left, core, right) triples from real
    words, frequency-ordered. A grille = fixed vertical offsets (o1, o2): word =
    left[r] + core[r+o1] + right[r+o2]. Offsets are what makes holes sit at
    different heights; 'swapping grilles' = changing offsets."""
    rows = Counter()
    for w in corpus_words:
        rows[split_word(w)] += 1
    common = rows.most_common(K)
    return [list(t) for t, _ in common], [n for _, n in common]

def gen_m5b(pages, rows_packed, seed, carry, p_reuse, p_swap, o1, o2, topic_size=60, prime=2):
    rng = random.Random(seed)
    rows, wts = rows_packed
    L = [r[0] for r in rows]; C = [r[1] for r in rows]; R = [r[2] for r in rows]
    N = len(rows)
    def grille_word():
        r = rng.choices(range(N), wts)[0]
        return L[r] + C[(r + o1) % N] + R[(r + o2) % N]
    def resample_fragment(w):
        third = max(1, len(w)//3)
        i = rng.randrange(0, len(w), third) if len(w) > third else 0
        r = rng.choices(range(N), wts)[0]
        frag = rng.choice((L[r], C[r], R[r]))
        out = w[:i] + frag + w[i+third:]
        return out if out else w
    global_types, global_set, out_pages, prev_topic = [], set(), [], []
    for fnum, pid, real_ws in pages:
        recent = global_types[-500:]
        topic = [resample_fragment(t) if rng.random() < 0.3 else t
                 for t in prev_topic if rng.random() < carry]
        while len(topic) < topic_size:
            if recent and rng.random() < 0.8:
                topic.append(resample_fragment(recent[rng.randrange(len(recent))]))
            else:
                topic.append(grille_word())
        prev_topic = list(topic)
        counts = Counter(topic * prime)
        types_seen = list(dict.fromkeys(topic))
        ws = []
        for _ in range(len(real_ws)):
            r = rng.random()
            if r < p_reuse:
                bag = list(counts.items())
                tot = sum(c for _, c in bag)
                x = rng.randrange(tot); acc = 0; w = bag[-1][0]
                for t, c in bag:
                    acc += c
                    if acc > x: w = t; break
            elif r < p_reuse + p_swap:
                w = resample_fragment(rng.choice(types_seen))
            else:
                w = grille_word()
            ws.append(w)
            if w not in counts: types_seen.append(w)
            counts[w] += 1
        for t in types_seen:
            if t not in global_set:
                global_set.add(t); global_types.append(t)
        out_pages.append((fnum, pid, ws))
    return out_pages

# ------------------------------------------------------------------ main ----

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--corpus', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--seed', type=int, default=408)
    args = ap.parse_args()

    pages = load_pages(args.corpus)
    corpus_words = [w for _, _, ws in pages for w in ws]
    real = all_metrics(pages)
    results = {'corpus_source': args.corpus, 'seed': args.seed,
               'real_voynich': real, 'models': {}, 'multiseed': {}}

    keys = ['ttr','H1','H2_given_1','zipf_slope','word_len_mean','last_char_H',
            'jaccard_adjacent','jaccard_distant','page_unique_share']
    best = None
    for K in (40, 80, 120):
        table = build_table(corpus_words, K)
        for carry in (0.3, 0.5):
            for p_reuse in (0.6, 0.7):
                p_swap = 0.1
                gen = gen_m5(pages, table, args.seed, carry, p_reuse, p_swap)
                mm = all_metrics(gen)
                dist = 0.0
                for k in keys:
                    if real[k] is None or mm[k] is None: continue
                    scale = abs(real[k]) or 1.0
                    dist += ((real[k]-mm[k])/scale) ** 2
                dist = round(math.sqrt(dist), 4)
                tag = f'K={K},carry={carry},reuse={p_reuse}'
                results['models'][f'M5_grille[{tag}]'] = mm | {'composite_distance': dist}
                if best is None or dist < best[0]:
                    best = (dist, f'M5_grille[{tag}]', K, carry, p_reuse)
    # M5b: row-coupled grille (faithful device: holes at fixed offsets)
    for K in (1000, 3000):
        rows = build_rows(corpus_words, K)
        for (o1, o2) in ((0,0),(1,0),(0,2),(2,5)):
            for p_reuse in (0.6, 0.7):
                gen = gen_m5b(pages, rows, args.seed, 0.3, p_reuse, 0.1, o1, o2)
                mm = all_metrics(gen)
                dist = 0.0
                for k in keys:
                    if real[k] is None or mm[k] is None: continue
                    scale = abs(real[k]) or 1.0
                    dist += ((real[k]-mm[k])/scale) ** 2
                dist = round(math.sqrt(dist), 4)
                tag = f'K={K},o=({o1},{o2}),reuse={p_reuse}'
                results['models'][f'M5b_rowgrille[{tag}]'] = mm | {'composite_distance': dist}
                if best is None or dist < best[0]:
                    best = (dist, f'M5b_rowgrille[{tag}]', None, None, None)
    results['best_m5'] = best[1]

    # multi-seed stability for the best configuration
    mtag = best[1]
    m = re.match(r'(M5b_rowgrille|M5_grille)\[(.+)\]', mtag)
    ms = []
    for s in (101, 202, 303):
        if m.group(1) == 'M5b_rowgrille':
            pm = re.match(r'K=(\d+),o=\((\d+),(\d+)\),reuse=([\d.]+)', m.group(2))
            K, o1, o2, pr = int(pm.group(1)), int(pm.group(2)), int(pm.group(3)), float(pm.group(4))
            rows = build_rows(corpus_words, K)
            mm = all_metrics(gen_m5b(pages, rows, s, 0.3, pr, 0.1, o1, o2), seed=7)
        else:
            params = dict(kv.split('=') for kv in m.group(2).split(','))
            table = build_table(corpus_words, int(params['K']))
            mm = all_metrics(gen_m5(pages, table, s, float(params['carry']), float(params['reuse']), 0.1), seed=7)
        ms.append(mm)
    agg = {}
    for k in keys:
        vals = [m2[k] for m2 in ms if m2[k] is not None]
        if vals:
            mean = sum(vals)/len(vals)
            sd = math.sqrt(sum((v-mean)**2 for v in vals)/len(vals))
            agg[k] = {'mean': round(mean, 4), 'sd': round(sd, 4)}
    results['multiseed'] = {'config': mtag, 'seeds': [101, 202, 303], 'stats': agg}

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    (out/'results.json').write_text(json.dumps(results, indent=1))
    print(json.dumps({'real_voynich': real, 'best_m5': best[1],
                      'best': results['models'][best[1]],
                      'multiseed': results['multiseed']['stats']}, indent=1))

if __name__ == '__main__':
    main()
