#!/usr/bin/env python3
"""Entry-based doodler (M3): can a content-free process structured as an
illustrated encyclopedia reproduce the Voynich fingerprint?

Hypothesis under test (V. Gnuchev): the manuscript is not continuous prose but
a compilation of per-page entries, each tied to its illustration. M3 therefore
generates PER PAGE: each page gets a small invented "topic vocabulary", topic
words drift/mutate between adjacent pages, and within a page words are drawn
with preferential (Simon-style) reuse plus occasional mutation. No lexicon,
no meaning anywhere.

Corpus: data/corpora/ZL3b-n.txt (repo-pinned). Page structure (folios, token
counts per page) is taken from the real manuscript layout.

Usage: python entry_doodler.py --corpus ../../data/corpora/ZL3b-n.txt --out results/
Stdlib only. Deterministic under --seed.
"""
import argparse, json, math, random, re
from collections import Counter
from pathlib import Path

# ------------------------------------------------------------- corpus -------

def load_pages(path):
    """IVTFF -> ordered list of (folio_int, page_id, [words])."""
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
    return [(re.match(r'f(\d+)', p).group(1) and int(re.match(r'f(\d+)', p).group(1)), p, pages[p]) for p in order]

# ------------------------------------------------------------- metrics ------

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
    xs = [math.log10(r) for r, f in enumerate(freqs, 1) if 10 <= r <= 1000 and f > 0]
    ys = [math.log10(f) for r, f in enumerate(freqs, 1) if 10 <= r <= 1000 and f > 0]
    if len(xs) < 10: return None
    mx, my = sum(xs)/len(xs), sum(ys)/len(ys)
    den = sum((x-mx)**2 for x in xs)
    return sum((x-mx)*(y-my) for x, y in zip(xs, ys)) / den

def page_metrics(pages):
    """pages: list of (fnum, pid, [words]) in order."""
    words = [w for _, _, ws in pages for w in ws]
    n = len(words); types = len(set(words))
    lens = [len(w) for w in words]
    h1, h2c = char_stats(words)
    first_h = -sum(c/n * math.log2(c/n) for c in Counter(w[0] for w in words).values())
    last_h = -sum(c/n * math.log2(c/n) for c in Counter(w[-1] for w in words).values())
    psets = {pid: set(ws) for _, pid, ws in pages}
    pnums = [f for f, _, _ in pages]
    def jac(a, b): return len(a & b) / max(len(a | b), 1)
    adj, far = [], []
    ids = [pid for _, pid, _ in pages]
    for i in range(len(ids)-1):
        adj.append(jac(psets[ids[i]], psets[ids[i+1]]))
    rng = random.Random(7)
    for i, pid in enumerate(ids):
        cands = [q for j, q in enumerate(ids) if abs(pnums[j]-pnums[i]) > 20]
        if cands:
            far.append(jac(psets[pid], psets[rng.choice(cands)]))
    df = Counter()
    for pid in ids:
        for w in psets[pid]:
            df[w] += 1
    uniq = [sum(1 for w in psets[pid] if df[w] == 1)/max(len(psets[pid]),1) for pid in ids]
    return {
        'tokens': n, 'types': types, 'ttr': round(types/n, 4),
        'H1': round(h1, 3), 'H2_given_1': round(h2c, 3),
        'zipf_slope': round(zipf_slope(words), 3) if zipf_slope(words) else None,
        'word_len_mean': round(sum(lens)/len(lens), 2),
        'first_char_H': round(first_h, 3), 'last_char_H': round(last_h, 3),
        'jaccard_adjacent': round(sum(adj)/max(len(adj),1), 4),
        'jaccard_distant': round(sum(far)/max(len(far),1), 4),
        'page_unique_share': round(sum(uniq)/max(len(uniq),1), 4),
    }

# ------------------------------------------------------------- M3 model -----

def build_habit(corpus_words):
    starts = Counter(w[0] for w in corpus_words)
    trans = {}
    for w in corpus_words:
        for a, b in zip(w, w[1:] + ' '):
            trans.setdefault(a, Counter())[b] += 1
    lens = [len(w) for w in corpus_words]
    return starts, trans, lens, sorted(starts)

def gen_m3(pages, corpus_words, seed, drift, topic_size, p_reuse, p_mut, prime, carry):
    rng = random.Random(seed)
    starts, trans, lens, alpha = build_habit(corpus_words)
    global_types_set = set()

    def habit_word():
        w = rng.choices(alpha, [starts[c] for c in alpha])[0]
        target = rng.choice(lens)
        while len(w) < target:
            opts = trans.get(w[-1])
            if not opts: break
            chars, counts = zip(*opts.items())
            c = rng.choices(chars, counts)[0]
            if c == ' ': break
            w += c
        return w or 'a'

    def mutate(w):
        if len(w) < 3: return w
        i = rng.randrange(len(w))
        opts = trans.get(w[i-1]) if i > 0 else starts
        cands = [(c, n) for c, n in opts.items() if c != ' '] if opts else []
        if cands and rng.random() < 0.6:
            chars, counts = zip(*cands)
            return w[:i] + rng.choices(chars, counts)[0] + w[i+1:]
        return w[:i] + w[i+1:]  # delete

    global_types = []          # every type invented so far (manuscript-level vocabulary)
    out_pages = []
    prev_topic = []
    for fnum, pid, real_ws in pages:
        # page topic: carry over part of the previous page's topic (with drift),
        # fill the rest with mutations of recent global types or fresh inventions
        recent = global_types[-500:] if global_types else []
        topic = []
        for t in prev_topic:
            if rng.random() < carry:
                topic.append(mutate(t) if rng.random() < drift else t)
        while len(topic) < topic_size:
            if recent and rng.random() < 0.8:
                base = recent[rng.randrange(len(recent))]
                topic.append(mutate(base) if rng.random() < drift + 0.3 else base)
            else:
                topic.append(habit_word())
        prev_topic = list(topic)
        counts = Counter()
        types_seen = []
        for t in topic:                       # topic priming
            counts[t] += prime
            types_seen.append(t)
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
            elif r < p_reuse + p_mut:
                w = mutate(rng.choice(types_seen))
            else:
                w = habit_word()               # brand-new invention
            ws.append(w)
            if w not in counts: types_seen.append(w)
            counts[w] += 1
        for t in types_seen:
            if t not in global_types_set:
                global_types.append(t)
                global_types_set.add(t)
        out_pages.append((fnum, pid, ws))
    return out_pages

# ------------------------------------------------------------- main ---------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--corpus', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--seed', type=int, default=408)
    args = ap.parse_args()

    pages = load_pages(args.corpus)
    corpus_words = [w for _, _, ws in pages for w in ws]
    real = page_metrics(pages)
    results = {'corpus_source': args.corpus, 'seed': args.seed,
               'real': real, 'models': {}}

    keys = ['ttr','H1','H2_given_1','zipf_slope','word_len_mean','first_char_H',
            'last_char_H','jaccard_adjacent','jaccard_distant','page_unique_share']
    best = None
    for carry in (0.3, 0.5, 0.7):
        for topic_size in (30, 60):
            for prime in (2, 5):
                for p_reuse in (0.6, 0.7):
                    p_mut = 0.1
                    drift = 0.3
                    gen = gen_m3(pages, corpus_words, args.seed, drift, topic_size, p_reuse, p_mut, prime, carry)
                    mm = page_metrics(gen)
                    dist = 0.0
                    for k in keys:
                        if real[k] is None or mm[k] is None: continue
                        scale = abs(real[k]) or 1.0
                        dist += ((real[k]-mm[k])/scale) ** 2
                    dist = round(math.sqrt(dist), 4)
                    tag = f'carry={carry},topic={topic_size},prime={prime},reuse={p_reuse}'
                    results['models'][f'M3_entry[{tag}]'] = mm | {'composite_distance': dist}
                    if best is None or dist < best[0]:
                        best = (dist, tag)
    results['best_m3'] = best[1]
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    (out/'results.json').write_text(json.dumps(results, indent=1))
    print(json.dumps({'real': real, 'best_m3': best[1],
                      'best': results['models'][f'M3_entry[{best[1]}]']}, indent=1))

if __name__ == '__main__':
    main()
