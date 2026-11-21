# NumPy-only independent verification — k26, task 6.1

**Limit:** this file validates numerical EM and parameter estimation only. The pgmpy integration, BIC structure learning and full six-point report require installing `pgmpy==1.1.2` locally.

- Training rows: 2000; complete training rows: 367; test rows: 2000
- EM stopping rule: |L_new - L_previous| < 1e-6 × N, or 100 updates.

## EM starts (all log-likelihoods refer to observed TRAIN values)

| Seed | Initial L | Final L | Updates | Monotone? |
|---:|---:|---:|---:|:---:|
| 1662057955 | -14474.17419 | -8464.44690 | 27 | yes |
| 942484271 | -12326.67147 | -8464.44714 | 28 | yes |
| 1405681630 | -15374.75367 | -8464.44700 | 31 | yes |
| 191664963 | -14737.22006 | -8464.44623 | 27 | yes |
| 929893137 | -15104.05579 | -8464.44712 | 29 | yes |

Best seed: **191664963**, final observed TRAIN L = **-8464.44623**.

## Expert-structure parameter estimation

| Model | TRAIN observed log L | TEST sum log P (clipped) | TEST mean log P | G accuracy | Zero test rows |
|---|---:|---:|---:|---:|---:|
| MLE complete | -inf | -9816.9797 | -4.90849 | 0.831 | 24 |
| MLE families | -inf | -9693.4904 | -4.84675 | 0.847 | 21 |
| EM best of 5 | -8464.4462 | -9221.0051 | -4.61050 | 0.847 | 0 |

## P(G) versus test distribution

| State | Test frequency | Complete MLE | Family MLE | EM |
|---|---:|---:|---:|---:|
| A | 0.3855 | 0.4798 | 0.4324 | 0.3859 |
| B | 0.1160 | 0.1249 | 0.1336 | 0.1208 |
| C | 0.4985 | 0.3954 | 0.4340 | 0.4933 |

## Selected P/MAP answers without external inference API

| Query | Model | Values |
|---|---|---|
| `P(G)` | MLE complete | A: 0.4798; B: 0.1249; C: 0.3954 |
| `P(G)` | MLE families | A: 0.4324; B: 0.1336; C: 0.4340 |
| `P(G)` | EM best of 5 | A: 0.3859; B: 0.1208; C: 0.4933 |
| `P(L)` | MLE complete | Bad: 0.5195; Good: 0.4805 |
| `P(L)` | MLE families | Bad: 0.5496; Good: 0.4504 |
| `P(L)` | EM best of 5 | Bad: 0.5854; Good: 0.4146 |
| `P(I)` | MLE complete | Dumb: 0.5777; Intelligent: 0.4223 |
| `P(I)` | MLE families | Dumb: 0.6062; Intelligent: 0.3938 |
| `P(I)` | EM best of 5 | Dumb: 0.7901; Intelligent: 0.2099 |
| `P(B)` | MLE complete | No: 0.4758; Yes: 0.5242 |
| `P(B)` | MLE families | No: 0.5783; Yes: 0.4217 |
| `P(B)` | EM best of 5 | No: 0.6131; Yes: 0.3869 |
| `P(G \| D==Hard, I==Intelligent)` | MLE complete | A: 0.2690; B: 0.2112; C: 0.5198 |
| `P(G \| D==Hard, I==Intelligent)` | MLE families | A: 0.2914; B: 0.1845; C: 0.5241 |
| `P(G \| D==Hard, I==Intelligent)` | EM best of 5 | A: 0.3703; B: 0.2235; C: 0.4062 |
| `P(G \| D==Easy, I==Dumb)` | MLE complete | A: 0.4855; B: 0.1348; C: 0.3797 |
| `P(G \| D==Easy, I==Dumb)` | MLE families | A: 0.4982; B: 0.1581; C: 0.3437 |
| `P(G \| D==Easy, I==Dumb)` | EM best of 5 | A: 0.5152; B: 0.1469; C: 0.3379 |
| `P(I \| G==A, S==Good)` | MLE complete | Dumb: 0.1078; Intelligent: 0.8922 |
| `P(I \| G==A, S==Good)` | MLE families | Dumb: 0.1281; Intelligent: 0.8719 |
| `P(I \| G==A, S==Good)` | EM best of 5 | Dumb: 0.1219; Intelligent: 0.8781 |

**Reminder:** structure-learning results must be generated with the installed pgmpy library by running `python -m student_bn --level 6`.
