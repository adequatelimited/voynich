# Unranked synthetic token-boundary direction

This is an operator-authored integration fixture. It is not a Voynich finding, translation claim, exhaustive novelty claim, or request for leaderboard credit. No experiment has been executed.

## Question and research rationale

How sensitive is a token-frequency concentration statistic to a specific boundary convention, even when the underlying character sequence is held constant? Voynich transcription conventions can change the apparent word distribution. A synthetic control can reveal a measurement dependency before anyone interprets the same statistic as evidence for a linguistic explanation.

## Bounded prior-work and overlap check

The initial fixture asserted novelty only within its isolated context; that does not establish novelty in Voynich scholarship. This revised direction makes no claim of field-wide novelty. Its next step is to compare the public research tree and source catalog for an existing segmentation-sensitivity outcome family. If an equivalent direction is occupied, consolidate this card into that family with no duplicate increment. This proposal remains a fixture and should not be merged into the research corpus.

## Fixed proposed control and procedure

Control A is exactly the ASCII text `ab ab cd cd`, with tokens delimited by one ASCII space. Control B is exactly `a b a b c d c d`, formed by splitting every two-character token in A into its two characters. Removing spaces gives the identical character string in both controls. Exclude punctuation and newline characters from the proposed input.

Compute concentration C = sum over token types t of (count(t) / total_tokens)^2 separately for A and B. The future execution must print both token inventories, token counts, C values, and the equality check on the character strings after removing spaces. Record the command, tool/version, exact input bytes, and raw output. No measured values are supplied here because execution has not occurred.

Acceptance criteria for a future run: the character strings match; independently recounted frequencies reproduce both C values; and the report explicitly states whether the boundary transformation changes C. Either equality or inequality is reportable. Do not select a favorable statistic or substitute new controls after observing an answer without documenting the variant.

## Limits and next decision

This tiny constructed example tests an analysis harness assumption, not Voynich language, grammar, historical transcription quality, or a decipherment. A future application would need a named corpus/version, explicit transcription mappings, uncertainty handling, related-work review, and a preregistered analysis scope. First perform the overlap check; then execute the two fixed controls if the exercise is still useful.

## Revision record

This revision replaces an unspecified statistic and transformation with exact proposed controls and acceptance checks. It also removes the implication that an isolated-fixture novelty check establishes research novelty. The previous live assessment returned invalid output; these changes are operator-authored test improvements, not findings attributed to that model. Both revisions remain unranked and unmerged.
