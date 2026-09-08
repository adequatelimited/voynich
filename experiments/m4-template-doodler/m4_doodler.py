#!/usr/bin/env python3
"""M4 template doodler + positive controls.

Two upgrades over pilots 1-2:
1. POSITIVE CONTROLS: real texts measured with the same metric suite.
   - Culpeper's Complete Herbal (PG 49513): a REAL encyclopedia with REAL
     per-herb entries — the direct control for the entry-structure finding.
   - Alice in Wonderland (repo data/corpora/pg11.txt): narrative English control.
2. M4 TEMPLATE MODEL: word generation follows Stolfi's published word grammar
   (Stolfi 2000a, ic.unicamp.br/~stolfi/voynich/00-EXPORT/00-06-07-word-grammar/):
   core {t p k f cth cph ckh cfh}, mantle {ch sh ee}, crust {d l r s n x i m g},
   circles {a o y} as pre-modifiers/final, e attached after core/mantle.
   Density profile of a word must be a single unimodal hill. Layer letter weights
   are estimated from the corpus (slot assignment = published model; weights = data).
   Template words are embedded in the M3 entry engine (topic carry-over, drift,
   preferential reuse); mutations resample one slot.

Usage: python m4_doodler.py --corpus ../../data/corpora/ZL3b-n.txt \
         --alice ../../data/corpora/pg11.txt --culpeper <path>/pg49513.txt --out results/
Stdlib only. Deterministic under --seed.
"""
import argparse, json, math, random, re
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------- parsing ---

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
    return [(i, name, ws) for i, name, ws in entries if len(ws) >= 40]

def alice_chunks(path, chunk=155):
    ws = words_en(pg_body(path))
    return [(i, f'chunk{i}', ws[i*chunk:(i+1)*chunk]) for i in range(len(ws)//chunk)]

# ---------------------------------------------------------------- metrics ---

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

# ------------------------------------------------------- Stolfi template ----

CORE   = ['t','p','k','f','cth','cph','ckh','cfh']
MANTLE = ['ch','sh','ee']
CRUST  = ['d','l','r','s','n','x','i','m','g']
CIRCLES = ['a','o','y']

def layer_weights(corpus_words):
    """Estimate per-layer letter frequencies from corpus by Stolfi assignment."""
    cw, mw, rw, circ_end = Counter(), Counter(), Counter(), Counter()
    for w in corpus_words:
        for L, C in ((CORE, cw), (MANTLE, mw), (CRUST, rw)):
            for g in L:
                if g in w:
                    C[g] += w.count(g)
        if w and w[-1] in CIRCLES:
            circ_end[w[-1]] += 1
    return cw, mw, rw, circ_end

def make_template_word(rng, cw, mw, rw, circ_end, p_circle=0.35, p_final_y=0.40):
    """One Stolfi-grammar word: unimodal density hill, circles as modifiers."""
    def pick(C, pool):
        items = [(g, C.get(g, 1)) for g in pool]
        gs, ws = zip(*items)
        return rng.choices(gs, ws)[0]
    parts = []          # (density, text) in order
    # core (density 3) — maybe empty
    core = pick(cw, CORE) if rng.random() < 0.8 else ''
    if core and rng.random() < 0.35:  # e attaches after core/mantle
        core += 'e'
    # mantle left/right (density 2)
    m_left = pick(mw, MANTLE) if rng.random() < 0.45 else ''
    m_right = pick(mw, MANTLE) if rng.random() < 0.35 else ''
    # crust outer (density 1)
    c_left = pick(rw, CRUST) if rng.random() < 0.35 else ''
    c_right = pick(rw, CRUST) if rng.random() < 0.55 else ''
    seq = [x for x in (c_left, m_left, core, m_right, c_right) if x]
    # circles as pre-modifiers
    out = ''
    for piece in seq:
        if rng.random() < p_circle:
            out += rng.choices(CIRCLES, [3, 4, 1])[0]
        out += piece
    if not out:
        out = 'o'
    # final circle (usually y)
    if rng.random() < p_final_y:
        gs, ws = zip(*circ_end.items())
        out += rng.choices(gs, ws)[0]
    return out

def template_parseable(w):
    """Check: does the word satisfy the unimodal-hill density rule?"""
    dens = []
    i = 0
    while i < len(w):
        g = None
        for pool, d in ((CORE,3),(MANTLE,2),(CRUST,1)):
            for c in sorted(pool, key=len, reverse=True):
                if w.startswith(c, i):
                    g = (d, c); break
            if g: break
        if g:
            dens.append(g[0]); i += len(g[1])
        else:
            i += 1  # circles and e: modifiers, ignored
    if not dens: return True
    peak = dens.index(max(dens))
    return all(dens[j] <= dens[j+1] for j in range(peak)) and \
           all(dens[j] >= dens[j+1] for j in range(peak, len(dens)-1))

# ------------------------------------------------------------------ M4 ------

def gen_m4(pages, corpus_words, seed, carry, topic_size, prime, p_reuse, p_mut):
    rng = random.Random(seed)
    cw, mw, rw, circ_end = layer_weights(corpus_words)
    def tword(): return make_template_word(rng, cw, mw, rw, circ_end)
    def mutate(w):
        # template-aware: regenerate with high overlap by splicing a fresh word's slot
        u = tword()
        if len(w) > 3 and len(u) > 3:
            cut = rng.randrange(1, len(w))
            cut2 = rng.randrange(1, len(u))
            return (w[:cut] + u[cut2:]) if rng.random() < 0.5 else (u[:cut2] + w[cut:])
        return u
    global_types, global_set, out_pages, prev_topic = [], set(), [], []
    for fnum, pid, real_ws in pages:
        recent = global_types[-500:]
        topic = [mutate(t) if rng.random() < 0.3 else t
                 for t in prev_topic if rng.random() < carry]
        while len(topic) < topic_size:
            if recent and rng.random() < 0.8:
                topic.append(mutate(recent[rng.randrange(len(recent))]))
            else:
                topic.append(tword())
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
            elif r < p_reuse + p_mut:
                w = mutate(rng.choice(types_seen))
            else:
                w = tword()
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
    ap.add_argument('--alice', required=True)
    ap.add_argument('--culpeper', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--seed', type=int, default=408)
    args = ap.parse_args()

    pages = load_pages(args.corpus)
    corpus_words = [w for _, _, ws in pages for w in ws]
    real = all_metrics(pages)
    culp = culpeper_entries(args.culpeper)
    alice = alice_chunks(args.alice)
    results = {'corpus_source': args.corpus, 'seed': args.seed,
               'real_voynich': real,
               'control_culpeper': all_metrics(culp),
               'control_alice': all_metrics(alice),
               'controls_meta': {'culpeper_entries': len(culp),
                                 'alice_chunks': len(alice)},
               'models': {}}
    # coverage of the real corpus by the published grammar
    parse_ok = sum(1 for w in set(corpus_words) if template_parseable(w))
    results['stolfi_grammar_coverage_types'] = round(parse_ok / len(set(corpus_words)), 4)

    keys = ['ttr','H1','H2_given_1','zipf_slope','word_len_mean','last_char_H',
            'jaccard_adjacent','jaccard_distant','page_unique_share']
    best = None
    for carry in (0.2, 0.3, 0.5):
        for topic_size in (30, 60):
            for p_reuse in (0.6, 0.7):
                p_mut, prime = 0.1, 2
                gen = gen_m4(pages, corpus_words, args.seed, carry, topic_size, prime, p_reuse, p_mut)
                mm = all_metrics(gen)
                dist = 0.0
                for k in keys:
                    if real[k] is None or mm[k] is None: continue
                    scale = abs(real[k]) or 1.0
                    dist += ((real[k]-mm[k])/scale) ** 2
                dist = round(math.sqrt(dist), 4)
                tag = f'carry={carry},topic={topic_size},reuse={p_reuse}'
                results['models'][f'M4_template[{tag}]'] = mm | {'composite_distance': dist}
                if best is None or dist < best[0]:
                    best = (dist, tag)
    results['best_m4'] = best[1]
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    (out/'results.json').write_text(json.dumps(results, indent=1))
    print(json.dumps({'real_voynich': real,
                      'control_culpeper': results['control_culpeper'],
                      'control_alice': results['control_alice'],
                      'stolfi_coverage': results['stolfi_grammar_coverage_types'],
                      'best_m4': best[1],
                      'best': results['models'][f'M4_template[{best[1]}]']}, indent=1))

if __name__ == '__main__':
    main()
