import json
import pytest

from pathlib import Path

from student_bn.data import load_csv, load_description, data_statistics

DATA = Path(__file__).resolve().parents[1] / "data/k26"


def test_load_real_dataset_and_missing_values():
    description = load_description(DATA / "opis.json")
    train = load_csv(DATA / "dane.csv", description)
    test = load_csv(DATA / "test.csv", description, complete=True)
    assert len(description.variables) == 9
    assert data_statistics(train)["rows"] == 2000
    assert data_statistics(train)["complete_rows"] == 367
    assert len(test) == 2000
    assert train["I"].isna().sum() == 1289


@pytest.mark.parametrize("update, fragment", [
    ({"unexpected": 1}, r"\$\.unexpected"),
    ({"expert_edges": [["D", "G"], ["G", "D"]]}, "directed cycle"),
    ({"variables": {"I": {"states": ["Dumb", "Dumb"]}}}, "duplicate state"),
])
def test_bad_json_is_rejected_with_location(tmp_path, update, fragment):
    payload = json.loads((DATA / "opis.json").read_text())
    if "variables" in update:
        payload["variables"]["I"].update(update["variables"]["I"])
    else:
        payload.update(update)
    source = tmp_path / "opis.json"
    source.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match=fragment):
        load_description(source)


def test_bad_csv_has_line_number(tmp_path):
    description = load_description(DATA / "opis.json")
    source = tmp_path / "test.csv"
    source.write_text("D,I,M,Q,E,G,S,L,B\nEasy,Dumb,Low\n")
    with pytest.raises(ValueError, match=r"test.csv:2: expected 9 fields"):
        load_csv(source, description)


def test_missing_test_value_is_rejected(tmp_path):
    description = load_description(DATA / "opis.json")
    source = tmp_path / "test.csv"
    source.write_text("D,I,M,Q,E,G,S,L,B\nEasy,Dumb,Low,High,No,A,Good,,Yes\n")
    with pytest.raises(ValueError, match=r"test.csv:2: missing value in L"):
        load_csv(source, description, complete=True)
