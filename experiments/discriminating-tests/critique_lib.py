#!/usr/bin/env python3
"""Adversarial critique of the generative-falsification family (PRs #3-#9).

Implements PROTOCOL.md exactly. Five blocks, each aimed at damaging a named claim:
  A0 parser-contamination audit          (all headline numbers)
  A1 transcription-alphabet confound      ("no language approaches H2|1 / final-glyph H")
  A2 cipher advocate on real texts        ("residue = device")
  A3 structure claims vs nulls/confounds  ("encyclopedia structure confirmed", "30% private")
  A4 medieval-orthography control         ("richest vocabulary, odd for language")

Usage:
  python adversarial_critique.py --repo ../.. --lab R:/Coding/LinearA/tmp/voynich_lab --out results/
Stdlib only. Deterministic (seeds 408 / 7, the family's constants).
"""
import argparse, hashlib, json, math, random, re, statistics
from collections import Counter, OrderedDict
from pathlib import Path

SAMPLE = 35000
SEED_HOMOPHONE = 408
SEED_DISTANT = 7
N_PERM = 200
DET_P = 0.90       # determinism-merge conditional-probability threshold (PROTOCOL A1)
DET_MINFRAC = 0.001

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

# =========================================================== family parser ===
# Verbatim semantics of load_pages() in m4_doodler.py / m5_grille.py / controls_entry.py.

def family_load_pages(path):
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

# ============================================================ clean parser ===

HDR = re.compile(r'^<(f\d+[rv]\d*)>\s*<!([^>]*)>')
LOC = re.compile(r'^<(f(\d+)[rv]\d*)\.(\d+),([^>]*)>\s*(.*)$')

def clean_tokens(text, comma_split=True):
    text = re.sub(r'\{[^}]*\}', '', text)
    text = text.replace('<->', ' ')                      # gap marker = word boundary
    text = re.sub(r'<[^>]*>', '', text)                  # every other tag
    text = re.sub(r'\[([^\]:]*):[^\]]*\]', r'\1', text)  # [a:b] -> a (preferred reading)
    if comma_split:
        parts = re.split(r'[.\s,]+', text)
    else:
        parts = re.split(r'[.\s]+', text.replace(',', ''))
    out = []
    for w in parts:
        if not w or re.search(r'[?@\d]', w):             # illegible / extended glyph: drop token
            continue
        if re.fullmatch(r'[a-z]+', w):
            out.append(w)
    return out

def clean_load(path, comma_split=True, loci_filter=None):
    pages = OrderedDict()
    def get(pid):
        if pid not in pages:
            pages[pid] = {'id': pid, 'fnum': int(re.match(r'f(\d+)', pid).group(1)),
                          'meta': {}, 'words': [], 'loci': []}
        return pages[pid]
    for line in open(path, encoding='utf-8', errors='replace'):
        line = line.rstrip('\n')
        if line.startswith('#'):
            continue
        m = HDR.match(line)
        if m:
            get(m.group(1))['meta'] = dict(re.findall(r'\$([A-Z])=(\S+)', m.group(2)))
            continue
        m = LOC.match(line)
        if not m:
            continue
        pid, code, text = m.group(1), m.group(4), m.group(5)
        ltype = code[1] if len(code) > 1 else '?'
        if loci_filter and ltype not in loci_filter:
            continue
        ws = clean_tokens(text, comma_split)
        if ws:
            p = get(pid); p['words'].extend(ws); p['loci'].append((ltype, ws))
    return [p for p in pages.values() if p['words']]

def as_triples(pages):
    return [(p['fnum'], p['id'], p['words']) for p in pages]

# ================================================================= controls ===

def pg_body(path):
    t = open(path, encoding='utf-8', errors='replace').read()
    s = t.find('*** START OF'); e = t.find('*** END OF')
    return t[s:e] if s >= 0 and e > s else t

def words_en(text, min_len=2):
    text = text.replace('\u2019', "'")
    return [w.lower() for w in re.findall(r"[A-Za-z']+", text) if len(w) >= min_len]

def letters_only(words):
    """Keep Unicode letters only (Cyrillic and Greek included), lowercase; drop
    digits, apostrophes, hyphens. For Latin-script text this equals [a-z]+ plus
    accented letters."""
    out = []
    for w in words:
        w = re.sub(r'[\W\d_]', '', w.lower())
        if w:
            out.append(w)
    return out

def culpeper_entries(path):
    body = pg_body(path)
    marks = list(re.finditer(r"\n\n\s+([A-Z][A-Z' \-]{2,40})\.\n\n_", body))
    entries = []
    for i, m in enumerate(marks):
        end = marks[i+1].start() if i+1 < len(marks) else len(body)
        entries.append((i, m.group(1).title(), words_en(body[m.end():end])))
    return [(i, n, ws) for i, n, ws in entries if len(ws) >= 40]

def alice_chunks(path, chunk=155):
    ws = words_en(pg_body(path))
    return [(i, f'chunk{i}', ws[i*chunk:(i+1)*chunk]) for i in range(len(ws)//chunk)]

def load_bible(path):
    t = open(path, encoding='utf-8', errors='replace').read()
    t = re.sub(r'<[^>]+>', ' ', t)
    return re.findall(r"[\w'\u2019\-]+", t, flags=re.UNICODE)

SIGLA = re.compile(r'\b(E|Hn|Hl|Pt|Ln|Cm|Cp|Dd|Sl|Gg|Ha|Lt|Tr|T)\.')

def chaucer_skeat(path):
    t = open(path, encoding='utf-8', errors='replace').read()
    s = t.find('Whan that Aprille'); e = t.find('END OF VOL')
    lines = []
    for ln in t[s:e].split('\n'):
        if not ln.strip():
            continue
        lead = len(ln) - len(ln.lstrip(' '))
        if lead >= 4 and ('_' in ln or SIGLA.search(ln) or re.match(r'\s+\d+\.', ln)):
            continue                                   # textual-note block
        if re.fullmatch(r"\s*[A-Z][A-Z0-9 .,;:'\-\u2018\u2019]+\s*", ln):
            continue                                   # all-caps heading
        ln = re.sub(r'\[[^\]]*\]', '', ln)             # [2: T. 23-58.]
        ln = re.sub(r'\(\d+\)', '', ln)                # (640)
        ln = re.sub(r'\s+\d+\s*$', '', ln)             # trailing line number
        ln = ln.replace('_', ' ')
        lines.append(ln)
    return '\n'.join(lines)

def chaucer_purves(path):
    t = open(path, encoding='utf-8', errors='replace').read()
    s = t.find('WHEN that Aprilis'); e = t.find('*** END OF')
    lines, in_notes = [], False
    for ln in t[s:e].split('\n'):
        if not ln.strip():
            continue
        if re.match(r'\s*Notes to ', ln):              # editorial note block starts
            in_notes = True
            continue
        if re.fullmatch(r"\s*[A-Z][A-Z0-9 .,;:'\-\u2018\u2019<>]+\s*", ln):
            if re.match(r"\s*THE [A-Z\u2019' ]+(TALE|PROLOGUE)", ln):
                in_notes = False                       # next tale heading ends the notes
            continue
        if in_notes:
            continue
        ln = re.sub(r'<\d+>', '', ln)                  # footnote markers
        ln = re.sub(r'\s{2,}\*.*$', '', ln)            # right-margin gloss
        ln = ln.replace('*', '')
        lines.append(ln)
    return '\n'.join(lines)

# ================================================================== metrics ===

def H(counter):
    n = sum(counter.values())
    return -sum(c/n * math.log2(c/n) for c in counter.values()) if n else 0.0

def seq_of(sym_words):
    seq = []
    for w in sym_words:
        seq.extend(w); seq.append(' ')
    return seq[:-1]

def seq_stats(sym_words):
    """H1 and H2|1 over the space-joined symbol sequence (family formula when
    symbols are characters)."""
    seq = seq_of(sym_words)
    h1 = H(Counter(seq))
    h2 = H(Counter(zip(seq, seq[1:])))
    return h1, h2 - h1

def zipf_slope(words):
    freqs = sorted(Counter(words).values(), reverse=True)
    pts = [(r, f) for r, f in enumerate(freqs, 1) if 10 <= r <= 1000 and f > 0]
    if len(pts) < 10:
        return None
    xs = [math.log10(r) for r, _ in pts]; ys = [math.log10(f) for _, f in pts]
    mx, my = sum(xs)/len(xs), sum(ys)/len(ys)
    den = sum((x-mx)**2 for x in xs)
    return sum((x-mx)*(y-my) for x, y in zip(xs, ys)) / den

def core_metrics(words):
    n = len(words); c = Counter(words); types = len(c)
    h1, h2c = seq_stats(words)
    z = zipf_slope(words)
    return {
        'tokens': n, 'types': types, 'ttr': round(types/n, 4),
        'hapax_share_of_types': round(sum(1 for v in c.values() if v == 1)/types, 4),
        'H1': round(h1, 3), 'H2_given_1': round(h2c, 3),
        'first_char_H': round(H(Counter(w[0] for w in words)), 3),
        'last_char_H': round(H(Counter(w[-1] for w in words)), 3),
        'zipf_slope': round(z, 3) if z is not None else None,
        'word_len_mean': round(sum(len(w) for w in words)/n, 2),
    }

def page_metrics(triples, seed=SEED_DISTANT, far_dist=20):
    psets = {pid: set(ws) for _, pid, ws in triples}
    pnums = [f for f, _, _ in triples]; ids = [pid for _, pid, _ in triples]
    def jac(a, b): return len(a & b) / max(len(a | b), 1)
    adj = [jac(psets[ids[i]], psets[ids[i+1]]) for i in range(len(ids)-1)]
    rng = random.Random(seed); far = []
    for i, pid in enumerate(ids):
        cands = [q for j, q in enumerate(ids) if abs(pnums[j]-pnums[i]) > far_dist]
        if cands:
            far.append(jac(psets[pid], psets[rng.choice(cands)]))
    df = Counter()
    for pid in ids:
        for w in psets[pid]:
            df[w] += 1
    uniq = [sum(1 for w in psets[pid] if df[w] == 1)/max(len(psets[pid]), 1) for pid in ids]
    return {
        'pages': len(ids),
        'jaccard_adjacent': round(sum(adj)/max(len(adj), 1), 4),
        'jaccard_distant': round(sum(far)/max(len(far), 1), 4) if far else None,
        'page_unique_share': round(sum(uniq)/max(len(uniq), 1), 4),
    }

def full_metrics(triples):
    words = [w for _, _, ws in triples for w in ws]
    return core_metrics(words) | page_metrics(triples)

def truncate_triples(triples, n_tokens):
    out, acc = [], 0
    for f, pid, ws in triples:
        if acc >= n_tokens:
            break
        take = ws[:n_tokens-acc]
        out.append((f, pid, take)); acc += len(take)
    return out

# ======================================================= alphabet transforms ===

LEVEL_B = ['cth', 'ckh', 'cph', 'cfh', 'ch', 'sh']
LEVEL_C = LEVEL_B + ['iiin', 'iin', 'in', 'ii', 'eee', 'ee']

def merge_glyphs(words, merges):
    ms = sorted(merges, key=len, reverse=True)
    out = []
    for w in words:
        i, syms = 0, []
        while i < len(w):
            for m in ms:
                if w.startswith(m, i):
                    syms.append(m); i += len(m); break
            else:
                syms.append(w[i]); i += 1
        out.append(syms)
    return out

def determinism_merge(sym_words, p=DET_P, minfrac=DET_MINFRAC, max_iter=200):
    words = [list(w) for w in sym_words]
    merges = []
    for _ in range(max_iter):
        total = sum(len(w) for w in words)
        pair, first = Counter(), Counter()
        for w in words:
            for a, b in zip(w, w[1:]):
                pair[(a, b)] += 1; first[a] += 1
        best = None
        for (a, b), c in pair.items():
            if c >= minfrac*total and c/first[a] >= p and (best is None or c > best[1]):
                best = ((a, b), c)
        if not best:
            break
        (a, b), c = best
        merges.append({'pair': a + '+' + b, 'count': c, 'p_b_given_a': round(c/first[a], 3)})
        new = a + b
        for w in words:
            i, out = 0, []
            while i < len(w):
                if i+1 < len(w) and w[i] == a and w[i+1] == b:
                    out.append(new); i += 2
                else:
                    out.append(w[i]); i += 1
            w[:] = out
    return words, merges

def alphabet_block(words, label):
    """H2|1 and final-symbol entropy at raw / det-merge levels (any corpus) and at
    levels b/c (+det) for EVA text."""
    res = {'label': label}
    raw = [list(w) for w in words]
    h1, h2 = seq_stats(raw)
    res['raw'] = {'symbols': len(set(s for w in raw for s in w)), 'H1': round(h1, 3),
                  'H2_given_1': round(h2, 3), 'final_H': round(H(Counter(w[-1] for w in raw)), 3)}
    det, merges = determinism_merge(raw)
    h1, h2 = seq_stats(det)
    res['det'] = {'symbols': len(set(s for w in det for s in w)), 'H1': round(h1, 3),
                  'H2_given_1': round(h2, 3), 'final_H': round(H(Counter(w[-1] for w in det)), 3),
                  'merges': merges}
    return res

def eva_alphabet_block(words):
    res = alphabet_block(words, 'Voynich clean')
    for name, lv in (('b', LEVEL_B), ('c', LEVEL_C)):
        sym = merge_glyphs(words, lv)
        h1, h2 = seq_stats(sym)
        res[name] = {'symbols': len(set(s for w in sym for s in w)), 'H1': round(h1, 3),
                     'H2_given_1': round(h2, 3), 'final_H': round(H(Counter(w[-1] for w in sym)), 3)}
        det, merges = determinism_merge(sym)
        h1, h2 = seq_stats(det)
        res[name + '_det'] = {'symbols': len(set(s for w in det for s in w)), 'H1': round(h1, 3),
                              'H2_given_1': round(h2, 3),
                              'final_H': round(H(Counter(w[-1] for w in det))), 'merges': merges}
        res[name + '_det']['final_H'] = round(H(Counter(w[-1] for w in det)), 3)
    return res

# ================================================================== ciphers ===

CORE = ['cth', 'cph', 'ckh', 'cfh', 't', 'p', 'k', 'f']
MANTLE = ['ch', 'sh', 'ee']

def split_word(w):
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

def build_cipher_tables(voy_words):
    letters = Counter(c for w in voy_words for c in w)
    eva_letters = [c for c, _ in letters.most_common()] + \
                  [c for c in 'abcdefghijklmnopqrstuvwxyz' if c not in letters]
    ngrams = Counter()
    for w in voy_words:
        for n in (2, 3):
            for i in range(len(w)-n+1):
                ngrams[w[i:i+n]] += 1
    groups = [(g, c) for g, c in ngrams.most_common(120)]
    left, right = Counter(), Counter()
    for w in voy_words:
        l, _, r = split_word(w)
        if l: left[l] += 1
        if r: right[r] += 1
    return {'letters': eva_letters, 'groups': groups,
            'left': [g for g, _ in left.most_common(40)],
            'right': [g for g, _ in right.most_common(40)]}

def letter_ranks(plain_words):
    c = Counter(ch for w in plain_words for ch in w)
    ranked = [ch for ch, _ in c.most_common()]
    return {ch: i for i, ch in enumerate(ranked)}

def encipher(plain_words, tables, kind, seed=SEED_HOMOPHONE):
    rng = random.Random(seed)
    rank = letter_ranks(plain_words)
    groups = tables['groups']
    def group(i):
        return groups[i % len(groups)][0]
    def homophone(ch):
        i = rank[ch]
        opts = [groups[(i + 26*k) % len(groups)] for k in range(3)]
        gs, ws = zip(*opts)
        return rng.choices(gs, ws)[0]
    out = []
    for w in plain_words:
        if kind == 'C1':
            out.append(''.join(tables['letters'][rank[ch] % 26] for ch in w))
        elif kind == 'C2':
            out.append(''.join(group(rank[ch]) for ch in w))
        elif kind == 'C3':
            out.append(''.join(homophone(ch) for ch in w))
        elif kind == 'C4':
            abbr = w[0] + ''.join(ch for ch in w[1:] if ch not in 'aeiou')
            out.append(''.join(homophone(ch) for ch in abbr))
        elif kind == 'C6':   # EXPLORATORY, post hoc, not in PROTOCOL: abbreviated fixed verbose
            abbr = w[0] + ''.join(ch for ch in w[1:] if ch not in 'aeiou')
            out.append(''.join(group(rank[ch]) for ch in abbr))
        elif kind == 'C5':
            L, R = tables['left'], tables['right']
            if len(w) == 1:
                out.append(L[rank[w[0]] % len(L)])
            else:
                mid = ''.join(tables['letters'][rank[ch] % 26] for ch in w[1:-1])
                out.append(L[rank[w[0]] % len(L)] + mid + R[rank[w[-1]] % len(R)])
    return out

def cipher_block(plain_triples, tables, label):
    res = {}
    plain_words = [w for _, _, ws in plain_triples for w in ws]
    res['plaintext'] = full_metrics(plain_triples) | {'label': label}
    for kind in ('C1', 'C2', 'C3', 'C4', 'C5', 'C6'):
        ct = encipher(plain_words, tables, kind)
        # re-cut into the plaintext's entries
        trip, k = [], 0
        for f, pid, ws in plain_triples:
            trip.append((f, pid, ct[k:k+len(ws)])); k += len(ws)
        m = full_metrics(trip)
        ab = alphabet_block(ct, kind)
        m['H2_given_1_det'] = ab['det']['H2_given_1']
        m['det_merges'] = len(ab['det']['merges'])
        m['sample'] = ' '.join(ct[:8])
        res[kind] = m
    return res

# ===================================================================== A3 ===

def permutation_null(triples, n_perm=N_PERM, seed=SEED_DISTANT):
    words = [w for _, _, ws in triples for w in ws]
    sizes = [len(ws) for _, _, ws in triples]
    rng = random.Random(seed)
    adj, far, uniq = [], [], []
    for _ in range(n_perm):
        rng.shuffle(words)
        k, trip = 0, []
        for (f, pid, _), s in zip(triples, sizes):
            trip.append((f, pid, words[k:k+s])); k += s
        m = page_metrics(trip)
        adj.append(m['jaccard_adjacent']); far.append(m['jaccard_distant']); uniq.append(m['page_unique_share'])
    def summ(xs):
        xs = sorted(xs)
        return {'mean': round(statistics.mean(xs), 4), 'sd': round(statistics.pstdev(xs), 4),
                'p2.5': round(xs[int(0.025*len(xs))], 4), 'p97.5': round(xs[min(len(xs)-1, int(0.975*len(xs)))], 4)}
    return {'n_perm': n_perm, 'jaccard_adjacent': summ(adj), 'jaccard_distant': summ(far),
            'page_unique_share': summ(uniq)}

def confound_block(pages, seed=SEED_DISTANT, min_dist=5):
    psets = {p['id']: set(p['words']) for p in pages}
    def jac(a, b): return len(a & b) / max(len(a | b), 1)
    def key(p): return (p['meta'].get('L', '?'), p['meta'].get('I', '?'))
    same, diff = [], []
    for a, b in zip(pages, pages[1:]):
        (same if key(a) == key(b) else diff).append(jac(psets[a['id']], psets[b['id']]))
    rng = random.Random(seed); far_same = []
    for p in pages:
        cands = [q for q in pages if q is not p and key(q) == key(p) and abs(q['fnum']-p['fnum']) >= min_dist]
        if cands:
            far_same.append(jac(psets[p['id']], psets[rng.choice(cands)['id']]))
    # adjacent pairs crossing language only / section only
    cross_L = [jac(psets[a['id']], psets[b['id']]) for a, b in zip(pages, pages[1:])
               if a['meta'].get('L') != b['meta'].get('L')]
    def mean(xs): return round(sum(xs)/len(xs), 4) if xs else None
    return {
        'adjacent_pairs_same_L_and_I': len(same), 'adjacent_same_L_I_jaccard': mean(same),
        'adjacent_pairs_diff_L_or_I': len(diff), 'adjacent_diff_L_or_I_jaccard': mean(diff),
        'distant_same_L_I_pairs': len(far_same), 'distant_same_L_I_jaccard': mean(far_same),
        'ratio_within_class': round(mean(same)/mean(far_same), 3) if same and far_same else None,
        'adjacent_cross_language_pairs': len(cross_L), 'adjacent_cross_language_jaccard': mean(cross_L),
        'language_counts': dict(Counter(p['meta'].get('L', '?') for p in pages)),
        'section_counts': dict(Counter(p['meta'].get('I', '?') for p in pages)),
    }

# =================================================================== main ===

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True)
    ap.add_argument('--lab', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    repo, lab, out = Path(args.repo), Path(args.lab), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    corpus = repo / 'data/corpora/ZL3b-n.txt'
    culp_path = lab / 'pg49513.txt'
    alice_path = repo / 'data/corpora/pg11.txt'
    bibles = sorted((lab / 'bibles').glob('*.xml'))
    skeat_path = lab / 'pg22120_chaucer_skeat_CT.txt'
    purves_path = lab / 'pg2383_chaucer_purves.txt'
    hashes = {str(p.name): sha256(p) for p in [corpus, culp_path, alice_path, skeat_path, purves_path] + bibles}
    (out / 'source_hashes.json').write_text(json.dumps(hashes, indent=1))
    R = {'protocol': 'PROTOCOL.md', 'sample_tokens': SAMPLE, 'verdicts': {}}

    # ---------------------------------------------------------------- A0 ----
    fam = family_load_pages(corpus)
    fam_words = [w for _, _, ws in fam for w in ws]
    clean_pages = clean_load(corpus)
    clean = as_triples(clean_pages)
    clean_words = [w for _, _, ws in clean for w in ws]
    nocomma = as_triples(clean_load(corpus, comma_split=False))
    contaminated = [w for w in fam_words if not re.fullmatch(r'[a-z]+', w)]
    A0 = {
        'family_parser': full_metrics(fam),
        'clean_parser': full_metrics(clean),
        'clean_parser_comma_merged': full_metrics(nocomma),
        'contaminated_tokens': len(contaminated), 'contaminated_types': len(set(contaminated)),
        'contamination_examples': Counter(contaminated).most_common(15),
        'family_char_inventory': Counter(''.join(fam_words)).most_common(),
        'clean_min_len2': core_metrics([w for w in clean_words if len(w) >= 2]),
    }
    R['A0'] = A0
    t = A0['clean_parser']['types']
    R['verdicts']['R0.1'] = 'CONTAMINATED' if abs(t - 10120) / 10120 > 0.03 else 'WITHIN 3%'

    # controls with the [a-z]+ no-length-filter tokeniser at <=35k tokens (R0.2)
    lang_words = {}
    for xml in bibles:
        lang_words[xml.stem] = letters_only(load_bible(xml))[:SAMPLE]
    culp = culpeper_entries(culp_path)
    alice = alice_chunks(alice_path)
    ctrl_words = {
        'Culpeper': letters_only(words_en(pg_body(culp_path), min_len=1))[:SAMPLE],
        'Alice': letters_only(words_en(pg_body(alice_path), min_len=1))[:SAMPLE],
    }
    richness = {k: core_metrics(v) for k, v in (lang_words | ctrl_words).items()}
    A0['controls_same_tokeniser'] = richness
    A0['clean_parser_35k'] = core_metrics(clean_words[:SAMPLE])
    A0['clean_parser_comma_merged_35k'] = core_metrics([w for _, _, ws in nocomma for w in ws][:SAMPLE])
    max_ctrl = max(richness.items(), key=lambda kv: kv[1]['types'])
    A0['max_control_types'] = {'name': max_ctrl[0], 'types': max_ctrl[1]['types']}
    t35 = A0['clean_parser_35k']['types']
    R['verdicts']['R0.2'] = ('RICHEST SURVIVES' if t35 > max_ctrl[1]['types'] else 'RICHEST FAILS')

    # ---------------------------------------------------------------- A1 ----
    A1 = {'voynich': eva_alphabet_block(clean_words), 'languages': {}, 'controls': {}}
    for k, v in lang_words.items():
        A1['languages'][k] = alphabet_block(v, k)
    for k, v in ctrl_words.items():
        A1['controls'][k] = alphabet_block(v, k)
    R['A1'] = A1
    voy_b_det = A1['voynich']['b_det']['H2_given_1']
    min_lang = min((v['det']['H2_given_1'], k) for k, v in A1['languages'].items())
    A1['gate_R1_1'] = {'voynich_b_det': voy_b_det, 'lowest_language_det': min_lang,
                       'gap': round(min_lang[0] - voy_b_det, 3)}
    R['verdicts']['R1.1'] = 'ALPHABET-ROBUST' if min_lang[0] - voy_b_det >= 0.30 else 'ALPHABET-DEPENDENT'
    voy_c_final = A1['voynich']['c']['final_H']
    min_final = min((v['raw']['final_H'], k) for k, v in A1['languages'].items())
    A1['gate_R1_2'] = {'voynich_level_c_final_H': voy_c_final, 'lowest_language_raw_final_H': min_final,
                       'gap': round(min_final[0] - voy_c_final, 3)}
    R['verdicts']['R1.2'] = 'ALPHABET-ROBUST' if min_final[0] - voy_c_final >= 0.20 else 'ALPHABET-DEPENDENT'

    # ---------------------------------------------------------------- A2 ----
    tables = build_cipher_tables(clean_words)
    culp_letters = [(i, n, letters_only(ws)) for i, n, ws in culp]
    culp_letters = truncate_triples(culp_letters, SAMPLE)
    lat = lang_words['Latin']
    lat_triples = [(i, f'chunk{i}', lat[i*155:(i+1)*155]) for i in range(len(lat)//155)]
    A2 = {'tables_summary': {'letters': tables['letters'][:26], 'top_groups': tables['groups'][:30],
                             'left_fragments': tables['left'][:15], 'right_fragments': tables['right'][:15]},
          'culpeper': cipher_block(culp_letters, tables, 'Culpeper entries (<=35k tokens)'),
          'latin': cipher_block(lat_triples, tables, 'Latin Vulgate (35k tokens, 155-token chunks)')}
    R['A2'] = A2
    hits = []
    for src in ('culpeper', 'latin'):
        for kind in ('C1', 'C2', 'C3', 'C4', 'C5'):
            m = A2[src][kind]
            ok = m['H2_given_1'] <= 2.56 and m['last_char_H'] <= 2.90 and 0.22 <= m['ttr'] <= 0.32
            m['passes_R2_1'] = ok
            if ok:
                hits.append(f'{src}/{kind}')
    A2['R2_1_hits'] = hits
    R['verdicts']['R2.1'] = 'NON-DISCRIMINATING' if hits else 'NOT REPRODUCED BY TESTED CIPHERS'

    # ---------------------------------------------------------------- A3 ----
    obs = page_metrics(clean)
    null = permutation_null(clean)
    conf = confound_block(clean_pages)
    p_only = as_triples(clean_load(corpus, loci_filter={'P'}))
    culp_trunc = truncate_triples([(i, n, ws) for i, n, ws in culp], SAMPLE)
    alice_trunc = truncate_triples(alice, SAMPLE)
    A3 = {'observed': obs, 'permutation_null': null, 'confounds': conf,
          'paragraph_loci_only': page_metrics(p_only) | {'tokens': sum(len(ws) for _, _, ws in p_only)},
          'controls_size_matched': {
              'Culpeper_full': page_metrics([(i, n, ws) for i, n, ws in culp]) | {'tokens': sum(len(ws) for _, _, ws in culp)},
              'Culpeper_35k': page_metrics(culp_trunc) | {'tokens': sum(len(ws) for _, _, ws in culp_trunc)},
              'Alice_full': page_metrics(alice) | {'tokens': sum(len(ws) for _, _, ws in alice)},
              'Alice_35k': page_metrics(alice_trunc) | {'tokens': sum(len(ws) for _, _, ws in alice_trunc)},
          }}
    # sensitivity: uncertain spaces treated as no-space (the family's choice)
    nocomma_pages = clean_load(corpus, comma_split=False)
    A3['comma_merged_sensitivity'] = {
        'observed': page_metrics(nocomma), 'permutation_null': permutation_null(nocomma),
        'confounds': confound_block(nocomma_pages)}
    A3['family_parser_observed'] = page_metrics(fam)
    R['A3'] = A3
    r31 = conf['ratio_within_class'] is not None and conf['ratio_within_class'] >= 1.30 \
        and obs['jaccard_adjacent'] > null['jaccard_adjacent']['p97.5']
    R['verdicts']['R3.1'] = 'TOPICAL ORGANISATION SURVIVES' if r31 else 'LANGUAGE/SECTION ARTEFACT'
    excess = obs['page_unique_share'] - null['page_unique_share']['mean']
    A3['R3_2_excess_over_null'] = round(excess, 4)
    R['verdicts']['R3.2'] = 'ANOMALOUS STRUCTURE SURVIVES' if excess >= 0.05 else 'HAPAX-RICHNESS CONSEQUENCE'
    A3['R3_3_ratio_vs_culpeper_35k'] = round(obs['page_unique_share'] / A3['controls_size_matched']['Culpeper_35k']['page_unique_share'], 2)

    # ---------------------------------------------------------------- A4 ----
    sk_text, pu_text = chaucer_skeat(skeat_path), chaucer_purves(purves_path)
    A4 = {}
    for label, txt in (('Skeat_MiddleEnglish', sk_text), ('Purves_modernised', pu_text)):
        w2 = letters_only(words_en(txt, min_len=2))[:SAMPLE]
        w1 = letters_only(words_en(txt, min_len=1))[:SAMPLE]
        A4[label] = {'min_len2': core_metrics(w2), 'min_len1': core_metrics(w1),
                     'sample': ' '.join(w1[:20])}
    A4['voynich_clean'] = {'min_len1': core_metrics(clean_words),
                           'min_len2': core_metrics([w for w in clean_words if len(w) >= 2])}
    R['A4'] = A4
    me = A4['Skeat_MiddleEnglish']['min_len1']['ttr']
    R['verdicts']['R4.1'] = 'WITHDRAWN' if me >= 0.25 else ('SURVIVES this control' if me <= 0.22 else 'WEAKENED')
    A4['R4_2_orthography_effect_ttr'] = round(me - A4['Purves_modernised']['min_len1']['ttr'], 4)

    (out / 'results.json').write_text(json.dumps(R, indent=1, ensure_ascii=False))
    print(json.dumps(R['verdicts'], indent=1))
    print('A0 family vs clean:', A0['family_parser']['types'], A0['clean_parser']['types'], A0['clean_parser']['ttr'])
    print('A1 gates:', A1['gate_R1_1'], A1['gate_R1_2'])
    print('A2 hits:', hits)
    print('A3:', obs, null['jaccard_adjacent'], null['page_unique_share'], conf['ratio_within_class'])
    print('A4:', me, A4['Purves_modernised']['min_len1']['ttr'])

if __name__ == '__main__':
    main()
