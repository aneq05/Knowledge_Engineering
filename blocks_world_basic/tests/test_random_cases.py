import unittest

from src.dfs import solve_dfs
from src.experiments import generate_cases
from src.verifier import verify_plan


class RandomCaseTests(unittest.TestCase):
    def test_generation_is_reproducible(self):
        first = generate_cases(seed=123, min_size=3, max_size=4, cases_per_size=2)
        second = generate_cases(seed=123, min_size=3, max_size=4, cases_per_size=2)
        self.assertEqual(first, second)

    def test_generates_requested_numbers_and_valid_distinct_states(self):
        cases = generate_cases(seed=123, min_size=3, max_size=5, cases_per_size=5)
        self.assertEqual(len(cases), 15)
        for case in cases:
            self.assertEqual(case.start.size, case.size)
            self.assertEqual(case.goal.size, case.size)
            self.assertNotEqual(case.start, case.goal)

    def test_every_found_solution_passes_verification(self):
        cases = generate_cases(seed=123, min_size=3, max_size=5, cases_per_size=2)

        for case in cases:
            with self.subTest(size=case.size, number=case.number):
                result = solve_dfs(case.start, case.goal)
                self.assertTrue(result.solved, result.status)

                valid, message = verify_plan(case.start, case.goal, result.moves)
                self.assertTrue(valid, message)


if __name__ == "__main__":
    unittest.main()
