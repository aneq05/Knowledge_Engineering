# Student BN - Zestaw k26 – wariant modelu student

## 1. Dataset and input validation

Training rows: **2000**; complete training rows: **367**; test rows: **2000**. The test file is used ONLY for evaluation.

| Variable | Meaning | States | Missing (train) |
|---|---|---|---:|
| D | trudność kursu | Easy, Hard | 0.0% |
| I | zdolności studenta | Dumb, Intelligent | 64.5% |
| M | motywacja studenta | Low, High | 10.4% |
| Q | jakość prowadzącego | Low, High | 4.2% |
| E | udział w kursie przygotowawczym | No, Yes | 3.5% |
| G | ocena z kursu | A, B, C | 20.9% |
| S | wynik testu SAT | Bad, Good | 0.0% |
| L | list polecający | Bad, Good | 9.8% |
| B | stypendium naukowe | No, Yes | 13.5% |

## 2. Expert network and MLE

Expert edges: D->G, G->B, G->L, I->G, I->S, M->E, Q->G, S->L.
Largest CPD: **P(G | D, I, Q)**, shape (3, 2, 2, 2), 24 cells.
Unobserved parent configurations: **0**.
pgmpy DiscreteMLE fills a completely unseen parent configuration with a uniform distribution (not with a column of zeros).

| D | I | Q | P(G=A) | P(G=B) | P(G=C) |
|---|---|---|---|---|---|
| Easy | Dumb | Low | 0.49405 | 0.14881 | 0.35714 |
| Easy | Dumb | High | 0.50746 | 0.17910 | 0.31343 |
| Easy | Intelligent | Low | 0.88776 | 0.10204 | 0.01020 |
| Easy | Intelligent | High | 0.87755 | 0.08163 | 0.04082 |
| Hard | Dumb | Low | 0.00000 | 0.05634 | 0.94366 |
| Hard | Dumb | High | 0.00000 | 0.20000 | 0.80000 |
| Hard | Intelligent | Low | 0.27273 | 0.18182 | 0.54545 |
| Hard | Intelligent | High | 0.33333 | 0.19048 | 0.47619 |

## 3. Queries: point evidence and logical events

### MLE: zapytania.txt

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

### MLE: ograniczenia.txt

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

### EM: zapytania.txt

| Query | Answer | P(evidence) |
|---|---|---:|
| `P(G)` | A: 0.38591; B: 0.12077; C: 0.49332 | 1.000000 |
| `P(L)` | Bad: 0.58538; Good: 0.41462 | 1.000000 |
| `P(I)` | Dumb: 0.79012; Intelligent: 0.20988 | 1.000000 |
| `P(B)` | No: 0.61314; Yes: 0.38686 | 1.000000 |
| `P(G \| D==Hard, I==Intelligent)` | A: 0.37029; B: 0.22351; C: 0.40620 | 0.085422 |
| `P(G \| D==Easy, I==Dumb)` | A: 0.51524; B: 0.14688; C: 0.33788 | 0.468540 |
| `P(I \| G==A, S==Good)` | Dumb: 0.12190; Intelligent: 0.87810 | 0.149426 |
| `P(I \| G==C)` | Dumb: 0.92571; Intelligent: 0.07429 | 0.493318 |
| `P(I \| G==C, D==Hard)` | Dumb: 0.89582; Intelligent: 0.10418 | 0.333057 |
| `P(D \| G==C)` | Easy: 0.32486; Hard: 0.67514 | 0.493318 |
| `P(G, L \| S==Good)` | A,Bad: 0.07121; A,Good: 0.51941; B,Bad: 0.11465; B,Good: 0.02606; C,Bad: 0.25699; C,Good: 0.01169 | 0.253000 |
| `P(G \| M==Low)` | A: 0.38591; B: 0.12077; C: 0.49332 | 0.292255 |
| `P(M \| G==A, L==Bad)` | Low: 0.29225; High: 0.70775 | 0.040650 |
| `P(B \| I==Intelligent)` | No: 0.40353; Yes: 0.59647 | 0.209882 |
| `P(I \| B==Yes)` | Dumb: 0.67640; Intelligent: 0.32360 | 0.386859 |
| `P(I \| G==A, L==Bad, M==High)` | Dumb: 0.58555; Intelligent: 0.41445 | 0.028770 |
| `MAP(G)` | G=C (P=0.49332) | 1.000000 |
| `MAP(G \| D==Easy, I==Intelligent)` | G=A (P=0.88636) | 0.124460 |
| `MAP(Q, S \| D==Hard, G==B)` | Q=Low, S=Good (P=0.30119) | 0.039756 |

### EM: ograniczenia.txt

| Query | Answer | P(evidence) |
|---|---|---:|
| `P(I \| M==Low or E==No)` | Dumb: 0.79012; Intelligent: 0.20988 | 0.424853 |
| `P(Q \| not E==No or I==Intelligent)` | Low: 0.69234; High: 0.30766 | 0.691862 |
| `P(D \| atleast(2, G==B, M==Low, I==Intelligent))` | Easy: 0.59394; Hard: 0.40606 | 0.109632 |
| `P(D \| S==Good and (M==Low or I==Dumb))` | Easy: 0.59300; Hard: 0.40700 | 0.115693 |
| `P(I \| not (L==Good or E==No) and D!=Easy)` | Dumb: 0.84967; Intelligent: 0.15033 | 0.211497 |
| `P(E \| I==Intelligent and S==Bad and G in {A, B})` | No: 0.38999; Yes: 0.61001 | 0.013103 |
| `P(E \| atmost(1, B==Yes, D==Hard, S==Good) and I==Intelligent)` | No: 0.38999; Yes: 0.61001 | 0.044882 |
| `P(M \| (G==A and Q==High and L==Bad) or (I==Intelligent and B!=Yes and D==Easy))` | Low: 0.29225; High: 0.70775 | 0.046269 |
| `P(I \| E==No and S==Bad and G in {A, B} and L==Bad and D==Hard and M==High)` | Dumb: 0.91371; Intelligent: 0.08629 | 0.001627 |

## 4. Test metrics and baselines

Natural logarithm, with P(row) clipped from below at 1e-10. For G, all other observed test attributes are treated as evidence.

| Model | Mean log P(row) | P(row)=0 | Accuracy G | Impossible predictor evidence |
|---|---:|---:|---:|---:|
| MLE | -4.84675 | 21 | 0.847 | 0 |
| EM | -4.60958 | 0 | 0.847 | 0 |
| BIC learned | -4.47146 | 6 | 0.866 | 0 |
| Independent | -6.08089 | 0 | 0.498 | 0 |
| Always predict G=C (train majority) | - | - | 0.498 | - |

An edge-free model treats all features as independent; its G prediction is the training-majority baseline. For impossible evidence contexts, the classifier falls back to this same training-majority grade.

## 5. Full-data EM

Completed EM updates: **15**; observed-data log likelihood: **-8746.2103 -> -8464.4474**; non-decreasing: **True**.
EM performs an exact E-step across all compatible latent completions; partially missing rows are not discarded.
This learns parameters under an ignorable-missingness assumption. MNAR mechanisms may bias estimates even after EM.

## 6. BIC structure learning with expert knowledge

Structure search uses only **367 complete TRAIN rows**; the selected DAG is refitted using family-complete rows of all training records.
BIC on the structure-search subset: expert **-1822.5991**, learned **-1731.8316** (delta=+90.7675).
Learned edges: D->G, E->G, E->S, G->B, G->L, I->G, I->S, M->E, S->B.
Added relative to the expert graph: E->G, E->S, S->B.
Removed relative to the expert graph: Q->G, S->L.
Required/forbidden edges and temporal layers constrain the search. A DAG (not a PDAG) is necessary for parameter fitting.

## 7. Reasoning in the expert graph (MLE)

**Predictive (causal-direction) reasoning:** D -> G. P(G=A | D=Easy)=0.6504, P(G=A | D=Hard)=0.1147.
This is observational conditioning, not a measured intervention/do-effect.

**Diagnostic reasoning:** from grade back to aptitude I -> G. P(I=Intelligent | G=A)=0.5858, P(I=Intelligent | G=C)=0.2041.

**Explaining away:** D -> G <- I. Conditioning on G opens the collider.
Without grade: P(D=Hard | I=Dumb)=0.4070, P(D=Hard | I=Intelligent)=0.4070.
With G=A: P(D=Hard | I=Dumb, G=A)=0.0000, P(D=Hard | I=Intelligent, G=A)=0.1844.

### D-separation versus numerical independence

Conditional TV = weighted TV between P(X,Y|Z) and P(X|Z)P(Y|Z). Small numerical TV supports an independence predicted by d-separation; a d-connected pair can still happen to be independent for special CPD parameters.

| X | Y | Condition | D-connected? | Conditional TV |
|---|---|---|---|---:|
| D | I | - | no | 0.00000000 |
| D | I | G | yes | 0.09868400 |
| D | B | G | no | 0.00000000 |
| D | B | - | yes | 0.17704213 |
| G | S | I | no | 0.00000000 |
| Q | M | - | no | 0.00000000 |

## 8. Ancestral sampling versus exact probabilities

| Query | Accepted samples | TV distance |
|---|---:|---:|
| `P(I | M==Low or E==No)` | 8522 | 0.00609 |
| `P(Q | not E==No or I==Intelligent)` | 15294 | 0.00216 |
| `P(D | atleast(2, G==B, M==Low, I==Intelligent))` | 3525 | 0.00174 |

## 9. Notes and limitations

- MLE is unsmoothed. Sparse family configurations can cause zero joint probabilities.
- A larger accuracy does not automatically imply better joint probability calibration.
- Hill climb finds a local BIC optimum and does not prove causal directions from data alone.
- The report includes the cumulative 6-point extension in sections 10 and 11.
