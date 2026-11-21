import os
import pytest

from pathlib import Path

pytest.importorskip("pgmpy")

from student_bn.__main__ import run


@pytest.mark.skipif(os.environ.get("RUN_FULL_INTEGRATION") != "1",
                    reason="set RUN_FULL_INTEGRATION=1 to run three real BIC searches")
def test_full_six_point_pipeline(tmp_path):
    dataset = Path(__file__).resolve().parents[1] / "data/k26"
    output = tmp_path / "results"
    report = run(dataset, output, level=6, em_iterations=6, em_starts=5,
                 imputation_rounds=1, samples=0, seed=11)
    text = report.read_text(encoding="utf-8")
    assert "Six-point extension" in text
    assert "HC (complete, free)" in text
    assert "HC (complete, expert)" in text
    assert "HC (EM + imputation)" in text
    for name in ("answers_mle.json", "answers_em.json", "answers_mle_complete.json",
                 "answers_structure_free.json", "answers_structure_expert.json",
                 "answers_structure_em_imputed.json"):
        assert (output / name).is_file()
