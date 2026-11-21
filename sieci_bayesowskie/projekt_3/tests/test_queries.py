import numpy as np
import pytest

from pathlib import Path

from student_bn.data import load_description
from student_bn.joint import StateSpace
from student_bn.queries import condition_mask, load_queries, parse_query

DATA = Path(__file__).resolve().parents[1] / "data/k26"


def test_parse_all_real_queries():
    desc = load_description(DATA / "opis.json")
    basic = load_queries(DATA / "zapytania.txt", desc)
    advanced = load_queries(DATA / "ograniczenia.txt", desc, advanced=True)
    assert len(basic) == 19
    assert len(advanced) == 9
    assert sum(query.kind == "MAP" for query in basic) == 3
    assert all(query.evidence is None for query in advanced)


def test_logical_conditions_are_vectorized_and_correct():
    desc = load_description(DATA / "opis.json")
    space = StateSpace.from_description(desc)
    q = parse_query("P(I | atleast(2, G==B, M==Low, S==Good))", 1, desc, advanced=True)
    result = condition_mask(q.condition, space, space.assignments)
    codes = space.assignments
    expected = (
        (codes[:, space.positions["G"]] == space.states["G"].index("B")).astype(int)
        + (codes[:, space.positions["M"]] == space.states["M"].index("Low")).astype(int)
        + (codes[:, space.positions["S"]] == space.states["S"].index("Good")).astype(int)
    ) >= 2
    np.testing.assert_array_equal(result, expected)
    q = parse_query("P(I | not E==No or D!=Easy)", 1, desc, advanced=True)
    result = condition_mask(q.condition, space, space.assignments)
    expected = (codes[:, space.positions["E"]] != 0) | (codes[:, space.positions["D"]] != 0)
    np.testing.assert_array_equal(result, expected)


def test_basic_equalities_and_duplicate_targets():
    desc = load_description(DATA / "opis.json")
    query = parse_query("MAP(Q, S | D==Hard, G==B)", 20, desc)
    assert query.evidence == {"D": "Hard", "G": "B"}
    with pytest.raises(ValueError, match="duplicate"):
        parse_query("P(G, G)", 1, desc)
    with pytest.raises(ValueError, match="also occurs"):
        parse_query("P(G | G==A)", 1, desc)


@pytest.mark.parametrize("source", [
    "P(G | I==X)",
    "P(G | __import__(os))",
    "P(G | I.__class__==Dumb)",
    "P(G | I==Dumb or I==Intelligent)",
])
def test_reject_invalid_or_advanced_evidence_in_simple_file(source):
    desc = load_description(DATA / "opis.json")
    with pytest.raises(ValueError):
        parse_query(source, 4, desc, advanced=False)


def test_logical_query_target_cannot_occur_inside_formula():
    desc = load_description(DATA / "opis.json")
    with pytest.raises(ValueError, match="also occurs"):
        parse_query("P(I | atleast(1, I==Dumb, G==A))", 2, desc, advanced=True)
