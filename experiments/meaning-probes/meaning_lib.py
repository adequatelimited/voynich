#!/usr/bin/env python3
"""meaning_lib.py — data access for the meaning-probes pass.

DATA ACCESS ONLY. No statistics, no decision rules, no claims. Every test script
imports from here so that all five tests see exactly the same corpus objects.

Provenance of the clean IVTFF parser: `clean_tokens` / `clean_load` are verbatim
from experiments/adversarial-critique/adversarial_critique.py (protocol 15b6999),
which established that the earlier "family" parser inflated the type count by 24%.
The 20-merge glyph list is the frozen result of T2 in
experiments/discriminating-tests (protocol 318a679), freq mode, corpus Voynich_S.

Stdlib only. Deterministic.
"""
import hashlib, io, math, re, unicodedata
from collections import Counter, OrderedDict
from pathlib import Path

# ============================================================== constants ===

SEED = 408                    # the project's constant

# T2 frozen byte-pair merges, in application order (freq mode, Voynich_S).
MERGES_20 = ['ch', 'dy', 'ai', 'ok', 'ol', 'ee', 'sh', 'in', 'che', 'aiin',
             'ot', 'ar', 'al', 'qok', 'or', 'she', 'eey', 'ain', 'daiin', 'chedy']

# EVA gallows characters (single) and their benched forms.
GALLOWS = ['cth', 'ckh', 'cph', 'cfh', 't', 'p', 'k', 'f']

# The ten zodiac signs that survive, in manuscript order, with their folios.
# Capricorn and Aquarius are lost; the series begins at Pisces.
ZODIAC_SIGNS = OrderedDict([
    ('Pisces',      ['f70v2']),
    ('Aries',       ['f70v1', 'f71r']),
    ('Taurus',      ['f71v', 'f72r1']),
    ('Gemini',      ['f72r2']),
    ('Cancer',      ['f72r3']),
    ('Leo',         ['f72v3']),
    ('Virgo',       ['f72v2']),
    ('Libra',       ['f72v1']),
    ('Scorpius',    ['f73r']),
    ('Sagittarius', ['f73v']),
])
FIT_SIGNS = ['Pisces', 'Aries', 'Taurus', 'Gemini', 'Cancer']
TEST_SIGNS = ['Leo', 'Virgo', 'Libra', 'Scorpius', 'Sagittarius']


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ========================================================= IVTFF parsing ===

HDR = re.compile(r'^<(f\d+[rv]\d*)>\s*<!([^>]*)>')
LOC = re.compile(r'^<(f(\d+)[rv]\d*)\.(\d+),([^>]*)>\s*(.*)$')
CLOCK = re.compile(r'^\d\d:\d\d$')


def clean_tokens(text, comma_split=True):
    """Verbatim from adversarial_critique.py. `,` = uncertain space.

    comma_split=True treats it as a space (the conservative reading),
    False as no space. Both are reported wherever the choice can matter.
    """
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
        if not w or re.search(r'[?@\d]', w):             # illegible / extended glyph: drop
            continue
        if re.fullmatch(r'[a-z]+', w):
            out.append(w)
    return out


def parse_pages(path, comma_split=True):
    """Full-fidelity parse: pages -> loci, keeping locus codes, inline clock
    comments, the free-text comment that immediately precedes a locus, and the
    paragraph-start/end markers <%> / <$>.

    Returns OrderedDict page_id -> {
        'id', 'fnum', 'meta' ($Q $P $F $B $I $L $H $C $X), 'loci': [locus...]}
    locus = {'n', 'code', 'pos', 'type', 'sub', 'raw', 'words', 'clock',
             'comment', 'para_start', 'para_end'}
    where pos = code[0] ('@' first of a group, '&' continuation, '+' next line,
    '=' last line, '*' , '~'), type = code[1] ('P' paragraph, 'L' label,
    'C' circular, 'R' radial, 'T' title), sub = code[2:] (e.g. 'z' zodiac).
    """
    pages = OrderedDict()
    cur, pending = None, None
    for raw in io.open(path, encoding='utf-8', errors='replace'):
        line = raw.rstrip('\n')
        m = HDR.match(line)
        if m:
            cur = m.group(1)
            pages[cur] = {'id': cur, 'fnum': int(re.match(r'f(\d+)', cur).group(1)),
                          'meta': dict(re.findall(r'\$([A-Z])=(\S+)', m.group(2))),
                          'loci': []}
            pending = None
            continue
        if line.startswith('#'):
            c = line.lstrip('#').strip()
            if c:
                pending = c
            continue
        m = LOC.match(line)
        if not m or cur is None:
            continue
        code, text = m.group(4), m.group(5)
        inline = re.findall(r'<!([^>]*)>', text)
        clock = next((i for i in inline if CLOCK.match(i)), None)
        pages[cur]['loci'].append({
            'n': int(m.group(3)), 'code': code,
            'pos': code[0] if code else '?',
            'type': code[1] if len(code) > 1 else '?',
            'sub': code[2:] if len(code) > 2 else '',
            'raw': text,
            'words': clean_tokens(text, comma_split),
            'clock': clock,
            'comment': pending,
            'para_start': '<%>' in text,
            'para_end': '<$>' in text,
        })
        pending = None
    return pages


def section_pages(pages, illus):
    """Pages whose $I illustration code is in `illus` (a string of codes).
    H herbal, S stars/recipes, B biological, P pharmaceutical, Z zodiac,
    C cosmological, A astronomical, T text-only."""
    return [p for p in pages.values() if p['meta'].get('I') in illus]


def all_words(pages, types=None):
    out = []
    for p in pages.values() if isinstance(pages, dict) else pages:
        for l in p['loci']:
            if types is None or l['type'] in types:
                out.extend(l['words'])
    return out


# ================================================== glyph-unit segmentation ==

def bpe_apply(word, merges=MERGES_20):
    """Apply byte-pair merges IN ORDER (the way the T2 curve produced them),
    not longest-match. Returns a list of glyph units."""
    syms = list(word)
    for m in merges:
        # find the (a, b) split that produced this merge: the merge string is
        # a+b where a is itself a unit already present. Re-derive by scanning
        # for any adjacent pair whose concatenation equals m.
        i = 0
        out = []
        while i < len(syms):
            if i + 1 < len(syms) and syms[i] + syms[i + 1] == m:
                out.append(m); i += 2
            else:
                out.append(syms[i]); i += 1
        syms = out
    return syms


def units(words, merges=MERGES_20):
    return [bpe_apply(w, merges) for w in words]


def unit_str(u, sep='|'):
    return sep.join(u)


# ================================================= zodiac label extraction ==

def zodiac_labels(pages, comma_split=True):
    """One record per zodiac label locus, in manuscript (ring) order.

    Ring identity: within a page, a new ring begins at every Lz locus whose
    position character is '@' (ZL marks the first member of each locus group
    that way and continues with '&'). This reproduces the ring blocks named in
    the ZL comments (outer / inner / central) on every zodiac page.

    Returns list of dicts:
      sign, page, locus_n, ring (0-based within sign), idx_in_ring,
      idx_in_sign, clock, clock_min, words, text (words joined), n_words
    """
    out = []
    for sign, folios in ZODIAC_SIGNS.items():
        ring = -1
        idx_in_sign = 0
        for fo in folios:
            p = pages.get(fo)
            if p is None:
                continue
            for l in p['loci']:
                if l['type'] != 'L' or l['sub'] != 'z':
                    continue
                if l['pos'] == '@' or ring < 0:
                    ring += 1
                    idx_in_ring = 0
                if not l['words']:
                    continue
                cm = None
                if l['clock']:
                    hh, mm = l['clock'].split(':')
                    cm = (int(hh) % 12) * 60 + int(mm)
                out.append({'sign': sign, 'page': fo, 'locus_n': l['n'],
                            'ring': ring, 'idx_in_ring': idx_in_ring,
                            'idx_in_sign': idx_in_sign,
                            'clock': l['clock'], 'clock_min': cm,
                            'words': l['words'],
                            'text': ' '.join(l['words']),
                            'n_words': len(l['words'])})
                idx_in_ring += 1
                idx_in_sign += 1
    return out


def sign_rings(labels):
    """sign -> ring -> list of label records (manuscript order)."""
    out = OrderedDict()
    for r in labels:
        out.setdefault(r['sign'], OrderedDict()).setdefault(r['ring'], []).append(r)
    return out


# ================================================ recipe paragraph extraction

STAR = re.compile(r'(?i)\b(light|dark|lightish|darkish)\b')
POINTS = re.compile(r'(\d+)(?:/\d+)?\s*[-\s]?point')
WORDPOINTS = {'six': 6, 'seven': 7, 'eight': 8, 'nine': 9}
WORDPT = re.compile(r'(?i)\b(six|seven|eight|nine)[-\s]pointed')


def parse_star(comment):
    """Attributes of the star drawn beside a Recipes paragraph, from the ZL
    comment on the line above. Returns dict or None when the comment does not
    describe a star."""
    if not comment:
        return None
    c = comment.strip()
    if 'star' not in c.lower():
        return None
    m = POINTS.search(c)
    pts = int(m.group(1)) if m else None
    if pts is None:
        m = WORDPT.search(c)
        pts = WORDPOINTS[m.group(1).lower()] if m else None
    sh = STAR.search(c)
    return {'raw': c,
            'shade': (sh.group(1).lower() if sh else None),
            'points': pts,
            'dotted': ('dotted' in c.lower()),
            'tail': ('tail' in c.lower()),
            'uncertain': ('?' in c)}


def paragraphs(pages, page_ids=None, illus=None):
    """Reconstruct paragraphs: a paragraph runs from a locus carrying <%> up to
    and including the next locus carrying <$> (or to the locus before the next
    <%> if the end marker is missing).

    Returns list of dicts: page, illus, lang, start_locus, n_lines, words,
    first_word, first_line_words, star (from the comment on the <%> line).
    """
    out = []
    for p in pages.values():
        if page_ids is not None and p['id'] not in page_ids:
            continue
        if illus is not None and p['meta'].get('I') not in illus:
            continue
        cur = None
        for l in p['loci']:
            if l['type'] not in ('P',):
                continue
            if l['para_start']:
                if cur is not None:
                    out.append(cur)
                cur = {'page': p['id'], 'illus': p['meta'].get('I'),
                       'lang': p['meta'].get('L'), 'hand': p['meta'].get('H'),
                       'start_locus': l['n'], 'n_lines': 0, 'words': [],
                       'lines': [], 'star': parse_star(l['comment']),
                       'comment': l['comment']}
            if cur is None:
                continue
            cur['n_lines'] += 1
            cur['words'].extend(l['words'])
            cur['lines'].append(l['words'])
            if l['para_end']:
                out.append(cur)
                cur = None
        if cur is not None:
            out.append(cur)
    for d in out:
        d['first_word'] = d['words'][0] if d['words'] else None
        d['first_line_words'] = d['lines'][0] if d['lines'] else []
    return [d for d in out if d['words']]


def non_initial_line_words(pages, page_ids=None, illus=None):
    """First word of every paragraph-internal line (a line that is not the
    first line of its paragraph). The natural within-section control for
    paragraph-initial words."""
    out = []
    for p in pages.values():
        if page_ids is not None and p['id'] not in page_ids:
            continue
        if illus is not None and p['meta'].get('I') not in illus:
            continue
        seen_start = False
        for l in p['loci']:
            if l['type'] != 'P':
                continue
            if l['para_start']:
                seen_start = True
                continue
            if seen_start and l['words']:
                out.append(l['words'][0])
    return out


# ============================================== label / text split by page ==

def label_text_by_page(pages, illus=None):
    """Per page: the words that sit in label loci and the words that sit in
    running-text loci (paragraph, circular, radial). Same page = same scribe,
    same Currier language, same section, so the comparison is confound-free
    for those three variables."""
    out = OrderedDict()
    for p in pages.values():
        if illus is not None and p['meta'].get('I') not in illus:
            continue
        lab, txt = [], []
        for l in p['loci']:
            if l['type'] == 'L':
                lab.extend(l['words'])
            elif l['type'] in ('P', 'C', 'R'):
                txt.extend(l['words'])
        if lab and txt:
            out[p['id']] = {'labels': lab, 'text': txt,
                            'illus': p['meta'].get('I'),
                            'lang': p['meta'].get('L')}
    return out


# ================================================== control: numeral series ==
# Spelled-out and written numeral systems 1..30. These are lexical facts, not
# corpus measurements; they exist to calibrate the power of the ordinal tests.

_EN = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
       'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen',
       'eighteen', 'nineteen', 'twenty', 'twentyone', 'twentytwo', 'twentythree',
       'twentyfour', 'twentyfive', 'twentysix', 'twentyseven', 'twentyeight',
       'twentynine', 'thirty']
_LA = ['unus', 'duo', 'tres', 'quattuor', 'quinque', 'sex', 'septem', 'octo', 'novem',
       'decem', 'undecim', 'duodecim', 'tredecim', 'quattuordecim', 'quindecim',
       'sedecim', 'septendecim', 'duodeviginti', 'undeviginti', 'viginti',
       'vigintiunus', 'vigintiduo', 'vigintitres', 'vigintiquattuor', 'vigintiquinque',
       'vigintisex', 'vigintiseptem', 'vigintiocto', 'vigintinovem', 'triginta']
_IT = ['uno', 'due', 'tre', 'quattro', 'cinque', 'sei', 'sette', 'otto', 'nove', 'dieci',
       'undici', 'dodici', 'tredici', 'quattordici', 'quindici', 'sedici', 'diciassette',
       'diciotto', 'diciannove', 'venti', 'ventuno', 'ventidue', 'ventitre',
       'ventiquattro', 'venticinque', 'ventisei', 'ventisette', 'ventotto',
       'ventinove', 'trenta']
_DE = ['eins', 'zwei', 'drei', 'vier', 'fuenf', 'sechs', 'sieben', 'acht', 'neun', 'zehn',
       'elf', 'zwoelf', 'dreizehn', 'vierzehn', 'fuenfzehn', 'sechzehn', 'siebzehn',
       'achtzehn', 'neunzehn', 'zwanzig', 'einundzwanzig', 'zweiundzwanzig',
       'dreiundzwanzig', 'vierundzwanzig', 'fuenfundzwanzig', 'sechsundzwanzig',
       'siebenundzwanzig', 'achtundzwanzig', 'neunundzwanzig', 'dreissig']
_FR = ['un', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept', 'huit', 'neuf', 'dix',
       'onze', 'douze', 'treize', 'quatorze', 'quinze', 'seize', 'dixsept', 'dixhuit',
       'dixneuf', 'vingt', 'vingtetun', 'vingtdeux', 'vingttrois', 'vingtquatre',
       'vingtcinq', 'vingtsix', 'vingtsept', 'vingthuit', 'vingtneuf', 'trente']

_ROMAN_UNITS = ['', 'i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix']
_ROMAN_TENS = ['', 'x', 'xx', 'xxx']


def roman(n):
    return _ROMAN_TENS[n // 10] + _ROMAN_UNITS[n % 10]


# Greek Milesian alphabetic numerals 1..30 (alpha..iota, kappa.., transliterated
# to Latin letters so every control shares one alphabet family).
_GREEK_1_9 = ['a', 'b', 'g', 'd', 'e', 'st', 'z', 'h', 'th']
_GREEK_TENS = ['', 'i', 'k', 'l']


def milesian(n):
    return _GREEK_TENS[n // 10] + _GREEK_1_9[(n % 10) - 1] if n % 10 else _GREEK_TENS[n // 10]


def numeral_controls():
    """name -> list of 30 strings, index 0 = 'one'."""
    return OrderedDict([
        ('English', _EN), ('Latin', _LA), ('Italian', _IT), ('German', _DE),
        ('French', _FR),
        ('Roman', [roman(n) for n in range(1, 31)]),
        ('GreekMilesian', [milesian(n) for n in range(1, 31)]),
        ('LatinOrdinalAbbrev', ['d' + roman(n) for n in range(1, 31)]),  # "die i", "die ii"...
    ])


# ============================================= control: Culpeper herb names ==

def pg_body(path):
    t = io.open(path, encoding='utf-8', errors='replace').read()
    s = t.find('*** START OF'); e = t.find('*** END OF')
    return t[s:e] if s >= 0 and e > s else t


def words_en(text, min_len=2):
    text = text.replace('\u2019', "'")
    return [w.lower() for w in re.findall(r"[A-Za-z']+", text) if len(w) >= min_len]


def letters_only(words):
    out = []
    for w in words:
        s = ''.join(ch for ch in unicodedata.normalize('NFC', w.lower())
                    if unicodedata.category(ch).startswith('L'))
        if s:
            out.append(s)
    return out


CULP_HEAD = re.compile(r'^([A-Z][A-Za-z\'\- ]{2,60})\.?\s*$')


def culpeper_entries(path):
    """(index, heading, body words) for each herb entry in Culpeper's Complete
    Herbal. Heading detection: a short all-initial-capitalised line followed
    within three lines by a paragraph. Verbatim rule from critique_lib.
    """
    body = pg_body(path)
    lines = body.split('\n')
    entries, cur = [], None
    for i, ln in enumerate(lines):
        s = ln.strip()
        m = CULP_HEAD.match(s)
        if m and len(s.split()) <= 6 and s.upper() != s.lower() and s[0].isupper():
            nxt = ' '.join(lines[i + 1:i + 4]).strip()
            if len(nxt) > 40:
                if cur:
                    entries.append(cur)
                cur = [len(entries), s, []]
                continue
        if cur is not None:
            cur[2].extend(words_en(s))
    if cur:
        entries.append(cur)
    return [(i, h, w) for i, h, w in entries if len(w) >= 30]


# ==================================================== similarity primitives ==

def lcs_len(a, b):
    la, lb = len(a), len(b)
    if la == 0 or lb == 0:
        return 0
    prev = [0] * (lb + 1)
    for i in range(1, la + 1):
        cur = [0] * (lb + 1)
        ai = a[i - 1]
        for j in range(1, lb + 1):
            cur[j] = prev[j - 1] + 1 if ai == b[j - 1] else max(prev[j], cur[j - 1])
        prev = cur
    return prev[lb]


def lcs_sim(a, b):
    """Normalised longest-common-subsequence similarity on two sequences
    (lists of glyph units, or strings). 1.0 = identical, 0.0 = disjoint."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return 2.0 * lcs_len(a, b) / (len(a) + len(b))


def edit_dist(a, b):
    la, lb = len(a), len(b)
    if la == 0:
        return lb
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        ai = a[i - 1]
        for j in range(1, lb + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ai != b[j - 1]))
        prev = cur
    return prev[lb]


def edit_sim(a, b):
    m = max(len(a), len(b))
    return 1.0 - edit_dist(a, b) / m if m else 1.0


def H(counter):
    n = sum(counter.values())
    if n == 0:
        return 0.0
    return -sum(c / n * math.log2(c / n) for c in counter.values() if c)
