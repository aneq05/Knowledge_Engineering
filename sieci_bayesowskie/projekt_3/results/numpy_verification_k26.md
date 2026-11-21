# k26 - independent NumPy verification (pre-run)

> This file is a numeric cross-check using the specified family-wise MLE and full-data EM formulas. It is not an execution of pgmpy 1.1.2, which could not be installed in this environment. Run `python -m student_bn` after installation to generate the official `results/report.md` including BIC and pgmpy VariableElimination.

## Data

| Metric | Value |
|---|---:|
| Training rows | 2000 |
| Complete training rows | 367 |
| Test rows | 2000 |
| Missing rate D | 0.0% |
| Missing rate I | 64.5% |
| Missing rate M | 10.4% |
| Missing rate Q | 4.2% |
| Missing rate E | 3.5% |
| Missing rate G | 20.9% |
| Missing rate S | 0.0% |
| Missing rate L | 9.8% |
| Missing rate B | 13.5% |

## Test evaluation

| Model | Mean log P(row) | Zero P(row) | G accuracy |
|---|---:|---:|---:|
| MLE | -4.8467 | 21 | 84.650% |
| Full EM | -4.6441 | 0 | 84.700% |
| Independent | -6.0809 | 0 | 49.850% |
| Majority G=C | - | - | 49.850% |

EM: 45 iterations, observed-data log likelihood -8746.210 -> -8464.440.

## MLE: zapytania.txt

| Query | Answer | P(evidence) |
|---|---|---:|
| `P(G)` | A: 0.43237; B: 0.13358; C: 0.43405 | 1.000000 |
| `P(L)` | Bad: 0.54958; Good: 0.45042 | 1.000000 |
| `P(I)` | Dumb: 0.60619; Intelligent: 0.39381 | 1.000000 |
| `P(B)` | No: 0.57826; Yes: 0.42174 | 1.000000 |
| `P(G \| D==Hard, I==Intelligent)` | A: 0.29138; B: 0.18448; C: 0.52414 | 0.160281 |
| `P(G \| D==Easy, I==Dumb)` | A: 0.49818; B: 0.15813; C: 0.34369 | 0.359470 |
| `P(I \| G==A, S==Good)` | Dumb: 0.12810; Intelligent: 0.87190 | 0.282199 |
| `P(I \| G==C)` | Dumb: 0.79589; Intelligent: 0.20411 | 0.434049 |
| `P(I \| G==C, D==Hard)` | Dumb: 0.72539; Intelligent: 0.27461 | 0.305920 |
| `P(D \| G==C)` | Easy: 0.29520; Hard: 0.70480 | 0.434049 |
| `P(G, L \| S==Good)` | A,Bad: 0.06493; A,Good: 0.49396; B,Bad: 0.10415; B,Good: 0.02840; C,Bad: 0.29273; C,Good: 0.01582 | 0.504923 |
| `P(G \| M==Low)` | A: 0.43237; B: 0.13358; C: 0.43405 | 0.292574 |
| `P(M \| G==A, L==Bad)` | Low: 0.29257; High: 0.70743 | 0.046756 |
| `P(B \| I==Intelligent)` | No: 0.43441; Yes: 0.56559 | 0.393812 |
| `P(I \| B==Yes)` | Dumb: 0.47187; Intelligent: 0.52813 | 0.421741 |
| `P(I \| G==A, L==Bad, M==High)` | Dumb: 0.37419; Intelligent: 0.62581 | 0.033076 |
| `MAP(G)` | G=C (P=0.43405) | 1.000000 |
| `MAP(G \| D==Easy, I==Intelligent)` | G=A (P=0.88461) | 0.233530 |
| `MAP(Q, S \| D==Hard, G==B)` | Q=Low, S=Good (P=0.39610) | 0.054378 |

## MLE: ograniczenia.txt

| Query | Answer | P(evidence) |
|---|---|---:|
| `P(I \| M==Low or E==No)` | Dumb: 0.60619; Intelligent: 0.39381 | 0.425361 |
| `P(Q \| not E==No or I==Intelligent)` | Low: 0.69223; High: 0.30777 | 0.763265 |
| `P(D \| atleast(2, G==B, M==Low, I==Intelligent))` | Easy: 0.57309; Hard: 0.42691 | 0.175846 |
| `P(D \| S==Good and (M==Low or I==Dumb))` | Easy: 0.59300; Hard: 0.40700 | 0.234290 |
| `P(I \| not (L==Good or E==No) and D!=Easy)` | Dumb: 0.67595; Intelligent: 0.32405 | 0.203417 |
| `P(E \| I==Intelligent and S==Bad and G in {A, B})` | No: 0.39053; Yes: 0.60947 | 0.008721 |
| `P(E \| atmost(1, B==Yes, D==Hard, S==Good) and I==Intelligent)` | No: 0.39053; Yes: 0.60947 | 0.073166 |
| `P(M \| (G==A and Q==High and L==Bad) or (I==Intelligent and B!=Yes and D==Easy))` | Low: 0.29257; High: 0.70743 | 0.078340 |
| `P(I \| E==No and S==Bad and G in {A, B} and L==Bad and D==Hard and M==High)` | Dumb: 0.94939; Intelligent: 0.05061 | 0.001632 |

## EM: zapytania.txt

| Query | Answer | P(evidence) |
|---|---|---:|
| `P(G)` | A: 0.38590; B: 0.12078; C: 0.49332 | 1.000000 |
| `P(L)` | Bad: 0.58538; Good: 0.41462 | 1.000000 |
| `P(I)` | Dumb: 0.79024; Intelligent: 0.20976 | 1.000000 |
| `P(B)` | No: 0.61314; Yes: 0.38686 | 1.000000 |
| `P(G \| D==Hard, I==Intelligent)` | A: 0.37026; B: 0.22353; C: 0.40621 | 0.085374 |
| `P(G \| D==Easy, I==Dumb)` | A: 0.51530; B: 0.14687; C: 0.33783 | 0.468610 |
| `P(I \| G==A, S==Good)` | Dumb: 0.12192; Intelligent: 0.87808 | 0.149425 |
| `P(I \| G==C)` | Dumb: 0.92574; Intelligent: 0.07426 | 0.493316 |
| `P(I \| G==C, D==Hard)` | Dumb: 0.89587; Intelligent: 0.10413 | 0.333055 |
| `P(D \| G==C)` | Easy: 0.32487; Hard: 0.67513 | 0.493316 |
| `P(G, L \| S==Good)` | A,Bad: 0.07121; A,Good: 0.51941; B,Bad: 0.11466; B,Good: 0.02606; C,Bad: 0.25698; C,Good: 0.01169 | 0.253000 |
| `P(G \| M==Low)` | A: 0.38590; B: 0.12078; C: 0.49332 | 0.292255 |
| `P(M \| G==A, L==Bad)` | Low: 0.29225; High: 0.70775 | 0.040650 |
| `P(B \| I==Intelligent)` | No: 0.40354; Yes: 0.59646 | 0.209764 |
| `P(I \| B==Yes)` | Dumb: 0.67658; Intelligent: 0.32342 | 0.386857 |
| `P(I \| G==A, L==Bad, M==High)` | Dumb: 0.58575; Intelligent: 0.41425 | 0.028770 |
| `MAP(G)` | G=C (P=0.49332) | 1.000000 |
| `MAP(G \| D==Easy, I==Intelligent)` | G=A (P=0.88636) | 0.124390 |
| `MAP(Q, S \| D==Hard, G==B)` | Q=Low, S=Good (P=0.30113) | 0.039774 |

## EM: ograniczenia.txt

| Query | Answer | P(evidence) |
|---|---|---:|
| `P(I \| M==Low or E==No)` | Dumb: 0.79024; Intelligent: 0.20976 | 0.424853 |
| `P(Q \| not E==No or I==Intelligent)` | Low: 0.69234; High: 0.30766 | 0.691816 |
| `P(D \| atleast(2, G==B, M==Low, I==Intelligent))` | Easy: 0.59393; Hard: 0.40607 | 0.109596 |
| `P(D \| S==Good and (M==Low or I==Dumb))` | Easy: 0.59300; Hard: 0.40700 | 0.115693 |
| `P(I \| not (L==Good or E==No) and D!=Easy)` | Dumb: 0.84974; Intelligent: 0.15026 | 0.211501 |
| `P(E \| I==Intelligent and S==Bad and G in {A, B})` | No: 0.38999; Yes: 0.61001 | 0.013006 |
| `P(E \| atmost(1, B==Yes, D==Hard, S==Good) and I==Intelligent)` | No: 0.38999; Yes: 0.61001 | 0.044784 |
| `P(M \| (G==A and Q==High and L==Bad) or (I==Intelligent and B!=Yes and D==Easy))` | Low: 0.29225; High: 0.70775 | 0.046248 |
| `P(I \| E==No and S==Bad and G in {A, B} and L==Bad and D==Hard and M==High)` | Dumb: 0.91440; Intelligent: 0.08560 | 0.001627 |
