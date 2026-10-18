import unittest

from src.input_reader import read_problem


class FileValidationTests(unittest.TestCase):
    def test_rejects_all_invalid_example_files(self):
        cases = {
            "examples/invalid_self.txt": "samym sobie",
            "examples/invalid_nonexistent.txt": "nieistniejącym",
            "examples/invalid_two_on_one.txt": "tym samym klocku",
            "examples/invalid_cycle.txt": "cykl",
        }

        for path, expected_message in cases.items():
            with self.subTest(path=path):
                with self.assertRaisesRegex(ValueError, expected_message):
                    read_problem(path)


if __name__ == "__main__":
    unittest.main()
