# Evidence constraints for any translation

These are rejection gates, not clues to force into a preferred language.

## Physical and historical

- Four parchment samples were radiocarbon dated to 1404–1438 CE at 95.4% in the original Arizona AMS report. This dates the parchment, not necessarily the writing: <https://www.voynich.nu/papers/Carbon_GH_2009.pdf>.
- McCrone found the sampled text and drawing inks chemically similar and tentatively contemporaneous; later page/quire numbers and the Latin annotation use different inks: <https://beinecke.library.yale.edu/sites/default/files/files/voynich_analysis.pdf>.
- The surviving codex has 102 folios, missing leaves, foldouts, later foliation, and evidence of rebinding. A decoding must not assume uninterrupted original narrative order: <https://pre1600ms.beinecke.library.yale.edu/docs/pre1600.ms408.htm>.
- Claims of a specific author, source city, John Dee ownership, or Roger Bacon authorship are hypotheses, not established provenance.

## Script and corpus

- EVA is a graphical transliteration convention, not a phonetic Romanization. Capitalization and multicharacter EVA forms may encode joining or glyph structure.
- Currier A and B are statistically distinct varieties, not proven languages. Report both separately; a universal mapping must predict rather than erase their differences.
- Lisa Fagin Davis's peer-reviewed paleographic model proposes five hands. Treat these assignments as a model to test, not ground truth; for manuscript-wide claims, hold out whole proposed hands and do not retune the mapping per hand: <https://doi.org/10.1353/mns.2020.0004>.
- Hand, Currier variety, illustration type, and codicology are strongly associated and partly confounded. A section classifier is not automatically a semantic decoder.
- Labels differ from paragraph text and must be evaluated separately.
- Word forms have strong glyph-slot, line-edge, paragraph-initial, and cross-space dependencies. A proposed mechanism must quantitatively reproduce them.
- Conditional character entropy is unusually low. One-to-one substitution with unchanged segmentation cannot turn ordinary plaintext entropy into the observed value.
- Word-type distributions show page/section burstiness relative to specified shuffled baselines. Matching Zipf frequencies or a few repeated forms is insufficient.
- A June 2026 preprint reports a strong positional boundary profile and shows that its opposite-direction n-gram signal is reproducible by word-level Markov resampling. Treat the proposed four-signature profile as a candidate mechanism benchmark pending reproduction on the pinned corpus; do not use directionality alone as evidence for a cipher or generator: <https://arxiv.org/abs/2604.19762v2>.

Reviews and primary analyses used to set these gates include Bowern and Lindemann (<https://doi.org/10.1146/annurev-linguistics-011619-030613>), Currier's original report (<https://www.voynich.nu/extra/img/curr_main.pdf>), Reddy and Knight (<https://aclanthology.org/W11-1511/>), Smith and Ponzi (<https://doi.org/10.1080/01611194.2019.1596998>), and Montemurro and Zanette (<https://doi.org/10.1371/journal.pone.0066344>).

## Minimum solution gate

These are project acceptance criteria for manuscript-wide claims, not literature-established necessary conditions for every scoped experiment.

A proposed translation is rejected unless it:

1. Names exact folios, image IDs, transcription files, and versions.
2. Round-trips the source without silent glyph changes.
3. Freezes substitution, null, homophone, reordering, and tokenization rules before held-out tests.
4. Reports full-folio coverage, exceptions, and degrees of freedom.
5. Demonstrates stratified robustness across at least one held-out hand, Currier variety, and illustration section without retuning, where sample size permits.
6. Explains glyph slots, low entropy, line/paragraph effects, cross-space dependencies, and page-level structure together.
7. Beats shuffled, random-dictionary, frequency-only, and, where applicable, self-copying baselines under equal search budgets.
8. Produces grammatical literal readings of complete held-out lines and independently checkable semantic predictions.
9. Uses historically appropriate target-language data; modern dictionary resemblance is not evidence.
