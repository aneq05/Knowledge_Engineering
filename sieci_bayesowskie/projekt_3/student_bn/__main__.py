from __future__ import annotations

import argparse
import sys

from pathlib import Path
from pgmpy.inference import VariableElimination

from .data import load_csv, load_description
from .evaluation import evaluate_model, majority_accuracy, majority_grade, sampling_comparison
from .joint import StateSpace
from .learning import fit_em, fit_em_multistart, fit_mle
from .queries import load_queries, solve_query
from .report import make_report, make_six_point_report, save_answers
from .structure import iterative_structure_learning, learn_bic_structure, learn_dag


def run(
    dataset: Path,
    output: Path,
    *,
    level: int = 6,
    em_iterations: int = 100,
    em_starts: int = 5,
    imputation_rounds: int = 2,
    samples: int = 20000,
    seed: int = 42,
) -> Path:
    description = load_description(dataset / "opis.json")
    train = load_csv(dataset / "dane.csv", description)
    test = load_csv(dataset / "test.csv", description, complete=True)
    queries = load_queries(dataset / "zapytania.txt", description)
    advanced = load_queries(dataset / "ograniczenia.txt", description, advanced=True)
    space = StateSpace.from_description(description)

    # 4-point solution: the original expert model and its baselines.
    mle = fit_mle(description, train)
    independent = fit_mle(description, train, edges=[])
    multistart = (
        fit_em_multistart(description, train, mle, starts=em_starts,
                          max_iter=em_iterations, seed=seed)
        if level == 6 else None
    )
    em = multistart.best if multistart is not None else fit_em(
        description, train, mle, max_iter=em_iterations
    )
    learned = learn_bic_structure(description, train)  # constrained BIC, complete rows
    models = {"MLE": mle, "EM": em.model, "BIC learned": learned.model, "Independent": independent}

    output.mkdir(parents=True, exist_ok=True)
    answers = {}
    for name, model in (("MLE", mle), ("EM", em.model)):
        joint = space.probability_table(model)
        inference = VariableElimination(model)
        regular = [solve_query(query, model, space, joint, inference) for query in queries]
        logical = [solve_query(query, model, space, joint, inference) for query in advanced]
        answers[name] = (regular, logical)
        save_answers(output / f"answers_{name.lower()}.json", regular + logical)

    majority = majority_grade(train, space.states["G"])
    def score(model):
        return evaluate_model(model, test, space, fallback_grade=majority)

    scores = {name: score(model) for name, model in models.items()}
    sampled = sampling_comparison(mle, space, space.probability_table(mle),
                                  advanced[:3], size=samples, seed=seed)
    report = make_report(
        description, train, test, space, models, answers, scores,
        majority, majority_accuracy(test, majority), em, learned, sampled,
    )

    if level == 6:
        # 6.1: compare three different parameter estimators for the SAME expert graph.
        complete_mle = fit_mle(description, train.dropna())
        parameter_models = {
            "MLE (complete rows)": complete_mle,
            "MLE (families)": mle,
            "EM (5+ starts)": em.model,
        }

        # 6.2: three BIC structure-learning variants; same EM fitting for every DAG.
        free_dag = learn_dag(description, train.dropna(), constrained=False)
        imputation_steps = iterative_structure_learning(
            description, train, em.model,
            rounds=imputation_rounds, max_iter=em_iterations, seed=seed,
        )
        structure_edges = {
            "HC (complete, free)": tuple(sorted(free_dag.edges())),
            "HC (complete, expert)": learned.edges,
            "HC (EM + imputation)": imputation_steps[-1].edges,
        }
        structure_models = {
            name: fit_em(
                description, train, fit_mle(description, train, edges=edges),
                max_iter=em_iterations,
            ).model
            for name, edges in list(structure_edges.items())[:2]
        }
        # The last loop iteration already applies exactly the same MLE-initialized EM.
        structure_models["HC (EM + imputation)"] = imputation_steps[-1].em.model
        regular_answers = {
            "MLE (families)": answers["MLE"][0],
            "EM (5+ starts)": answers["EM"][0],
        }
        filenames = {
            "MLE (complete rows)": "answers_mle_complete.json",
            "HC (complete, free)": "answers_structure_free.json",
            "HC (complete, expert)": "answers_structure_expert.json",
            "HC (EM + imputation)": "answers_structure_em_imputed.json",
        }
        for name, model in {"MLE (complete rows)": complete_mle, **structure_models}.items():
            joint = space.probability_table(model)
            infer = VariableElimination(model)
            responses = [solve_query(query, model, space, joint, infer) for query in queries]
            regular_answers[name] = responses
            save_answers(output / filenames[name], responses)

        six_scores = {name: score(model) for name, model in
                      {**parameter_models, **structure_models}.items()}
        report += "\n\n" + make_six_point_report(
            description, train, test, space, multistart, parameter_models,
            structure_models, six_scores, structure_edges, imputation_steps,
            regular_answers,
        )

    path = output / "report.md"
    path.write_text(report, encoding="utf-8")
    return path


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Student BN: 4/6-point analysis with pgmpy 1.1.2")
    parser.add_argument("--dataset", type=Path, default=root / "data/k26")
    parser.add_argument("--output", type=Path, default=root / "results")
    parser.add_argument("--level", choices=(4, 6), type=int, default=6,
                        help="4 = original solution; 6 = full EM/BIC comparison (default)")
    parser.add_argument("--em-iterations", type=int, default=100)
    parser.add_argument("--em-starts", type=int, default=5,
                        help="random EM restarts for expert graph, at least 5")
    parser.add_argument("--imputation-rounds", type=int, default=2)
    parser.add_argument("--samples", type=int, default=20000, help="0 = skip sampling")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    try:
        path = run(args.dataset, args.output, level=args.level,
                   em_iterations=args.em_iterations, em_starts=args.em_starts,
                   imputation_rounds=args.imputation_rounds,
                   samples=args.samples, seed=args.seed)
    except (ValueError, ArithmeticError) as exc:
        print(f"Input/calculation error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    print(f"Report: {path}")
    print(f"Query results: {args.output / 'answers_mle.json'} and other answers_*.json files")


if __name__ == "__main__":
    main()
