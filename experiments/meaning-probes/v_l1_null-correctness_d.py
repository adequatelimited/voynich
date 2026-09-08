#!/usr/bin/env python3
"""v_l1_null-correctness_d.py -- is gate leg 1 counting facts or counting units?

Gate leg 1 counts UNITS clearing |log-odds|>=1 with Bonferroni p<0.01. The 25
units of a family partition the words (each word has exactly one initial unit
and one final unit), so the per-unit tests are strongly dependent, and the T2
byte-pair merges can split a single phenomenon across several units.

Three checks on the word-initial family that the test agent calls its strongest
result (qok-, q-, c-, daiin-):

  (1) q- and qok- are both "the word begins with EVA q". Merge them into one
      unit and re-run: does the family still show >= 3 independent effects?
  (2) daiin- : 121 of its 122 TEST text tokens are the bare word "daiin", which
      is also the token driving daiin-FINAL. Restrict to strata of glyph-unit
      length >= 2 (so the bare word is excluded) and re-run both.
  (3) c- rests on a single label token. Leave-one-out: drop that token.

Same corrected MH estimator, same within-stratum word permutation, seed 408.
"""
import io, math, os, random, sys
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meaning_lib as ML

SEED = 408
KAPPA = 1.0
NPERM = int(os.environ.get('NPERM', '10000'))
REPO = 'R:/Coding/LinearA/tmp/voynich_repo'
ZL = REPO + '/data/corpora/ZL3b-n.txt'
OUT = REPO + '/experiments/meaning-probes/results'
LOG = []
def say(s=''):
    print(s); LOG.append(str(s))


def mh(strata):
    """corrected MH log-OR for a single binary unit; strata = (n, m1, pool) with
    pool entries 1 (carries unit) / 0 (does not), first m1 = label side."""
    R = S = 0.0
    for (n, m1, pool) in strata:
        t = sum(pool)
        if t == 0 or t == n:
            continue
        A = sum(pool[:m1])
        m0 = n - m1
        p1 = KAPPA * m1 / float(n)
        p0 = KAPPA * m0 / float(n)
        N = n + 2.0 * KAPPA
        R += (A + p1) * (m0 - t + A + p0) / N
        S += (m1 - A + p1) * (t - A + p0) / N
    return math.log(R / S) if (R > 0 and S > 0) else 0.0


def test_binary(name, strata, nperm=NPERM, seed=SEED):
    strata = [(n, m1, pool) for (n, m1, pool) in strata
              if 0 < m1 < n and 0 < sum(pool) < n]
    obs = mh(strata)
    nl = sum(sum(p[:m1]) for (n, m1, p) in strata)
    nt = sum(sum(p) - sum(p[:m1]) for (n, m1, p) in strata)
    rnd = random.Random(seed)
    ge = 0
    a = abs(obs)
    for _ in range(nperm):
        st = []
        for (n, m1, pool) in strata:
            s = rnd.sample(pool, m1)
            rest = list(pool)
            c = Counter(s)
            other = []
            for x in rest:
                if c[x] > 0:
                    c[x] -= 1
                else:
                    other.append(x)
            st.append((n, m1, s + other))
        if abs(mh(st)) >= a - 1e-12:
            ge += 1
    p = (ge + 1.0) / (nperm + 1.0)
    say('  %-46s log-odds=%8.4f  raw p=%.5f  bonf(x25)=%.5f  '
        'support %d label / %d text  strata=%d'
        % (name, obs, p, min(1, p * 25), nl, nt, len(strata)))
    return obs, p


def build(groups, member, minlen=1, drop=None):
    """member(word_units) -> bool. minlen: only strata of glyph-unit length >=
    minlen. drop: (page, word) token to exclude from the label side."""
    out = []
    for pid, lab, txt in groups:
        bl, bt = {}, {}
        for w in lab:
            u = ML.bpe_apply(w)
            if not u:
                continue
            if drop is not None and (pid, w) == drop and member(u):
                continue
            bl.setdefault(len(u), []).append(1 if member(u) else 0)
        for w in txt:
            u = ML.bpe_apply(w)
            if u:
                bt.setdefault(len(u), []).append(1 if member(u) else 0)
        for L, labs in sorted(bl.items()):
            if L < minlen:
                continue
            txts = bt.get(L)
            if not txts:
                continue
            out.append((len(labs) + len(txts), len(labs), labs + txts))
    return out


pages = ML.parse_pages(ZL, comma_split=True)
lt = ML.label_text_by_page(pages)
groups = [(pid, d['labels'], d['text']) for pid, d in lt.items()
          if pages[pid]['fnum'] % 2 == 1]

say('=' * 78)
say('v_l1 D: gate leg 1 counts units, not facts (TEST = odd folios, %d perms)'
    % NPERM)
say('=' * 78)

say('(0) reproduce the four word-initial passers as single binary tests')
test_binary('qok- (first glyph unit == qok)', build(groups, lambda u: u[0] == 'qok'))
test_binary('q- (first glyph unit == q)', build(groups, lambda u: u[0] == 'q'))
test_binary('c- (first glyph unit == c)', build(groups, lambda u: u[0] == 'c'))
test_binary('daiin- (first glyph unit == daiin)',
            build(groups, lambda u: u[0] == 'daiin'))
say()

say('(1) q- and qok- merged: word begins with EVA letter q')
test_binary('EVA q-initial (qok- and q- pooled)',
            build(groups, lambda u: u[0] in ('q', 'qok')))
say('    -> the two units the family counts separately are one phenomenon:')
say('       every q- and qok- word begins with the same EVA character.')
say()

say('(2) daiin: is it an ENDING/PREFIX, or one word type?')
say('    121 of the 122 TEST text tokens with daiin-initial are the bare word')
say('    "daiin" (glyph-unit length 1), which is also its own final unit.')
test_binary('daiin FINAL, all lengths', build(groups, lambda u: u[-1] == 'daiin'))
test_binary('daiin FINAL, glyph-unit length >= 2 only',
            build(groups, lambda u: u[-1] == 'daiin', minlen=2))
test_binary('daiin INITIAL, all lengths',
            build(groups, lambda u: u[0] == 'daiin'))
test_binary('daiin INITIAL, glyph-unit length >= 2 only',
            build(groups, lambda u: u[0] == 'daiin', minlen=2))
say()

say('(3) c- leave-one-out (its only label token is cpheey on f67r2)')
test_binary('c- with that single label token removed',
            build(groups, lambda u: u[0] == 'c', drop=('f67r2', 'cpheey')))
say()

say('(4) how much of the word-FINAL passer daiin survives without the bare word')
say('    (see (2)); and n-final leave-one-out on its 7 label tokens')
for w, pg in [('oteeeon', 'f17r'), ('oeoldan', 'f67r2'), ('oran', 'f67r2'),
              ('dan', 'f71v'), ('dan', 'f89r1'), ('dykaran', 'f89v2'),
              ('olaran', 'f101v')]:
    test_binary('n-final without label token %s@%s' % (w, pg),
                build(groups, lambda u: u[-1] == 'n', drop=(pg, w)),
                nperm=2000)

with io.open(os.path.join(OUT, 'v_l1_null-correctness_d.stdout.txt'), 'w',
             encoding='utf-8') as fh:
    fh.write('\n'.join(LOG) + '\n')
