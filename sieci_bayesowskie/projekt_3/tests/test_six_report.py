import sys
import numpy as np

from itertools import product
from pathlib import Path

from student_bn.data import load_csv, load_description
from student_bn.evaluation import evaluate_model, majority_grade
from student_bn.joint import StateSpace
from student_bn.learning import EMResult, MultiStartEM
from student_bn.queries import QueryResult, condition_mask, load_queries
from student_bn.report import make_six_point_report
from student_bn.structure import ImputationStep

DATA = Path(__file__).resolve().parents[1] / "data/k26"
sys.path.insert(0, str(Path(__file__).parent))
from test_learning_numeric import reference_mle


def test_report_includes_all_six_point_requested_sections():
    desc = load_description(DATA / "opis.json")
    train = load_csv(DATA / "dane.csv", desc)
    test = load_csv(DATA / "test.csv", desc, complete=True)
    space = StateSpace.from_description(desc)
    model = reference_mle(desc, train, space)
    joint = space.probability_table(model)
    query_list = load_queries(DATA / "zapytania.txt", desc)
    answers = []
    for query in query_list:
        mask = condition_mask(query.condition, space, space.assignments)
        p_condition = joint[mask].sum()
        distribution = (space.marginal(joint * mask, query.targets) / p_condition).flatten()
        configurations = tuple(product(*(desc.states[v] for v in query.targets)))
        chosen = configurations[int(np.argmax(distribution))] if query.kind == "MAP" else None
        answers.append(QueryResult(query, tuple(zip(configurations, distribution)), p_condition, chosen))
    parameters = {"MLE (complete rows)": model, "MLE (families)": model, "EM (5+ starts)": model}
    structures = {"HC (complete, free)": model, "HC (complete, expert)": model,
                  "HC (EM + imputation)": model}
    edges = {name: desc.expert_edges for name in structures}
    baseline = majority_grade(train, desc.states["G"])
    metrics = {name: evaluate_model(m, test, space, fallback_grade=baseline)
               for name, m in {**parameters, **structures}.items()}
    runs = tuple(EMResult(model, (-10000.0, -9000.0), True, seed=i, initialization="random")
                 for i in range(5))
    text = make_six_point_report(
        desc, train, test, space, MultiStartEM(runs, 0), parameters, structures,
        metrics, edges, (ImputationStep(1, desc.expert_edges, runs[0]),),
        {name: answers for name in {**parameters, **structures}},
    )
    for requirement in ("random Dirichlet", "Five or more", "Marginal", "TRAIN observed L",
                        "HC (complete, free)", "HC (complete, expert)", "HC (EM + imputation)",
                        "Markov equivalent", "Final model selection", "Largest changes"):
        assert requirement.lower() in text.lower()
