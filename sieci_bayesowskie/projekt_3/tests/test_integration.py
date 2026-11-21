import numpy as np
import pytest

from pathlib import Path
from itertools import product

pytest.importorskip("pgmpy")

from student_bn.data import load_csv, load_description
from student_bn.joint import StateSpace
from pgmpy.inference import VariableElimination
from student_bn.learning import fit_em, fit_mle
from student_bn.queries import load_queries, solve_query

DATA = Path(__file__).resolve().parents[1] / "data/k26"


def test_mle_joint_normalization_and_ve_agreement():
    desc = load_description(DATA / "opis.json")
    train = load_csv(DATA / "dane.csv", desc)
    model = fit_mle(desc, train)
    space = StateSpace.from_description(desc)
    joint = space.probability_table(model)
    assert np.isclose(joint.sum(), 1)
    full = VariableElimination(model).query(list(space.variables), show_progress=False)
    expected = [full.get_value(**dict(zip(space.variables, labels)))
                for labels in product(*(space.states[v] for v in space.variables))]
    np.testing.assert_allclose(joint, expected, atol=1e-12)
    assert all(np.isclose(cpd.values.sum(axis=0).ravel(), 1).all() for cpd in model.get_cpds())
    for query in load_queries(DATA / "zapytania.txt", desc)[:9]:
        result = solve_query(query, model, space, joint)
        assert np.isclose(sum(p for _, p in result.values), 1)


def test_em_uses_all_rows_and_likelihood_is_monotone():
    desc = load_description(DATA / "opis.json")
    train = load_csv(DATA / "dane.csv", desc)
    mle = fit_mle(desc, train)
    result = fit_em(desc, train, mle, max_iter=8)
    history = result.observed_log_likelihood
    assert len(history) == 9
    assert all(after >= before - 1e-7 for before, after in zip(history, history[1:]))
    result.model.check_model()
