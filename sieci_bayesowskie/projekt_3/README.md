# Student Bayesian network for dataset k26 (4 and 6 points)

The project implements the 6-point assignment, which also includes the
4-point tasks. The original inputs are in `data/k26/`. The program uses
`test.csv` only for evaluation. The examples below use Python 3.11 and
`pgmpy==1.1.2`.

## Running on Windows with PowerShell

From the project directory, create an environment and install the required
library. Each run writes to its own output directory.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install "pgmpy==1.1.2"
$env:PYTHONHASHSEED = "0"
python -m student_bn --level 4 --output results/local_4_pkt
python -m student_bn --level 6 --output results/local_6_pkt
```

On Linux or macOS, activate the environment with `source .venv/bin/activate`.
Use `PYTHONHASHSEED=0 python -m student_bn --level 6` to launch the program.

Set `PYTHONHASHSEED=0` before starting Python for reproducible tie-breaking
in `HillClimbSearch`. The `--seed` argument controls sampling and the
random EM initializations.

### Options

```powershell
python -m student_bn --level 6 --em-starts 5 --em-iterations 100 --imputation-rounds 2 --seed 42 --samples 20000
```

- `--em-starts` sets the number of random EM initializations on the expert
  graph. The minimum and default are both 5.
- `--em-iterations` limits EM updates per run. The default is 100.
- `--imputation-rounds` sets the number of EM, imputation, and hill-climbing
  rounds. The default is 2.
- `--seed` sets the random seed for EM, imputation, and sampling. The default
  is 42.
- `--samples` sets the number of samples in the report's sampling comparison.
  The default is 20,000. Use `0` to skip this comparison.
- `--dataset` and `--output` set the input and output directories.

## Code layout

```text
projekt_3/
├── data/k26/               # opis.json, dane.csv, test.csv, zapytania.txt, ograniczenia.txt
├── student_bn/
│   ├── __main__.py          # Runs loading, learning, evaluation, and reporting
│   ├── data.py              # Description, Variable, and JSON/CSV validation
│   ├── joint.py             # State encoding, joint distribution, marginalization, sampling
│   ├── learning.py          # DiscreteMLE, custom EM, and random restarts
│   ├── structure.py         # BIC structure learning, posterior imputation, and graph comparisons
│   ├── queries.py           # Probability and MAP queries, VariableElimination, AST validation
│   ├── evaluation.py        # Log-likelihood, accuracy, marginals, and total variation
│   └── report.py            # Markdown report and JSON export
├── tests/                   # Unit tests and optional full integration test
└── results/                 # Saved reports, answers, and numerical cross-checks
```

The 6-point version extends `learning.py`, `__main__.py`, `evaluation.py`,
and `report.py`. It adds `structure.py` for graph learning and reuses the
data, query, and joint-distribution modules. The suite also covers the new
workflow. See the [code walkthrough](OPIS_KODU.md) for a detailed description.

## 6.1 EM with missing data

`learning.fit_em` implements the assignment's pseudocode for variables
with finite discrete state spaces.

1. Initialize each CPD column with a positive random draw from a Dirichlet
   distribution in `"random"` mode or lightly smoothed family-wise MLE in
   `"mle"` mode.
2. In the **E-step**, enumerate the completions compatible with each unique
   observed pattern. Compute `p[h]` as the product of the relevant CPD
   entries and sum over completions to obtain `p_r`. If the pattern occurs
   `count` times, add `count * log(p_r)` to the log-likelihood and
   `count * p[h] / p_r` to the appropriate expected family counts.
3. In the **M-step**, normalize the counts within each parent configuration.
   Use a uniform distribution when its total count is zero.
4. Record the observed-data log-likelihood after each update and check
   that it is non-decreasing within numerical tolerance.
5. Stop when `abs(L_new - L_old) < 1e-6 * number_of_rows` or when the
   iteration limit is reached.
6. `fit_em_multistart` runs at least five random initializations and
   retains the model with the highest final observed-data log-likelihood.

The custom implementation retains partially observed rows. In pgmpy 1.1.2,
`DiscreteEM` discards those rows and treats entirely unobserved columns
as latent variables. The report explains this behavior.

The report compares **complete-case MLE**, **family-wise MLE**, and **EM**
using test log-likelihood, grade prediction accuracy, observed training
log-likelihood, all marginal distributions against empirical frequencies
in `test.csv`, and answers to `zapytania.txt`.

## 6.2 Three structure-learning strategies

All three strategies call `learn_dag` in `structure.py`, using
`HillClimbSearch(scoring_method="bic-d", return_type="dag")`.

| Strategy | Data for BIC | Constraints |
| --- | --- | --- |
| HC (complete, free) | Complete training rows | None |
| HC (complete, expert) | Complete training rows | `ExpertKnowledge` with required edges, forbidden edges, and temporal tiers |
| HC (EM + imputation) | One completed row per original training row | `ExpertKnowledge` |

The third strategy alternates between imputation, structure learning, and
parameter fitting.

```text
model = best EM fit on the expert graph
repeat R times:
    completed_data = sample from P(missing | observed, model)
    # Keep one row per student, so the sample size stays the same.
    new_dag = HillClimbSearch(BIC, completed_data, ExpertKnowledge)
    model = EM(original_incomplete_data, new_dag)
```

All three learned graphs use the same EM procedure for CPD estimation,
with lightly smoothed family-wise MLE initialization and identical
tolerance and iteration limits. The random restarts on the expert graph
in section 6.1 explore sensitivity to local optima.

For each graph, the report lists its edges, additions, removals, and
reversals relative to the expert graph, and its number of free parameters
`sum_X (r_X - 1) * product_parent(r_parent)`. It also reports observed
training log-likelihood, total and mean test log-likelihood, grade prediction
accuracy, and Markov equivalence based on the skeleton and v-structures.
It ranks changes in answers to `zapytania.txt` by total variation distance
between full query distributions and explains the final model choice.

## Output files

The 6-point run writes these files to the selected output directory.

```text
report.md                          # Report covering the 4- and 6-point tasks
answers_mle.json                   # Family-wise MLE, regular and logical queries
answers_em.json                    # Best EM fit, regular and logical queries
answers_mle_complete.json          # Complete-case MLE
answers_structure_free.json        # BIC structure learned without constraints
answers_structure_expert.json      # BIC structure learned with constraints
answers_structure_em_imputed.json  # BIC structure learned from imputed data
```

See the saved [4-point report](results/4_pkt/report.md) and
[6-point report](results/6_pkt/report.md) for the full pgmpy results.
The [NumPy cross-check](results/level6_numeric_validation.md) independently
checks numerical results for parameter estimation.

## Tests and limitations

```powershell
python -m pip install pytest
python -m pytest -q
```

The suite covers input validation, AST handling, EM on dataset k26,
five random starts, log-likelihood monotonicity, CPD axis alignment,
conditional imputation, and graph comparisons. Integration tests use pgmpy.

Missingness mechanisms (MCAR, MAR, and MNAR) affect the interpretation of the
results. EM estimates can remain biased under MNAR. Fit and BIC measure
statistical properties of the model, while causal direction requires
additional evidence. The structure-learning strategies use different data
(367 complete rows or 2,000 imputed rows), so their BIC scores are relative
to the observations used by each search.

### Full integration test with pgmpy

The full pipeline test is opt-in and runs the BIC structure-learning
strategies.

```powershell
$env:RUN_FULL_INTEGRATION = "1"
python -m pytest -q tests/test_full_pipeline.py
```

For the full experiment, run `python -m student_bn --level 6` with the
default limit of 100 EM updates.
