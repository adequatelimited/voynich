# H004-B-v2: teacher-forced contextual comparator

> Retrospective conditional model check only. This is not a free-running Markov test, a copy/edit identification, or a translation.

- Source SHA-256: `bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc`
- H004-A report SHA-256: `53caf3b04298838e102ddf4ac169a756e471b965de42abb8452b725ff042e469`
- Reserved pages / targets: 33 / 2072
- Replicates per order / master seed: 9999 / 4004
- Both comparators valid: `no`

| Order | Metric | Observed | Analytic expectation | Delta | Tail area | Positive pages | D95 |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | C: exact or one edit | 0.3062 | 0.2981 | +0.0081 | 0.2174 | 20 | +0.0252 |
| 1 | U: one edit, no exact | 0.2281 | 0.1709 | +0.0572 | 0.0001 | 29 | +0.0713 |
| 2 | C: exact or one edit | 0.3062 | 0.2953 | +0.0109 | 0.1379 | 20 | +0.0269 |
| 2 | U: one edit, no exact | 0.2281 | 0.1651 | +0.0631 | 0.0001 | 29 | +0.0759 |

## Comparator validity

- Order 1: `invalid`; context support overall/A/B = 99.95%/100.00%/99.94%; baseline UNK mass overall/A/B = 21.88%/28.88%/19.89%; page-equal predictive log lift = -1.0242.
- Order 2: `invalid`; context support overall/A/B = 49.52%/48.47%/49.81%; baseline UNK mass overall/A/B = 21.88%/28.88%/19.89%; page-equal predictive log lift = -1.3741.

## Disposition

inconclusive: both contextual comparators failed validity.

This result does not reject copying as a possible cause and does not test a free-running Markov generator.
