# Worked replication reports

[Transliteration inventory counts](transliteration-counts.json) reproduces a narrow, useful part of [Zandbergen's published version table](https://www.voynich.nu/transcr.html): both ZL and GC locus counts and explicit paragraph-start counts match. The source table's STA1 character counts and all word-count conventions are outside this reconstruction; the report is **partial**, and matching counts do not verify transcription accuracy.

[Conditional entropy](entropy.json) is a **partial reconstruction** of the kind of diagnostic studied by [Lindemann and Bowern](https://arxiv.org/abs/2010.14697v2). The actual local suite uses ZL3b, a fixed English prose prefix and clearly labeled controls, with full encoding and estimator definitions. It does not reproduce the original study's multilingual/historical corpora, exact figures or alternate glyph-composition experiments.

Run `python tools/research/verify_replications.py` to regenerate the narrow actual verification receipt. The complete baseline outputs remain the evidence for computed values. Changes in source bytes or outputs fail their checks; the receipt is an ordinary local execution record, not an official grader or authority signature.

Both reports were produced by the AI-assisted launch implementation. Their code is original, but no independent person has completed a clean-checkout reproduction. That launch gate remains open. A same-author rerun or a second AI persona does not close it.

A [fresh-interpreter verification](clean-environment-check.json) subsequently reproduced all three variants with identical scientific outputs, excluding measured CPU time, using a new Python 3.14 virtual environment without installed packages. All validation run manifests and raw outputs are retained under [experiments/runs/clean-env-verification-v1](../../experiments/runs/clean-env-verification-v1). This was the same implementation, machine and AI-assisted operator; it demonstrates environment reproducibility but does not replace independent human validation.
