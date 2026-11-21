# Blocks World – basic version (4 points)

The project covers tasks 1–4 of the assignment. It reads and validates block
arrangements, searches with bounded depth-first search and backtracking,
verifies plans independently, and runs reproducible experiments for `N=3..15`.

## Project layout

- `src/state.py` holds the state class, arrangement validation, and move rules.
- `src/input_reader.py` reads the initial and goal states.
- `src/verifier.py` checks the complete sequence of moves.
- `src/dfs.py` implements DFS with backtracking, statistics, and limits.
- `src/experiments.py` generates random cases and records measurements and results.
- `src/main.py` provides the command-line entry point.
- `tests/` contains automated unit tests.
- `examples/` contains sample inputs from the assignment.

The examples include a simple `N=3` problem, a reference `N=5` problem,
a larger `N=8` problem, and an invalid cyclic arrangement for demonstrating
input validation.

## Running the program

Run this command from the project directory.

```powershell
py -3 -m src.main
```

You can also supply an input file on the command line.

```powershell
py -3 -m src.main examples/simple_3.txt
```

To change the default input, edit the `INPUT_FILE` constant in `src/main.py`.

```python
INPUT_FILE = "examples/simple_3.txt"
```

Run the unit tests with the following command.

```powershell
py -3 -m unittest discover -s tests -v
```

`main.py` runs the solver for a single problem. DFS returns the first plan
it finds. The extended 6-point version of the assignment requires a shortest
plan.

## Experiment results for the report

```powershell
py -3 -m src.experiments
```

The command writes raw results for 65 problems to `results/results.csv`.
It records full move sequences for `N` from 3 through 8.
