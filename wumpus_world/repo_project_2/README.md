# Project 2 – Package Manager development notes

For the current implementation, commands, and 4- and 6-point reports, see
the [project README](package_manager/README.md). The notes below record
the earlier layout and development plan.

The [assignment specification](projekt2.pdf) defines the tasks.
**4.2** means task 2 at the 4-point level. The same convention applies to
6.1 and 8.1. The levels are cumulative, so the 6-point level includes the
4-point requirements, and the 8-point level includes both.

At the stage described here, the program installed packages into an empty
environment and covered the main parts of 4.1–4.4. The 4.5 experiments,
the final report, and a validation detail were pending. Installation into
an existing state, removal, explanations, and updates were planned.

## Original command-line interface

The original program required Python 3.11 or later. The commands at that
stage were run from the `repo_project_2` directory.

```text
python -m pip install -r requirements.txt
python -m package_manager repo_example.json requests_example.txt
python -m package_manager repos/repos/k26/repo_10.json repos/repos/k26/requests_10.txt
```

The first argument was the JSON repository file. The second was the
request file, with one request per line. The program printed the selected
versions and values of the three objectives, or reported infeasibility.

`installer.install(repo, requests)` returns an `InstallationResult` or
`None` when the requests are infeasible. Before returning a result, it
calls `verification.verify_state(repo, state, requests)`. The verifier
checks the state independently of Z3 and returns all detected violations.
An empty list indicates a valid state. The request argument is optional
when checking a repository and state.

The optimization objectives minimize requested package outdatedness first,
then the total number of installed packages, and then the outdatedness of
the remaining packages. A version's outdatedness is its position in the
package's versions sorted newest first, starting at zero.

## Validation and models

The loader rejects duplicate JSON keys, unknown fields, invalid types,
names, versions, and operators, equivalent duplicates, self-dependencies,
and self-conflicts. Messages identify the file and a location such as
`packages['app'].versions['2.0'].requires[1]`. JSON syntax errors include
a line and column. Request and state file errors include a line number.

User requests and repository requirements share the `Requirement` class.
Its constraints are `VersionConstraint` objects. `Dependency` stores
alternatives written with `|` in the input. Loading parses these constructs
into objects that the solver and verifier can use directly.

`load_repository` validates the repository and normalizes package names.
The knowledge base and verifier expect this normalized representation. If
you create a `Repository` programmatically, apply the same rules, including
normalized keys in `packages` and one entry per equivalent version.

Use the parser when creating requests in code. Run this example from the
current `package_manager/` project directory.

```python
from package_manager.installer import install
from package_manager.loaders import load_repository
from package_manager.requirements_parser import parse_requirement

result = install(load_repository("examples/repo_example.json"), [parse_requirement("app >=1.0")])
```

## Original progress on the 4-point tasks

| Task | Status at the time | Implementation |
| --- | --- | --- |
| **4.1 Loading, models, and validation** | Implemented with the empty-`versions` caveat below | [models.py](package_manager/package_manager/models.py) defines `Repository`, `PackageVersion`, `Requirement`, `VersionConstraint`, `Dependency`, `EnvironmentState`, and `InstalledPackage`. [json_reader.py](package_manager/package_manager/json_reader.py) uses `read_json`, `_ObjectPairs`, and `_convert_object` to detect JSON errors and duplicate keys. [loaders.py](package_manager/package_manager/loaders.py) provides `load_repository`, `load_requests`, `load_state`, and validation helpers. [requirements_parser.py](package_manager/package_manager/requirements_parser.py) parses requirements and normalizes names. [versions.py](package_manager/package_manager/versions.py) provides `version_key` for numeric version comparison. |
| **4.2 Knowledge base with axioms A1–A3** | Implemented | [knowledge_base.py](package_manager/package_manager/knowledge_base.py) defines `build_knowledge_base` and `_KnowledgeBaseBuilder`. `create_variables` creates `p==v` variables, `add_single_version_axiom` implements A1, `add_dependencies` implements A2, and `add_conflicts` implements A3. An `Axiom` stores a formula, an identifier, and a label. |
| **4.3 Optimal installation** | Implemented for an empty environment | [installer.py](package_manager/package_manager/installer.py) uses `z3.Optimize` with `lex` priority. `_request_formula` enforces the requests, `_costs` builds three objectives, and `_read_state` extracts the result. Infeasibility returns `None`. A solver result of `unknown` raises an error. The CLI reports the solution or infeasibility. |
| **4.4 Independent verification** | Implemented | [verification.py](package_manager/package_manager/verification.py) contains `verify_state`, `_find_version`, `_check_dependencies`, and `_check_conflicts`. The verifier checks the state and any supplied requests, then returns all violations. Installation checks each result before returning it, and the CLI reports violations. |
| **4.5 Experiments and report** | Pending at the time | The [Group 26 data](repos/repos/k26) was available. The remaining work included a measurement script, a result table, and a discussion of scaling. Sample runs and checks on small repositories were preliminary steps. |

The [knowledge base notes](kodowanie_bazy_wiedzy.md) explain the encoding and
formulas required for 4.2. This material was intended for the final report.

At this stage, `_load_versions` accepted an empty `versions: {}` object.
The assignment required at least one version per package. The planned
validation would report `packages['name'].versions` and include a test.

### Planned benchmark for 4.5

- [ ] Run the installation for every `N = 10, 30, 100, 300, 1000` with the
  Group 26 pair `repo_N.json` and `requests_N.txt`.
- [ ] Record the version count, axiom count, and requests for each case.
- [ ] Record the installed package count and outdatedness, or record that
  the case is infeasible.
- [ ] Measure the time to build the knowledge base, including file
  loading, and measure solving time separately.
- [ ] Record the result of independent verification. For infeasible
  cases, record that there is no resulting state to verify.
- [ ] Identify Group 26 in the report and discuss how runtime scales
  with repository size.

The proposed `experiments.py` module would collect measurements for a CSV
file and a report table. `repo_200.json` is reserved for task 6.4. The
[current 4-point report](package_manager/4pkt/raport4.md) contains the
completed benchmark.

## Original plan for the 6-point tasks

### 6.1 Installation into an existing state

The starting code provided `load_state`, state classes, the `manual`
flag, a shared knowledge base, and a verifier. Installation into an empty
environment marked requested packages with `manual=True`.

- [ ] Pass the initial state to the installer and read and write states
  through the CLI.
- [ ] Preserve manual installation flags and mark requested packages as
  manually installed.
- [ ] Generate a plan of installations, removals, upgrades, and downgrades.
- [ ] Minimize these five objectives in order.

1. Number of removed packages.
2. Number of version changes among retained packages.
3. Outdatedness of requested packages absent from the initial state.
4. Number of newly installed packages.
5. Outdatedness of the other newly installed packages.

An empty initial state should give the same result as the criteria from
4.3. The original `install` function accepted a repository and requests.
The proposed changes involved `installer.py`, `loaders.py`, and
`__main__.py`.

### 6.2 Removal and autoremove

The proposed operation would read a set `P` with one package name per line.
The final state would exclude every package in `P`. Dependent packages
could be removed or switched to a compatible version.

Minimize the objectives in the following order.

1. Removed manually installed packages outside `P`.
2. Version changes.
3. Newly installed packages.
4. Removed packages.

With `autoremove`, the fourth objective minimizes the total number of
installed packages. This allows the solver to discard unused dependencies.
Each result must pass `verify_state` and include a change plan. A
standalone `remover.py` was proposed.

### 6.3 Explanations for infeasible requests

The starting code included readable labels through `Axiom.label`,
identifiers through `Axiom.name`, and
`KnowledgeBase.add_to_solver(..., tracked=True)` for tracking axioms.

- [ ] Check satisfiability with `z3.Solver` and track the user's requests.
- [ ] Read `unsat_core` and map its entries to readable labels.
- [ ] Minimize the core so removing any single member makes the rest
  satisfiable.
- [ ] Show an explanation for requesting `app==2.0` together with `tool`
  in the sample repository.
- [ ] Explain infeasible cases from 4.5 or create infeasible examples if
  the benchmark has none.

The requirement is a **subset-minimal unsatisfiable core**. Each member
must be necessary within that set. Finding a core with the smallest
possible number of members is a stronger requirement.
`explanations.py` was proposed for this logic.

### 6.4 Reproducible operation scenario

- [ ] Start with an empty state on [repo_200.json](repos/repos/k26/repo_200.json).
- [ ] Run at least 10 random operations, including installations and
  removals with and without autoremove.
- [ ] Set and record the random seed.
- [ ] Check every intermediate state with `verify_state`.
- [ ] Record elapsed time and the counts of changes, installed packages,
  and manually installed packages for each operation.

This experiment depended on 6.1 and 6.2. The original plan suggested
including it in `experiments.py`. The
[current 6-point report](package_manager/6pkt/raport6.md) contains the
completed scenario.

## Requirements for the 8-point level

### 8.1 Updates

Update the set `P` of installed packages listed in a file. With no file,
the operation targets every installed package. Manually installed packages
and members of `P` must remain installed.

Minimize the objectives in the following order.

1. Outdatedness of packages in `P`.
2. Removed packages.
3. Version changes outside `P`.
4. Newly installed packages.
5. Outdatedness across all installed packages.

The plan was to reuse the knowledge base, independent verifier, and state
support from 6.1. Updates need their own constraints, objectives, and CLI
dispatch. A standalone `updater.py` was proposed.

### 8.2 Update conflicts and the Pareto front

- [ ] For each package in `P`, find its individually attainable newest
  version while retaining manually installed packages.
- [ ] Check whether all these versions can be installed together.
- [ ] If they cannot, report the conflict and explain it with the
  unsatisfiable core mechanism from 6.3.
- [ ] List the nondominated solutions on the Pareto front for the
  outdatedness of the conflicting packages.

In the assignment's reference example, the initial state is
`a 1.0 manual`, `b 1.0 manual`. The front consists of
`{a 2.0, b 1.0}` and `{a 1.1, b 2.0}`. Updating `a` alone should make
`a 2.0` attainable without that conflict. Lexicographic optimization
selects one solution based on objective order. This task requires
enumerating the Pareto front.

### 8.3 PyPI data

The assignment describes a `pypi_data.json` file with 92 packages and
3,330 versions. The plan called for obtaining it from the assignment
materials and adding support for its format.

- [ ] Read `requires_dist`, `requires_python`, and `meta.environment`.
- [ ] Interpret versions and requirements using PEP 440 and PEP 508
  through the `packaging` library.
- [ ] Use `requires_python` to skip versions incompatible with the target
  Python environment.
- [ ] Evaluate environment markers using `meta.environment`.
- [ ] Ignore extras as specified in the assignment.
- [ ] Support installations, removals, updates, verification, and
  explanations with the new input.
- [ ] Report loading and solving times for a scenario such as installing
  the oldest available `pandas` and `requests`, adding `boto3` and
  `aiobotocore`, updating, removing `botocore`, and explaining the
  conflict between the newest `boto3` and oldest `botocore`.

The existing parser and `versions.py` handle the project's simplified
format. PyPI data requires an adapter such as `pypi_loader.py`, along
with support for broader version comparisons and requirement matching.
The original loader should continue to validate the 4-point input format.

## Original development order

1. Complete validation for 4.1, run benchmark 4.5, and prepare the
   4-point report.
2. Add state persistence and change plans, then install into existing
   states (6.1).
3. Add removal with autoremove (6.2) and explanations (6.3).
4. Run the scenario for 6.4.
5. Add updates (8.1), then analyze conflicts and the Pareto front (8.2).
6. Add PyPI support and run the scenario for 8.3.

Submission at the selected level requires source code and run instructions,
sample inputs, and a report with results and commentary. The assignment
also requires presenting the project to the instructor. Automated tests
are recommended. The proof of NP-completeness at the end of the
specification is optional.

## Original development checks

The original unit test suite covered invalid inputs, examples from the
specification, and comparisons of the solver and verifier with exhaustive
enumeration on small repositories. Its only third-party dependency was
`z3-solver`.

```text
python -m unittest discover -s tests -v
```

The original style and strict type-checking setup used `pyproject.toml`
and ignored missing type declarations in the external Z3 dependency.

```text
python -m pip install -r requirements-dev.txt
python -m ruff check package_manager tests
python -m ruff format --check package_manager tests
python -m mypy
```

For the current test suite and commands, see the
[implementation guide](package_manager/README.md).
