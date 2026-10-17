import tempfile
import unittest
from pathlib import Path

from src.blocks_world import InputFormatError, read_problem


class InputTests(unittest.TestCase):
    def test_reads_comments_and_blank_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "problem.txt"
            path.write_text(
                "# start\n\n0 1 0 2 3\n# goal\n2 3 4 5 0\n",
                encoding="utf-8",
            )
            start, goal = read_problem(path)

        self.assertEqual(start.supports, (0, 1, 0, 2, 3))
        self.assertEqual(goal.supports, (2, 3, 4, 5, 0))

    def test_rejects_different_sizes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "problem.txt"
            path.write_text("0 0 0\n0 0 0 0\n", encoding="utf-8")
            with self.assertRaisesRegex(InputFormatError, "tyle samo"):
                read_problem(path)


if __name__ == "__main__":
    unittest.main()
