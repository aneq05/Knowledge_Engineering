import unittest

from src.dfs import solve_dfs
from src.state import BlockWorldState
from src.verifier import verify_plan


class SolverAndVerifierTests(unittest.TestCase):
    def setUp(self):
        self.start = BlockWorldState((0, 1, 0, 2, 3))
        self.goal = BlockWorldState((2, 3, 4, 5, 0))

    def test_dfs_solves_reference_problem(self):
        result = solve_dfs(
            self.start,
            self.goal,
            node_limit=20_000,
            time_limit_seconds=2.0,
        )
        self.assertTrue(result.solved, result)
        valid, _ = verify_plan(self.start, self.goal, result.moves)
        self.assertTrue(valid)

    def test_reports_node_limit(self):
        result = solve_dfs(
            self.start,
            self.goal,
            node_limit=1,
            time_limit_seconds=2.0,
        )
        self.assertEqual(result.status, "node_limit")
        self.assertEqual(result.expanded_nodes, 1)
        self.assertFalse(result.solved)

    def test_reports_time_limit(self):
        result = solve_dfs(
            self.start,
            self.goal,
            node_limit=20_000,
            time_limit_seconds=1e-12,
        )
        self.assertEqual(result.status, "time_limit")
        self.assertFalse(result.solved)

    def test_verifier_reports_first_illegal_move(self):
        valid, message = verify_plan(self.start, self.goal, [(4, 5)])
        self.assertFalse(valid)
        self.assertIn("Ruch 1", message)
        self.assertIn("wariancie podstawowym", message)

    def test_verifier_rejects_legal_but_incomplete_plan(self):
        valid, message = verify_plan(self.start, self.goal, [(4, 0)])
        self.assertFalse(valid)
        self.assertIn("Stan końcowy", message)


if __name__ == "__main__":
    unittest.main()
