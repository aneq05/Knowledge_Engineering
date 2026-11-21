from __future__ import annotations

import json

from itertools import combinations, product
from pathlib import Path

from .data import Description, data_statistics
from .evaluation import conditional_probability, independence_checks
from .joint import StateSpace
from .learning import EMResult, largest_cpd_info
from .structure import StructureResult
from .queries import QueryResult
from .evaluation import marginal_comparison, observed_train_log_likelihood, query_changes
from .structure import edge_changes, markov_equivalent, parameter_count


def _probabilities(result: QueryResult) -> str:
    if result.query.kind == "MAP":
        chosen = dict(zip(result.query.targets, result.maximum))
        probability = next(value for config, value in result.values if config == result.maximum)
        return ", ".join(f"{key}={value}" for key, value in chosen.items()) + f" (P={probability:.5f})"
    return "; ".join(
        f"{','.join(config)}: {probability:.5f}" for config, probability in result.values
    )


def _results_section(name: str, results: list[QueryResult]) -> list[str]:
    lines = [f"### {name}", "", "| Query | Answer | P(evidence) |", "|---|---|---:|"]
    for result in results:
        query_text = result.query.text.replace("|", r"\|")
        lines.append(f"| `{query_text}` | {_probabilities(result)} | {result.event_probability:.6f} |")
    return lines + [""]


def save_answers(path: Path, results: list[QueryResult]) -> None:
    payload = []
    for result in results:
        payload.append(
            {
                "query": result.query.text,
                "line": result.query.line,
                "kind": result.query.kind,
                "P_evidence": result.event_probability,
                "distribution": [
                    {"assignment": dict(zip(result.query.targets, assignment)), "probability": probability}
                    for assignment, probability in result.values
                ],
                "MAP": dict(zip(result.query.targets, result.maximum)) if result.maximum else None,
            }
        )
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def make_report(
    description: Description,
    train,
    test,
    space: StateSpace,
    models: dict[str, object],
    answers: dict[str, tuple[list[QueryResult], list[QueryResult]]],
    scores: dict[str, object],
    majority: str,
    majority_score: float,
    em: EMResult | None,
    learned: StructureResult | None,
    sampling: list[dict],
) -> str:
    stats = data_statistics(train)
    lines = [
        f"# Student BN - {description.name}",
        "",
        "## 1. Dataset and input validation",
        "",
        f"Training rows: **{stats['rows']}**; complete training rows: **{stats['complete_rows']}**; "
        f"test rows: **{len(test)}**. The test file is used ONLY for evaluation.",
        "",
        "| Variable | Meaning | States | Missing (train) |",
        "|---|---|---|---:|",
    ]
    for var, definition in description.variables.items():
        lines.append(f"| {var} | {definition.description} | {', '.join(definition.states)} | {stats['missing_rate'][var]:.1%} |")

    mle = models["MLE"]
    info = largest_cpd_info(description, mle, train)
    cpd = mle.get_cpds(info["variable"])
    lines += [
        "",
        "## 2. Expert network and MLE",
        "",
        "Expert edges: " + ", ".join(f"{a}->{b}" for a, b in description.expert_edges) + ".",
        f"Largest CPD: **P({info['variable']} | {', '.join(info['parents'])})**, "
        f"shape {info['shape']}, {info['entries']} cells.",
        f"Unobserved parent configurations: **{info['unseen_parent_configurations']}**.",
        "pgmpy DiscreteMLE fills a completely unseen parent configuration with a uniform distribution "
        "(not with a column of zeros).",
        "",
    ]
    if info["unseen_example"]:
        lines.append(f"First unseen configuration: {info['unseen_example']}, CPD={info['unseen_cpd']}.")
    parents = info["parents"]
    lines.append("| " + " | ".join([*parents, *(f"P({info['variable']}={state})" for state in info["states"])]) + " |")
    lines.append("|" + "---|" * (len(parents) + len(info["states"])))
    for states in product(*(description.states[p] for p in parents)):
        evidence = dict(zip(parents, states))
        probabilities = [cpd.get_value(**{info["variable"]: s, **evidence}) for s in info["states"]]
        lines.append("| " + " | ".join([*states, *(f"{value:.5f}" for value in probabilities)]) + " |")
    lines.append("")

    lines += ["## 3. Queries: point evidence and logical events", ""]
    for name, (regular, advanced) in answers.items():
        lines.extend(_results_section(f"{name}: zapytania.txt", regular))
        lines.extend(_results_section(f"{name}: ograniczenia.txt", advanced))

    lines += [
        "## 4. Test metrics and baselines",
        "",
        "Natural logarithm, with P(row) clipped from below at 1e-10. "
        "For G, all other observed test attributes are treated as evidence.",
        "",
        "| Model | Mean log P(row) | P(row)=0 | Accuracy G | Impossible predictor evidence |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, metric in scores.items():
        lines.append(
            f"| {name} | {metric.mean_log_probability:.5f} | {metric.zero_probability_rows} | "
            f"{metric.grade_accuracy:.3f} | {metric.impossible_grade_contexts} |"
        )
    lines += [
        f"| Always predict G={majority} (train majority) | - | - | {majority_score:.3f} | - |",
        "",
        "An edge-free model treats all features as independent; its G prediction is the "
        "training-majority baseline. For impossible evidence contexts, the classifier falls back "
        "to this same training-majority grade.",
        "",
    ]

    if em:
        history = em.observed_log_likelihood
        nondecreasing = all(b >= a - 1e-7 for a, b in zip(history, history[1:]))
        lines += [
            "## 5. Full-data EM",
            "",
            f"Completed EM updates: **{len(history)-1}**; observed-data log likelihood: "
            f"**{history[0]:.4f} -> {history[-1]:.4f}**; "
            f"non-decreasing: **{nondecreasing}**.",
            "EM performs an exact E-step across all compatible latent completions; "
            "partially missing rows are not discarded.",
            "This learns parameters under an ignorable-missingness assumption. "
            "MNAR mechanisms may bias estimates even after EM.",
            "",
        ]

    if learned:
        expert = set(description.expert_edges)
        detected = set(learned.edges)
        lines += [
            "## 6. BIC structure learning with expert knowledge",
            "",
            f"Structure search uses only **{learned.complete_rows} complete TRAIN rows**; "
            "the selected DAG is refitted using family-complete rows of all training records.",
            f"BIC on the structure-search subset: expert **{learned.expert_bic:.4f}**, "
            f"learned **{learned.bic:.4f}** (delta={learned.bic - learned.expert_bic:+.4f}).",
            "Learned edges: " + ", ".join(f"{a}->{b}" for a, b in learned.edges) + ".",
            "Added relative to the expert graph: " + (", ".join(f"{a}->{b}" for a, b in sorted(detected - expert)) or "none") + ".",
            "Removed relative to the expert graph: " + (", ".join(f"{a}->{b}" for a, b in sorted(expert - detected)) or "none") + ".",
            "Required/forbidden edges and temporal layers constrain the search. "
            "A DAG (not a PDAG) is necessary for parameter fitting.",
            "",
        ]

    joint = space.probability_table(mle)
    p = lambda v, s, e=None: conditional_probability(space, joint, v, s, e)
    lines += [
        "## 7. Reasoning in the expert graph (MLE)",
        "",
        "**Predictive (causal-direction) reasoning:** D -> G. "
        f"P(G=A | D=Easy)={p('G','A',{'D':'Easy'}):.4f}, "
        f"P(G=A | D=Hard)={p('G','A',{'D':'Hard'}):.4f}.",
        "This is observational conditioning, not a measured intervention/do-effect.",
        "",
        "**Diagnostic reasoning:** from grade back to aptitude I -> G. "
        f"P(I=Intelligent | G=A)={p('I','Intelligent',{'G':'A'}):.4f}, "
        f"P(I=Intelligent | G=C)={p('I','Intelligent',{'G':'C'}):.4f}.",
        "",
        "**Explaining away:** D -> G <- I. Conditioning on G opens the collider.",
        f"Without grade: P(D=Hard | I=Dumb)={p('D','Hard',{'I':'Dumb'}):.4f}, "
        f"P(D=Hard | I=Intelligent)={p('D','Hard',{'I':'Intelligent'}):.4f}.",
        f"With G=A: P(D=Hard | I=Dumb, G=A)="
        f"{p('D','Hard',{'I':'Dumb','G':'A'}):.4f}, "
        f"P(D=Hard | I=Intelligent, G=A)="
        f"{p('D','Hard',{'I':'Intelligent','G':'A'}):.4f}.",
        "",
        "### D-separation versus numerical independence",
        "",
        "Conditional TV = weighted TV between P(X,Y|Z) and P(X|Z)P(Y|Z). "
        "Small numerical TV supports an independence predicted by d-separation; "
        "a d-connected pair can still happen to be independent for special CPD parameters.",
        "",
        "| X | Y | Condition | D-connected? | Conditional TV |",
        "|---|---|---|---|---:|",
    ]
    for row in independence_checks(mle, space, joint):
        lines.append(
            f"| {row['X']} | {row['Y']} | {row['given'] or '-'} | "
            f"{'yes' if row['d_connected'] else 'no'} | {row['conditional_tv']:.8f} |"
        )
    lines.append("")

    if sampling:
        lines += ["## 8. Ancestral sampling versus exact probabilities", "",
                  "| Query | Accepted samples | TV distance |", "|---|---:|---:|"]
        for entry in sampling:
            tv = f"{entry['tv']:.5f}" if entry["tv"] is not None else "n/a"
            lines.append(f"| `{entry['query']}` | {entry['accepted']} | {tv} |")
        lines.append("")

    lines += [
        "## 9. Notes and limitations",
        "",
        "- MLE is unsmoothed. Sparse family configurations can cause zero joint probabilities.",
        "- A larger accuracy does not automatically imply better joint probability calibration.",
        "- Hill climb finds a local BIC optimum and does not prove causal directions from data alone.",
        "- The report includes the cumulative 6-point extension in sections 10 and 11.",
        "",
    ]
    return "\n".join(lines)


def make_six_point_report(
    description: Description,
    train,
    test,
    space: StateSpace,
    multistart,
    comparison_models: dict[str, object],
    structure_models: dict[str, object],
    scores: dict[str, object],
    structure_edges: dict[str, tuple[tuple[str, str], ...]],
    imputation_steps,
    regular_answers: dict[str, list[QueryResult]],
) -> str:
    expert_edges = tuple(description.expert_edges)

    lines = [
        "## 10. Six-point extension: EM on incomplete data",
        "",
        "**Why not `DiscreteEM`?** In pgmpy 1.1.2 it discards partially observed "
        "rows (unless entire columns are latent). The custom `fit_em` instead enumerates "
        "compatible missing-state completions for every unique observed pattern; no "
        "partially filled training record is discarded.",
        "",
        "**Pseudocode in the implementation:** random normalized CPDs → E-step "
        "(joint probability for each compatible completion; posterior fractional "
        "family counts; observed log likelihood L) → M-step (normalize counts or "
        "uniform for an unobserved family) → repeat until "
        "`abs(L_new-L_old) < 1e-6 * N` or the iteration limit. "
        "Repeated training rows are grouped and weighted by frequency.",
        "",
        f"Five or more **random Dirichlet initializations**: {len(multistart.runs)}. "
        f"Selected run **{multistart.best_index + 1}** by maximum observed TRAIN likelihood.",
        "",
        "| Start | Seed | Initial L | Final L | Updates | Converged? | Monotone? |",
        "|---:|---:|---:|---:|---:|:---:|:---:|",
    ]
    for i, run in enumerate(multistart.runs, 1):
        history = run.observed_log_likelihood
        monotonic = all(b >= a - 1e-7 for a, b in zip(history, history[1:]))
        lines.append(
            f"| {i}{' **(best)**' if i - 1 == multistart.best_index else ''} | {run.seed} | "
            f"{history[0]:.4f} | {history[-1]:.4f} | {len(history)-1} | "
            f"{'yes' if run.converged else 'limit'} | {'yes' if monotonic else '**NO**'} |"
        )
    lines += [
        "",
        "### Three parameter-estimation methods for the expert graph",
        "",
        "- **MLE (complete rows):** discard every TRAIN row containing any missing value, then estimate all CPDs.",
        "- **MLE (families):** each CPD uses rows where only its own family is complete.",
        "- **EM (best of random starts):** all TRAIN rows contribute fractional expected counts.",
        "",
        "TRAIN L is `sum(log P(observed attributes in row))`, with missing "
        "attributes marginalized out (not filled with their actual test values). "
        "TEST L is the sum of log probabilities of fully observed test rows "
        "with the 1e-10 floor specified in the assignment.",
        "",
        "| Estimator | TRAIN observed L | TEST L (clipped) | TEST mean log P(row) | TEST zero rows | TEST accuracy G |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, model in comparison_models.items():
        score = scores[name]
        train_l = observed_train_log_likelihood(model, train, space)
        lines.append(
            f"| {name} | {train_l:.4f} | {score.mean_log_probability * len(test):.4f} | "
            f"{score.mean_log_probability:.5f} | {score.zero_probability_rows} | "
            f"{score.grade_accuracy:.3f} |"
        )

    lines += [
        "",
        "The negative-infinity TRAIN likelihood for unsmoothed MLE is a valid "
        "outcome if even one observed training pattern has model probability zero. "
        "EM is initialized with strictly positive CPDs to avoid impossible "
        "observations during the E-step.",
        "",
        "### Marginal probabilities versus empirical frequencies in test.csv",
        "",
        "The TEST frequencies are reference values for **evaluation only**; "
        "no test row is used for MLE, EM, imputation, or BIC.",
        "",
        "| Variable | State | Test frequency | Complete MLE | Family MLE | EM (best) |",
        "|---|---|---:|---:|---:|---:|",
    ]
    comparison = marginal_comparison(comparison_models, test, space)
    cc, fam, em_name = tuple(comparison_models)
    for item in comparison:
        probs = item["models"]
        lines.append(
            f"| {item['variable']} | {item['state']} | {item['test']:.4f} | "
            f"{probs[cc]:.4f} | {probs[fam]:.4f} | {probs[em_name]:.4f} |"
        )
    lines += [
        "",
        "### Comparison of queries from zapytania.txt",
        "",
        "Results for family MLE and EM appear in section 3 above. "
        "These are the additional answers for **complete-row MLE**:",
        "",
    ]
    lines.extend(_results_section(cc, regular_answers[cc]))
    lines += [
        "**Interpretation.** Complete-case MLE uses fewer records and may be "
        "biased if the missingness mechanism depends on measured attributes. "
        "Family-wise MLE uses more observations per local CPD, but distinct CPDs "
        "can be learned from different row subsets. EM uses the joint "
        "conditional-dependence model to propagate uncertainty into missing "
        "variables; its answer depends on initialization and the assumed graph. "
        "For MNAR missingness, even a well-converged EM can remain biased.",
        "",
        "## 11. Six-point extension: three BIC structure-learning methods",
        "",
        "1. **HC (complete, free)**: BIC on complete TRAIN rows, with no constraints.",
        "2. **HC (complete, expert)**: same data, with required/forbidden edges "
        "and temporal layers from opis.json.",
        "3. **HC (EM + imputation)**: start from expert-graph EM, sample exactly "
        "one completion of each partially observed TRAIN row from its posterior; "
        "learn a constrained DAG by BIC; re-estimate CPDs with EM on the "
        "original incomplete TRAIN data; repeat.",
        "",
        "**Common parameter-fitting method:** each of these three learned "
        "structures is fitted via the same EM algorithm, with an identical "
        "smoothed family-MLE starting rule, tolerance and update limit. "
        "The >=5 random-start requirement is additionally tested on the expert graph "
        "in section 10. No imputed records are replicated: N is unchanged, "
        "so the BIC penalty is not artificially weakened.",
        "",
        "| Structure | Edges | Parameters | TRAIN observed L | TEST L (clipped) | TEST mean log P(row) | Accuracy G |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    expert_em_name = "EM (5+ starts)"
    model = comparison_models[expert_em_name]
    score = scores[expert_em_name]
    lines.append(
        f"| Expert graph (reference) | {len(expert_edges)} | "
        f"{parameter_count(description, expert_edges)} | "
        f"{observed_train_log_likelihood(model, train, space):.4f} | "
        f"{score.mean_log_probability * len(test):.4f} | "
        f"{score.mean_log_probability:.5f} | {score.grade_accuracy:.3f} |"
    )
    for name, model in structure_models.items():
        edges = structure_edges[name]
        score = scores[name]
        lines.append(
            f"| {name} | {len(edges)} | {parameter_count(description, edges)} | "
            f"{observed_train_log_likelihood(model, train, space):.4f} | "
            f"{score.mean_log_probability * len(test):.4f} | "
            f"{score.mean_log_probability:.5f} | {score.grade_accuracy:.3f} |"
        )

    lines += ["", "### Learned edges versus the expert graph", ""]
    edge_text = lambda edges: ", ".join(f"{a}→{b}" for a, b in sorted(edges)) or "none"
    for name, edges in structure_edges.items():
        changes = edge_changes(expert_edges, edges)
        equivalent = markov_equivalent(description.variables, expert_edges, edges)
        lines += [
            f"**{name}:** {edge_text(edges)}.",
            f"Added: {edge_text(changes['added'])}; removed: {edge_text(changes['removed'])}; "
            f"reversed: {edge_text(changes['reversed'])}. "
            f"Markov equivalent to expert: **{'yes' if equivalent else 'no'}**.",
            "",
        ]
    for first, second in combinations(structure_edges, 2):
        same = markov_equivalent(
            description.variables, structure_edges[first], structure_edges[second]
        )
        lines.append(f"- Markov equivalence: {first} vs {second}: {'yes' if same else 'no'}")
    lines += [
        "",
        "Two DAGs are Markov equivalent **only if** they share the undirected "
        "skeleton and all unshielded colliders (v-structures). In that case, "
        "opposing orientations cannot be distinguished from conditional "
        "independences alone. When the skeleton/v-structures differ, a difference "
        "is not explained solely by Markov equivalence. Neither method proves "
        "a causal direction from observational data alone.",
        "",
        "### Iterative imputation trace",
        "",
        "| Round | Graph edges | TRAIN observed L after EM | EM updates |",
        "|---:|---|---:|---:|",
    ]
    for step in imputation_steps:
        lines.append(
            f"| {step.round} | {edge_text(step.edges)} | "
            f"{step.em.observed_log_likelihood[-1]:.4f} | "
            f"{len(step.em.observed_log_likelihood)-1} |"
        )

    lines += [
        "",
        "### Largest changes in answers relative to the expert-graph family MLE",
        "",
        "TV is computed for the **entire joint posterior on query variables**, "
        "not by independently maximizing each target. A change of `P(evidence)` "
        "is also shown. Differences can result from changed adjacency/orientation, "
        "changed CPDs and missing-data treatment.",
        "",
        "| Structure | Query | TV versus expert MLE | ΔP(evidence) |",
        "|---|---|---:|---:|",
    ]
    ref = regular_answers[fam]
    changed = query_changes(
        ref,
        {name: regular_answers[name] for name in structure_models},
        limit=12,
    )
    for item in changed:
        query_label = item["query"].replace("|", r"\|")
        lines.append(
            f"| {item['model']} | `{query_label}` | "
            f"{item['tv']:.5f} | {item['evidence_delta']:+.5f} |"
        )
    # Concrete explanations based on each query's target/evidence and the actual edge changes.
    lines += ["", "### Why these particular query answers changed", ""]
    by_query = {result.query.text: result.query for result in ref}
    for item in changed[:5]:
        query = by_query[item["query"]]
        touched = set(query.targets) | set(query.evidence or ())
        differences = edge_changes(expert_edges, structure_edges[item["model"]])
        near = [(kind, a, b) for kind, edges in differences.items()
                for a, b in edges if a in touched or b in touched]
        description_of_edges = ", ".join(f"{kind} {a}→{b}" for kind, a, b in near)
        if not description_of_edges:
            description_of_edges = "no directly incident edge changes; indirect paths or CPD estimation differ"
        lines.append(
            f"- `{query.text}` in **{item['model']}** (TV={item['tv']:.4f}): "
            f"changes near its targets/evidence: {description_of_edges}. "
            "This identifies plausible paths of influence, not proof of causation."
        )

    lines += [
        "",
        "**How to explain the largest shifts:** inspect the added/removed/reversed "
        "edges immediately above, especially those touching the query targets "
        "or evidence variables. A new path can create a statistical dependence; "
        "a removed path can suppress it. A mere change of direction in an "
        "equivalent DAG need not change the distribution if parameters are fully "
        "re-estimated from complete data; here incomplete observations and local "
        "optima introduce additional differences.",
        "",
    ]

    candidates = {em_name: comparison_models[em_name], **structure_models}
    winner = max(candidates, key=lambda name: scores[name].mean_log_probability)
    winner_score = scores[winner]
    lines += [
        "### Final model selection",
        "",
        f"**Selected for this comparison: {winner}.** It has the best held-out "
        f"mean log P(row) ({winner_score.mean_log_probability:.5f}) among the "
        "expert EM and the three learned-graph EM models. Its G accuracy "
        f"is {winner_score.grade_accuracy:.3f}. The test set was used **only** "
        "to compare already fitted models; no structure or CPD was fitted "
        "to the test rows. A formal deployment pipeline should reserve a "
        "separate validation set for model selection and keep the test set "
        "untouched until the final evaluation.",
        "",
    ]
    return "\n".join(lines)
