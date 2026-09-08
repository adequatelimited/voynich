#!/usr/bin/env python3
"""V-Z1 part 3: the one reading the test agent did NOT take -- CIRCULAR gap
(a ring is a ring). If the ordinal gradient exists but was hidden by the linear
gap convention, it must show up here. Also: circular gap on the numeral
controls, to confirm the convention is not what is killing the signal."""
import json, math, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import meaning_lib as ML

HERE = Path(__file__).resolve().parent
ZL3B = HERE / '..' / '..' / 'data' / 'corpora' / 'ZL3b-n.txt'
MIN_RING = 8


def seq_of_words(words, level='units'):
    out = []
    for w in words:
        out.extend(ML.bpe_apply(w) if level == 'units' else list(w))
    return out


def build(signs, level='units', comma=True):
    pages = ML.parse_pages(str(ZL3B), comma_split=comma)
    by = ML.sign_rings(ML.zodiac_labels(pages, comma_split=comma))
    rings = []
    for s in signs:
        for ring, recs in by.get(s, {}).items():
            if len(recs) >= MIN_RING:
                rings.append([seq_of_words(r['words'], level) for r in recs])
    return rings


def ranks_avg(v):
    n = len(v); idx = sorted(range(n), key=lambda i: v[i]); r = [0.0] * n; i = 0
    while i < n:
        j = i
        while j + 1 < n and v[idx[j + 1]] == v[idx[i]]:
            j += 1
        a = sum(range(i + 1, j + 2)) / float(j - i + 1)
        for k in range(i, j + 1):
            r[idx[k]] = a
        i = j + 1
    return r


def pearson(x, y):
    n = len(x); mx = sum(x) / n; my = sum(y) / n
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    dx = math.sqrt(sum((a - mx) ** 2 for a in x)); dy = math.sqrt(sum((b - my) ** 2 for b in y))
    return num / (dx * dy) if dx > 0 and dy > 0 else 0.0


class R(object):
    def __init__(self, seqs, circular):
        n = self.n = len(seqs)
        self.circ = circular
        S = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                S[i][j] = S[j][i] = ML.lcs_sim(seqs[i], seqs[j])
        self.S = S

    def pairs(self, p):
        n, S = self.n, self.S
        out = []
        for i in range(n):
            for j in range(i + 1, n):
                g = j - i
                if self.circ:
                    g = min(g, n - g)
                out.append((g, S[p[i]][p[j]]))
        return out


def stats(rs, perms):
    g1s, g3s, rhos = [], [], []
    for r, p in zip(rs, perms):
        pr = r.pairs(p)
        g1s += [s for g, s in pr if g == 1]
        g3s += [s for g, s in pr if g >= 3]
        rhos.append(pearson(ranks_avg([g for g, _ in pr]), ranks_avg([s for _, s in pr])))
    return (sum(g1s) / len(g1s) - sum(g3s) / len(g3s), sum(rhos) / len(rhos))


def pc(obs, nulls):
    mu = sum(nulls) / len(nulls)
    d = abs(obs - mu)
    return (1.0 + sum(1 for x in nulls if abs(x - mu) >= d - 1e-12)) / (len(nulls) + 1.0)


def run(rings, circular, nperm=10000, seed=408, tag=''):
    rs = [R(s, circular) for s in rings]
    ident = [list(range(r.n)) for r in rs]
    od, orho = stats(rs, ident)
    rng = random.Random(seed)
    nd, nr = [], []
    for _ in range(nperm):
        pp = []
        for r in rs:
            q = list(range(r.n)); rng.shuffle(q); pp.append(q)
        a, b = stats(rs, pp)
        nd.append(a); nr.append(b)
    mu = sum(nd) / len(nd)
    sd = math.sqrt(sum((x - mu) ** 2 for x in nd) / len(nd))
    print('  %-34s Delta=%+.5f p=%.4f (z=%+.2f)  rho_bar=%+.5f p=%.4f'
          % (tag, od, pc(od, nd), (od - mu) / sd if sd else 0, orho, pc(orho, nr)))
    return od, pc(od, nd), orho, pc(orho, nr)


def cut_cyclic(series, sizes):
    out, k = [], 0
    for sz in sizes:
        out.append([series[(k + i) % len(series)] for i in range(sz)])
        k = (k + sz) % len(series)
    return out


def main():
    print('--- CIRCULAR gap (min(d, n-d)), the reading t_z1 did not take ---')
    for level in ('units', 'chars'):
        for split, signs in (('FIT', ML.FIT_SIGNS), ('TEST', ML.TEST_SIGNS)):
            rings = build(signs, level)
            run(rings, True, tag='%s|%s|circular' % (split, level))
    print('')
    print('--- linear gap, for reference (should match t_z1) ---')
    for split, signs in (('FIT', ML.FIT_SIGNS), ('TEST', ML.TEST_SIGNS)):
        run(build(signs, 'units'), False, tag='%s|units|linear' % split)

    print('')
    print('--- the same circular convention on the numeral controls ---')
    sizes = [len(r) for r in build(ML.TEST_SIGNS)]
    for name, series in ML.numeral_controls().items():
        rings = [[list(w) for w in ring] for ring in cut_cyclic(series, sizes)]
        run(rings, True, nperm=2000, tag='%s|circular' % name)


if __name__ == '__main__':
    main()
