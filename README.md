# Knowledge Engineering

Course projects and lab materials on planning, logical inference, dependency
resolution, and probabilistic modeling.

## Projects

| Project | Goal | Methods and tools |
| --- | --- | --- |
| [Project 1 – Blocks World](blocks_world_basic/README.md) | Find a legal sequence of moves from an initial block arrangement to a goal arrangement | Depth-first search with backtracking, independent plan verification |
| [Wumpus World](wumpus_world/README.md) | Plan an agent's actions in a cave based on local observations | Answer set programming (ASP), Clingo, risk strategies |
| [Project 2 – Package Manager](wumpus_world/repo_project_2/package_manager/README.md) | Plan package installations and removals subject to version constraints, dependencies, and conflicts | Z3, lexicographic optimization, independent state verification |
| [Project 3 – Student Bayesian Network](sieci_bayesowskie/projekt_3/README.md) | Learn a model from incomplete student data and answer probabilistic queries | pgmpy, MLE, EM, hill climbing with BIC, probability and MAP queries |

Run each example separately from the repository root in PowerShell with
Python 3.11.

## Blocks World

The program validates the initial and goal arrangements, searches for a
sequence of legal moves, and checks the resulting plan independently. The
project includes valid and invalid examples, experiments, and an interactive
visualization that steps through the search.
[Report](blocks_world_basic/reports/raport.md) · [DFS visualization](blocks_world_basic/other_resources/visualizations/dfs-krok-po-kroku.html)

```powershell
Set-Location blocks_world_basic
py -3.11 -m src.main examples/simple_3.txt
```

## Wumpus World

The agent combines observations with ASP rules to infer which cells are safe
and where hazards may be present. You can play manually, watch the agent, or
compare its cautious, risk-taking heuristic, and model-counting strategies.
[Visualizer guide](wumpus_world/README.md) · [Lab notebook](wumpus_world/lab.ipynb)

```powershell
Set-Location wumpus_world
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe visualizer.py
```

The local game is served at `http://127.0.0.1:8765` by default. To run the
classic AIMA scenario in the terminal, use
`.\.venv\Scripts\python.exe simulate.py --aima`.

## Package Manager

The solver reads a JSON package repository and computes a plan for an empty
or existing environment. It supports installation, removal with optional
`--autoremove`, and explanations for unsatisfiable installation requests.
Z3 optimizes the changes lexicographically, and a separate verifier checks
the resulting state. The project includes sample inputs, the group 26
benchmark data, and reports for the 4- and 6-point requirements.
[Project guide](wumpus_world/repo_project_2/package_manager/README.md) · [4-point report](wumpus_world/repo_project_2/package_manager/4pkt/raport4.md) · [6-point report](wumpus_world/repo_project_2/package_manager/6pkt/raport6.md)

This example plans an installation from a supplied environment state.

```powershell
Set-Location wumpus_world/repo_project_2/package_manager
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m package_manager install examples/repo_example.json examples/req_app2.txt --state examples/state_example.txt
```

## Student Bayesian Network

The program uses dataset `k26` to learn discrete Bayesian networks from
training data with missing values and evaluates them on a separate test set.
The 4-point run includes the expert graph, probability and joint MAP queries,
and grade prediction metrics. The 6-point run adds a comparison of parameter
estimators, including EM with multiple random starts, and three BIC-based
approaches to structure learning, one of which uses posterior imputation.
The program writes a Markdown report and query answers in JSON.
[Code walkthrough](sieci_bayesowskie/projekt_3/OPIS_KODU.md) · [4-point results](sieci_bayesowskie/projekt_3/results/4_pkt/report.md) · [6-point results](sieci_bayesowskie/projekt_3/results/6_pkt/report.md) · [Introductory pgmpy notebook](sieci_bayesowskie/pgmpy_intro.ipynb)

The `--output` option directs each run to a separate folder.

```powershell
Set-Location sieci_bayesowskie/projekt_3
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install "pgmpy==1.1.2"
$env:PYTHONHASHSEED = "0"
.\.venv\Scripts\python.exe -m student_bn --level 4 --output results/local_4_pkt
.\.venv\Scripts\python.exe -m student_bn --level 6 --output results/local_6_pkt
```
