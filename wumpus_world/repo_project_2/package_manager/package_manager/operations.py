"""Operacje na stanie: instalacja (6.1), usuwanie (6.2) i aktualizacja (8.1)."""

import z3

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .installer import _request_formula
from .knowledge_base import KnowledgeBase, build_knowledge_base
from .models import EnvironmentState, Repository, Requirement
from .plan import Change, diff_states
from .requirements_parser import normalize_name
from .solving import Encoding, encode, read_state, solve_lex
from .verification import verify_state


@dataclass(frozen=True)
class OperationResult:
    state: EnvironmentState
    changes: list[Change]
    costs: list[int]


# na 6 - zakończenie instalacji i usuwania
def _finish(enc: Encoding, solved, requested: set[str], requests: Sequence[Requirement] = ()):
    if solved is None:
        return None
    model, costs = solved
    state = read_state(enc, model, requested)
    errors = verify_state(enc.repository, state, requests)  # niezależna weryfikacja każdego wyniku
    if errors:
        raise RuntimeError("Solver zwrócił niepoprawny stan:\n" + "\n".join(errors))
    return OperationResult(state, diff_states(enc.initial, state), costs)


# na 6.1
def install_with_state(
    repository: Repository,
    requests: Sequence[Requirement],
    initial: EnvironmentState,
    kb: KnowledgeBase | None = None,
) -> OperationResult | None:
    kb = kb or build_knowledge_base(repository)
    enc = encode(repository, kb, initial)
    # nazwy pakietów żądanych
    requested = {normalize_name(r.package) for r in requests}
    # pakiety z repo
    known = set(repository.packages)
    # pakiety ze stanu początkowego
    old = set(initial.installed)
    # twarde ograniczenia
    hard = [_request_formula(r, kb) for r in requests]
    objectives = [
        enc.count(enc.removed.values()),  # 1. usunięte pakiety
        enc.count(enc.changed.values()),  # 2. zmiany wersji pakietów, które zostają
        enc.staleness(sorted((requested - old) & known)),  # 3. przestarzałość żądanych, które nie były zainstalowane
        enc.count(enc.new.values()),  # 4. nowe pakiety
        enc.staleness(sorted(known - old - requested)),  # 5. przestarzałość pozostałych nowych
    ]
    return _finish(enc, solve_lex(enc, hard, objectives), requested, requests)

# na 6.2
def remove_packages(
    repository: Repository,
    names: Sequence[str],
    initial: EnvironmentState,
    autoremove: bool = False,
    kb: KnowledgeBase | None = None,
) -> OperationResult | None:
    kb = kb or build_knowledge_base(repository)
    enc = encode(repository, kb, initial)
    to_remove = {normalize_name(name) for name in names}
    # dla każdego znanego pakietu z listy powstaje warunek not installed[p] -> pakiet musi zniknąć ze stanu końcowego
    hard = [z3.Not(enc.installed[p]) for p in to_remove if p in repository.packages]  # żaden z P nie zostaje
    # ręczne pakiety których użytkownik nie zażądał do usunięcia
    manual_outside = [p for p, item in initial.installed.items() if item.manual and p not in to_remove]
    objectives = [
        enc.count(enc.removed[p] for p in manual_outside),  # 1. usunięte pakiety ręczne spoza P
        enc.count(enc.changed.values()),  # 2. zmiany wersji
        enc.count(enc.new.values()),  # 3. nowe pakiety
        # 4. bez autoremove: usunięte pakiety; z autoremove: wszystkie zainstalowane pakiety
        enc.count(enc.installed.values()) if autoremove else enc.count(enc.removed.values()),
    ]
    return _finish(enc, solve_lex(enc, hard, objectives), set())

