# H005 pharmaceutical-plant anchor screen

Machine-readable JSON SHA-256: `e9459292e7b7c87464589b07c13845531bb27b427157eb568a1b335c50f5cb1f`

Disposition: **reject H005-v1 as a q15/q19 plant-identity label retrieval route under the frozen ZL/GC source-claim benchmark**

## Boundary

This is a ZL/GC test of a frozen external source-claim universe. It did not
load IT target prose and it has no blinded image gold. Even a statistical
pass cannot by itself license a plant name, species, language, or translation.

## Inventory

- Source pair claims: 35
- Raw fixed-split holdout before query gates: 7 claims on 6 folios (f19, f4, f43, f44, f48, f57)
- Strict ZL/GC query pairs: 17
- Strict physical target folios: 16
- Pharmaceutical source pages: 11
- Holdout pairs: 5
- Holdout folios: f19, f43, f44, f48, f57
- Breadth gate: pass

## Frozen retrieval result

- Selected discovery model: `M1`
- Discovery conservative MRR: M0=0.03910457, M1=0.08535222
- Holdout conservative MRR: 0.33991087
- MRR null mean / delta / p: 0.19643035 / 0.14348052 / 0.05680000
- Holdout top-three fraction: 0.40000000
- Top-three null mean / delta / p: 0.15847585 / 0.24152415 / 0.15920000
- Statistical gate: fail
- Identity-collision gate: fail
- IT robustness authorized: false
- Referential gloss authorized: false

## MRR subgroups

| Dimension | Subgroup | Split | Pairs | Observed MRR | Null mean | Delta | p |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Quire | `q15` | discovery | 3 | 0.12174525 | 0.04729849 | 0.07444676 | 0.06590000 |
| Quire | `q19` | discovery | 9 | 0.07322121 | 0.05939786 | 0.01382335 | 0.28020000 |
| Quire | `q15` | holdout | 3 | 0.55555556 | 0.30097040 | 0.25458515 | 0.04840000 |
| Quire | `q19` | holdout | 2 | 0.01644385 | 0.03962027 | -0.02317642 | 0.81160000 |
| Source strength | `M` | holdout | 2 | 0.09068627 | 0.21705550 | -0.12636923 | 0.91980000 |
| Source strength | `P` | holdout | 1 | 1.00000000 | 0.13443769 | 0.86556231 | 0.03020000 |
| Source strength | `S` | holdout | 2 | 0.25909091 | 0.20680153 | 0.05228938 | 0.23350000 |
| Query form | `ACACKABAG` | holdout | 1 | 1.00000000 | 0.13443769 | 0.86556231 | 0.03020000 |
| Query form | `AQABBA` | holdout | 2 | 0.09068627 | 0.21705550 | -0.12636923 | 0.91980000 |
| Query form | `BACABABA` | holdout | 1 | 0.01818182 | 0.03714374 | -0.01896192 | 0.66550000 |
| Query form | `KAQAB` | holdout | 1 | 0.50000000 | 0.37645931 | 0.12354069 | 0.28260000 |

## Held-out pairs

| Pair | Query family | Target | ZL rank | GC rank | Worse rank |
| --- | --- | --- | ---: | ---: | ---: |
| `q15-f89r1-25-f57r` | `AQABBA` | f57r | 5.0 | 6.0 | 6.0 |
| `q15-f89r1-26-f43v` | `ACACKABAG` | f43v | 1.0 | 1.0 | 1.0 |
| `q15-f89v2-54-f48v` | `KAQAB` | f48v | 2.0 | 2.0 | 2.0 |
| `q19-f99v-95-f44r` | `AQABBA` | f44r | 68.0 | 42.0 | 68.0 |
| `q19-f102v1-240-f19r` | `BACABABA` | f19r | 55.0 | 51.0 | 55.0 |

## Query-form collisions

- `AQABBA` labels distinct target folios: f44, f57.

## Gate checks

- PASS `at_least_12_physical_targets`
- PASS `at_least_16_strict_pairs`
- PASS `at_least_3_pharmaceutical_pages`
- PASS `at_least_5_holdout_pairs`
- PASS `at_least_5_holdout_physical_folios`
- PASS `both_q15_and_q19`
- FAIL `mrr_delta_at_least_0_15`
- FAIL `mrr_p_at_most_0_01`
- FAIL `positive_discovery_and_holdout_direction_in_each_quire`
- FAIL `top_three_fraction_at_least_0_60`
- FAIL `top_three_p_at_most_0_01`

## Interpretation

A favorable page rank would support only a relation between one frozen Lf
form and one claimed depicted entity. The route remains pre-semantic until
the text-blind image benchmark passes. Failures here reject only this frozen
q15/q19 identity-label retrieval route, not every possible label function.
