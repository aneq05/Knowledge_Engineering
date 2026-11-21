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
| `P(I \| G==C)` | Dumb: 0.92570; Intelligent: 0.07430 | 0.493318 |
| `P(I \| G==C, D==Hard)` | Dumb: 0.89582; Intelligent: 0.10418 | 0.333057 |
| `P(D \| G==C)` | Easy: 0.32486; Hard: 0.67514 | 0.493318 |
| `P(G, L \| S==Good)` | A,Bad: 0.07121; A,Good: 0.51941; B,Bad: 0.11465; B,Good: 0.02606; C,Bad: 0.25699; C,Good: 0.01169 | 0.253000 |
| `P(G \| M==Low)` | A: 0.38591; B: 0.12077; C: 0.49332 | 0.292255 |
| `P(M \| G==A, L==Bad)` | Low: 0.29225; High: 0.70775 | 0.040650 |
| `P(B \| I==Intelligent)` | No: 0.40353; Yes: 0.59647 | 0.209883 |
| `P(I \| B==Yes)` | Dumb: 0.67640; Intelligent: 0.32360 | 0.386859 |
| `P(I \| G==A, L==Bad, M==High)` | Dumb: 0.58555; Intelligent: 0.41445 | 0.028770 |
| `MAP(G)` | G=C (P=0.49332) | 1.000000 |
| `MAP(G \| D==Easy, I==Intelligent)` | G=A (P=0.88636) | 0.124460 |
| `MAP(Q, S \| D==Hard, G==B)` | Q=Low, S=Good (P=0.30118) | 0.039758 |

### EM: ograniczenia.txt

| Query | Answer | P(evidence) |
|---|---|---:|
| `P(I \| M==Low or E==No)` | Dumb: 0.79012; Intelligent: 0.20988 | 0.424853 |
| `P(Q \| not E==No or I==Intelligent)` | Low: 0.69234; High: 0.30766 | 0.691862 |
| `P(D \| atleast(2, G==B, M==Low, I==Intelligent))` | Easy: 0.59394; Hard: 0.40606 | 0.109633 |
| `P(D \| S==Good and (M==Low or I==Dumb))` | Easy: 0.59300; Hard: 0.40700 | 0.115693 |
| `P(I \| not (L==Good or E==No) and D!=Easy)` | Dumb: 0.84967; Intelligent: 0.15033 | 0.211498 |
| `P(E \| I==Intelligent and S==Bad and G in {A, B})` | No: 0.38999; Yes: 0.61001 | 0.013104 |
| `P(E \| atmost(1, B==Yes, D==Hard, S==Good) and I==Intelligent)` | No: 0.38999; Yes: 0.61001 | 0.044883 |
| `P(M \| (G==A and Q==High and L==Bad) or (I==Intelligent and B!=Yes and D==Easy))` | Low: 0.29225; High: 0.70775 | 0.046269 |
| `P(I \| E==No and S==Bad and G in {A, B} and L==Bad and D==Hard and M==High)` | Dumb: 0.91372; Intelligent: 0.08628 | 0.001627 |

## 4. Test metrics and baselines

Natural logarithm, with P(row) clipped from below at 1e-10. For G, all other observed test attributes are treated as evidence.

| Model | Mean log P(row) | P(row)=0 | Accuracy G | Impossible predictor evidence |
|---|---:|---:|---:|---:|
| MLE | -4.84675 | 21 | 0.847 | 0 |
| EM | -4.61050 | 0 | 0.847 | 0 |
| BIC learned | -4.47146 | 6 | 0.866 | 0 |
| Independent | -6.08089 | 0 | 0.498 | 0 |
| Always predict G=C (train majority) | - | - | 0.498 | - |

An edge-free model treats all features as independent; its G prediction is the training-majority baseline. For impossible evidence contexts, the classifier falls back to this same training-majority grade.

## 5. Full-data EM

Completed EM updates: **27**; observed-data log likelihood: **-14737.2201 -> -8464.4462**; non-decreasing: **True**.
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


## 10. Six-point extension: EM on incomplete data

**Why not `DiscreteEM`?** In pgmpy 1.1.2 it discards partially observed rows (unless entire columns are latent). The custom `fit_em` instead enumerates compatible missing-state completions for every unique observed pattern; no partially filled training record is discarded.

**Pseudocode in the implementation:** random normalized CPDs → E-step (joint probability for each compatible completion; posterior fractional family counts; observed log likelihood L) → M-step (normalize counts or uniform for an unobserved family) → repeat until `abs(L_new-L_old) < 1e-6 * N` or the iteration limit. Repeated training rows are grouped and weighted by frequency.

Five or more **random Dirichlet initializations**: 5. Selected run **4** by maximum observed TRAIN likelihood.

| Start | Seed | Initial L | Final L | Updates | Converged? | Monotone? |
|---:|---:|---:|---:|---:|:---:|:---:|
| 1 | 1662057955 | -14474.1742 | -8464.4469 | 27 | yes | yes |
| 2 | 942484271 | -12326.6715 | -8464.4471 | 28 | yes | yes |
| 3 | 1405681630 | -15374.7537 | -8464.4470 | 31 | yes | yes |
| 4 **(best)** | 191664963 | -14737.2201 | -8464.4462 | 27 | yes | yes |
| 5 | 929893137 | -15104.0558 | -8464.4471 | 29 | yes | yes |

### Three parameter-estimation methods for the expert graph

- **MLE (complete rows):** discard every TRAIN row containing any missing value, then estimate all CPDs.
- **MLE (families):** each CPD uses rows where only its own family is complete.
- **EM (best of random starts):** all TRAIN rows contribute fractional expected counts.

TRAIN L is `sum(log P(observed attributes in row))`, with missing attributes marginalized out (not filled with their actual test values). TEST L is the sum of log probabilities of fully observed test rows with the 1e-10 floor specified in the assignment.

| Estimator | TRAIN observed L | TEST L (clipped) | TEST mean log P(row) | TEST zero rows | TEST accuracy G |
|---|---:|---:|---:|---:|---:|
| MLE (complete rows) | -inf | -9816.9797 | -4.90849 | 24 | 0.831 |
| MLE (families) | -inf | -9693.4904 | -4.84675 | 21 | 0.847 |
| EM (5+ starts) | -8464.4462 | -9221.0051 | -4.61050 | 0 | 0.847 |

The negative-infinity TRAIN likelihood for unsmoothed MLE is a valid outcome if even one observed training pattern has model probability zero. EM is initialized with strictly positive CPDs to avoid impossible observations during the E-step.

### Marginal probabilities versus empirical frequencies in test.csv

The TEST frequencies are reference values for **evaluation only**; no test row is used for MLE, EM, imputation, or BIC.

| Variable | State | Test frequency | Complete MLE | Family MLE | EM (best) |
|---|---|---:|---:|---:|---:|
| D | Easy | 0.6080 | 0.6676 | 0.5930 | 0.5930 |
| D | Hard | 0.3920 | 0.3324 | 0.4070 | 0.4070 |
| I | Dumb | 0.7675 | 0.5777 | 0.6062 | 0.7901 |
| I | Intelligent | 0.2325 | 0.4223 | 0.3938 | 0.2099 |
| M | Low | 0.2980 | 0.2752 | 0.2926 | 0.2923 |
| M | High | 0.7020 | 0.7248 | 0.7074 | 0.7077 |
| Q | Low | 0.7075 | 0.6839 | 0.6922 | 0.6923 |
| Q | High | 0.2925 | 0.3161 | 0.3078 | 0.3077 |
| E | No | 0.4230 | 0.3733 | 0.3905 | 0.3900 |
| E | Yes | 0.5770 | 0.6267 | 0.6095 | 0.6100 |
| G | A | 0.3855 | 0.4798 | 0.4324 | 0.3859 |
| G | B | 0.1160 | 0.1249 | 0.1336 | 0.1208 |
| G | C | 0.4985 | 0.3954 | 0.4340 | 0.4933 |
| S | Bad | 0.7275 | 0.4823 | 0.4951 | 0.7470 |
| S | Good | 0.2725 | 0.5177 | 0.5049 | 0.2530 |
| L | Bad | 0.5700 | 0.5195 | 0.5496 | 0.5854 |
| L | Good | 0.4300 | 0.4805 | 0.4504 | 0.4146 |
| B | No | 0.6070 | 0.4758 | 0.5783 | 0.6131 |
| B | Yes | 0.3930 | 0.5242 | 0.4217 | 0.3869 |

### Comparison of queries from zapytania.txt

Results for family MLE and EM appear in section 3 above. These are the additional answers for **complete-row MLE**:

### MLE (complete rows)

| Query | Answer | P(evidence) |
|---|---|---:|
| `P(G)` | A: 0.47976; B: 0.12486; C: 0.39538 | 1.000000 |
| `P(L)` | Bad: 0.51949; Good: 0.48051 | 1.000000 |
| `P(I)` | Dumb: 0.57766; Intelligent: 0.42234 | 1.000000 |
| `P(B)` | No: 0.47582; Yes: 0.52418 | 1.000000 |
| `P(G \| D==Hard, I==Intelligent)` | A: 0.26900; B: 0.21125; C: 0.51975 | 0.140398 |
| `P(G \| D==Easy, I==Dumb)` | A: 0.48552; B: 0.13480; C: 0.37968 | 0.385629 |
| `P(I \| G==A, S==Good)` | Dumb: 0.10783; Intelligent: 0.89217 | 0.319426 |
| `P(I \| G==C)` | Dumb: 0.79607; Intelligent: 0.20393 | 0.395376 |
| `P(I \| G==C, D==Hard)` | Dumb: 0.69759; Intelligent: 0.30241 | 0.241302 |
| `P(D \| G==C)` | Easy: 0.38969; Hard: 0.61031 | 0.395376 |
| `P(G, L \| S==Good)` | A,Bad: 0.07773; A,Good: 0.53927; B,Bad: 0.08361; B,Good: 0.03583; C,Bad: 0.26356; C,Good: 0.00000 | 0.517711 |
| `P(G \| M==Low)` | A: 0.47976; B: 0.12486; C: 0.39538 | 0.275204 |
| `P(M \| G==A, L==Bad)` | Low: 0.27520; High: 0.72480 | 0.063148 |
| `P(B \| I==Intelligent)` | No: 0.31346; Yes: 0.68654 | 0.422343 |
| `P(I \| B==Yes)` | Dumb: 0.44684; Intelligent: 0.55316 | 0.524182 |
| `P(I \| G==A, L==Bad, M==High)` | Dumb: 0.41436; Intelligent: 0.58564 | 0.045769 |
| `MAP(G)` | G=A (P=0.47976) | 1.000000 |
| `MAP(G \| D==Easy, I==Intelligent)` | G=A (P=0.90360) | 0.281946 |
| `MAP(Q, S \| D==Hard, G==B)` | Q=Low, S=Good (P=0.41623) | 0.053356 |

**Interpretation.** Complete-case MLE uses fewer records and may be biased if the missingness mechanism depends on measured attributes. Family-wise MLE uses more observations per local CPD, but distinct CPDs can be learned from different row subsets. EM uses the joint conditional-dependence model to propagate uncertainty into missing variables; its answer depends on initialization and the assumed graph. For MNAR missingness, even a well-converged EM can remain biased.

## 11. Six-point extension: three BIC structure-learning methods

1. **HC (complete, free)**: BIC on complete TRAIN rows, with no constraints.
2. **HC (complete, expert)**: same data, with required/forbidden edges and temporal layers from opis.json.
3. **HC (EM + imputation)**: start from expert-graph EM, sample exactly one completion of each partially observed TRAIN row from its posterior; learn a constrained DAG by BIC; re-estimate CPDs with EM on the original incomplete TRAIN data; repeat.

**Common parameter-fitting method:** each of these three learned structures is fitted via the same EM algorithm, with an identical smoothed family-MLE starting rule, tolerance and update limit. The >=5 random-start requirement is additionally tested on the expert graph in section 10. No imputed records are replicated: N is unchanged, so the BIC penalty is not artificially weakened.

| Structure | Edges | Parameters | TRAIN observed L | TEST L (clipped) | TEST mean log P(row) | Accuracy G |
|---|---:|---:|---:|---:|---:|---:|
| Expert graph (reference) | 8 | 33 | -8464.4462 | -9221.0051 | -4.61050 | 0.847 |
| HC (complete, free) | 10 | 32 | -8062.7163 | -8750.6425 | -4.37532 | 0.861 |
| HC (complete, expert) | 9 | 35 | -8027.3980 | -8659.7477 | -4.32987 | 0.867 |
| HC (EM + imputation) | 9 | 35 | -8027.3980 | -8659.7477 | -4.32987 | 0.867 |

### Learned edges versus the expert graph

**HC (complete, free):** B→I, B→S, E→D, E→G, G→B, G→D, G→L, I→D, I→S, M→E.
Added: B→I, B→S, E→D, E→G, I→D; removed: I→G, Q→G, S→L; reversed: D→G. Markov equivalent to expert: **no**.

**HC (complete, expert):** D→G, E→G, E→S, G→B, G→L, I→G, I→S, M→E, S→B.
Added: E→G, E→S, S→B; removed: Q→G, S→L; reversed: none. Markov equivalent to expert: **no**.

**HC (EM + imputation):** D→G, E→G, E→S, G→B, G→L, I→G, I→S, M→E, S→B.
Added: E→G, E→S, S→B; removed: Q→G, S→L; reversed: none. Markov equivalent to expert: **no**.

- Markov equivalence: HC (complete, free) vs HC (complete, expert): no
- Markov equivalence: HC (complete, free) vs HC (EM + imputation): no
- Markov equivalence: HC (complete, expert) vs HC (EM + imputation): yes

Two DAGs are Markov equivalent **only if** they share the undirected skeleton and all unshielded colliders (v-structures). In that case, opposing orientations cannot be distinguished from conditional independences alone. When the skeleton/v-structures differ, a difference is not explained solely by Markov equivalence. Neither method proves a causal direction from observational data alone.

### Iterative imputation trace

| Round | Graph edges | TRAIN observed L after EM | EM updates |
|---:|---|---:|---:|
| 1 | D→G, E→G, G→B, G→L, I→G, I→S, M→E, S→B | -8038.7039 | 9 |
| 2 | D→G, E→G, E→S, G→B, G→L, I→G, I→S, M→E, S→B | -8027.3980 | 9 |

### Largest changes in answers relative to the expert-graph family MLE

TV is computed for the **entire joint posterior on query variables**, not by independently maximizing each target. A change of `P(evidence)` is also shown. Differences can result from changed adjacency/orientation, changed CPDs and missing-data treatment.

| Structure | Query | TV versus expert MLE | ΔP(evidence) |
|---|---|---:|---:|
| HC (complete, expert) | `P(I \| G==A, L==Bad, M==High)` | 0.29958 | -0.00013 |
| HC (EM + imputation) | `P(I \| G==A, L==Bad, M==High)` | 0.29958 | -0.00013 |
| HC (complete, free) | `P(I \| G==A, L==Bad, M==High)` | 0.29581 | +0.00019 |
| HC (complete, free) | `P(G \| M==Low)` | 0.27584 | -0.00038 |
| HC (complete, expert) | `P(G \| M==Low)` | 0.27150 | -0.00036 |
| HC (EM + imputation) | `P(G \| M==Low)` | 0.27150 | -0.00036 |
| HC (complete, free) | `MAP(Q, S \| D==Hard, G==B)` | 0.22892 | -0.01696 |
| HC (complete, expert) | `MAP(Q, S \| D==Hard, G==B)` | 0.21118 | -0.01660 |
| HC (EM + imputation) | `MAP(Q, S \| D==Hard, G==B)` | 0.21118 | -0.01660 |
| HC (complete, expert) | `P(B \| I==Intelligent)` | 0.20071 | -0.18446 |
| HC (EM + imputation) | `P(B \| I==Intelligent)` | 0.20071 | -0.18446 |
| HC (complete, free) | `P(I)` | 0.18456 | +0.00000 |

### Why these particular query answers changed

- `P(I | G==A, L==Bad, M==High)` in **HC (complete, expert)** (TV=0.2996): changes near its targets/evidence: added E→G, removed Q→G, removed S→L. This identifies plausible paths of influence, not proof of causation.
- `P(I | G==A, L==Bad, M==High)` in **HC (EM + imputation)** (TV=0.2996): changes near its targets/evidence: added E→G, removed Q→G, removed S→L. This identifies plausible paths of influence, not proof of causation.
- `P(I | G==A, L==Bad, M==High)` in **HC (complete, free)** (TV=0.2958): changes near its targets/evidence: added B→I, added E→G, added I→D, removed I→G, removed Q→G, removed S→L, reversed D→G. This identifies plausible paths of influence, not proof of causation.
- `P(G | M==Low)` in **HC (complete, free)** (TV=0.2758): changes near its targets/evidence: added E→G, removed I→G, removed Q→G, reversed D→G. This identifies plausible paths of influence, not proof of causation.
- `P(G | M==Low)` in **HC (complete, expert)** (TV=0.2715): changes near its targets/evidence: added E→G, removed Q→G. This identifies plausible paths of influence, not proof of causation.

**How to explain the largest shifts:** inspect the added/removed/reversed edges immediately above, especially those touching the query targets or evidence variables. A new path can create a statistical dependence; a removed path can suppress it. A mere change of direction in an equivalent DAG need not change the distribution if parameters are fully re-estimated from complete data; here incomplete observations and local optima introduce additional differences.

### Final model selection

**Selected for this comparison: HC (complete, expert).** It has the best held-out mean log P(row) (-4.32987) among the expert EM and the three learned-graph EM models. Its G accuracy is 0.867. The test set was used **only** to compare already fitted models; no structure or CPD was fitted to the test rows. A formal deployment pipeline should reserve a separate validation set for model selection and keep the test set untouched until the final evaluation.
