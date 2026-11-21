# Project 2 – Package Manager

This is the solution to Project 2 in Knowledge Engineering. The
[assignment specification](projekt2.pdf) defines the tasks. The program
encodes the package repository as a propositional knowledge base and uses
Z3 to plan installations and removals and to explain unsatisfiable requests.

**Group 26.** Authors: Milana Ronchyk and Anna Przyłucka.

## Implementation status

| Level | Tasks | Status | Report and results |
| --- | --- | --- | --- |
| 4 points | 4.1–4.5 | Complete | [Report](4pkt/raport4.md), [results](4pkt/results) |
| 6 points | 6.1–6.4 | Complete | [Report](6pkt/raport6.md), [results](6pkt/results) |

The [project presentation notes](prezentacja_package_manager.md) describe the
implementation and its modules in detail.

## Running the program

Use Python 3.11 or later. From this project directory, install the solver
dependency in a virtual environment. Install `pytest` to run the tests.

```powershell
python -m pip install -r requirements.txt
python -m pip install pytest
```

The first and third commands below plan installation into an empty
environment. The second starts from an existing state.

```powershell
python -m package_manager install examples/repo_example.json examples/req_app2.txt
python -m package_manager install examples/repo_example.json examples/req_app2.txt --state examples/state_example.txt
python -m package_manager install data/repo_10.json data/requests_10.txt
```

Use `remove` to plan removal and add `--autoremove` to remove unneeded
dependencies. Use `explain` to inspect an unsatisfiable request.

```powershell
python -m package_manager remove examples/repo_example.json examples/rm_tool.txt --state examples/state_example.txt
python -m package_manager remove examples/repo_example.json examples/rm_tool.txt --state examples/state_example.txt --autoremove
python -m package_manager explain examples/repo_example.json examples/requests_example.txt
```

The `--output FILE` option saves the new state in the format
`NAME VERSION [manual]`. Each resulting state is checked independently by
`verification.verify_state`, which performs its checks without Z3.

Use one request per line in a request file, for example `app==2.0`. Blank
lines and comments starting with `#` are ignored. Use one package name per
line in a removal file.

Run the benchmark, randomized scenario, validation scripts, and tests with
the commands below.

```powershell
python -m package_manager.experiments data --group 26 --timeout 600
python -m package_manager.scenario data/repo_200.json
python 4pkt/check4.py
python 6pkt/check6.py
python -m pytest
```

Run the `python -m ...` commands from the project directory with the virtual
environment active. You can also open `check4.py` or `check6.py` and run it
through the **Run** button in VS Code.

## Project layout

| Directory | Contents |
| --- | --- |
| `package_manager/` | Application source code |
| `data/` | Group 26 package repositories and requests (`repo_N.json`, `requests_N.txt`) |
| `examples/` | Assignment examples and small request files for the commands above |
| `tests/` | Automated tests run with `python -m pytest` |
| `4pkt/`, `6pkt/` | Validation scripts, recorded results in `results/`, and reports |

## Modules in `package_manager/`

| File | Responsibility | Level |
| --- | --- | --- |
| `models.py`, `versions.py`, `requirements_parser.py` | Repository, requirement, and state models, version comparison, parsing, and name normalization | 4 |
| `json_reader.py`, `loaders.py` | Read and validate repositories, requests, states, and package lists, with errors that identify the input location | 4, 6 |
| `knowledge_base.py` | Create `p==v` variables and label axioms A1–A3 | 4 |
| `installer.py` | Plan installation into an empty environment using the criteria from 4.3 | 4 |
| `verification.py` | Verify the resulting state independently of the solver | 4 |
| `experiments.py` | Run the 4.5 benchmark | 4 |
| `plan.py` | Build a change plan between states and save the resulting state | 6 |
| `solving.py` | Encode changes relative to the initial state and optimize them lexicographically | 6 |
| `operations.py` | Install into an existing state (6.1) and plan removal with optional autoremove (6.2) | 6 |
| `explanations.py` | Find a minimal unsatisfiable subset of axioms and requests (6.3) | 6 |
| `scenario.py` | Run the randomized scenario for 6.4 using seed 2026 | 6 |
| `__main__.py` | Provide the documented `install`, `remove`, and `explain` commands | 4, 6 |

## Optimization criteria

The operations use the same axioms. A1 permits at most one version of each
package, A2 encodes dependencies, and A3 encodes conflicts. The solver
minimizes the objectives lexicographically. A version's outdatedness is
its position in that package's version list sorted newest first, so the
newest version scores 0. The score for a set of packages is the sum.

| Operation | Objectives in priority order |
| --- | --- |
| Installation into an empty environment (4.3) | Requested package outdatedness, total package count, outdatedness of the other packages |
| Installation into an existing state (6.1) | Removed packages, version changes to retained packages, outdatedness of newly requested packages, new packages, outdatedness of other new packages |
| Removal (6.2) | Removed manually installed packages outside the request, version changes, new packages, removed packages. With `--autoremove`, the last objective is the total number of installed packages. |

## Results

The recorded assignment examples match the expected results for
installation into an empty environment, installation into an existing
state, removal, and removal with autoremove. Each resulting state passed
independent verification. For the largest Group 26 repository in
experiment 4.5 (21,096 versions and 14,776 axioms), building the knowledge
base took about 3.5 seconds and solving took about 6 seconds. The 12-operation
scenario on `repo_200.json` took about 29 seconds. The linked reports contain
the full results.
