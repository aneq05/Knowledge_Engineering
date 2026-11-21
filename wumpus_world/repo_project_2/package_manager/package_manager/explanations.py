"""Wyjaśnianie braku rozwiązania: minimalny (względem zawierania) sprzeczny podzbiór."""

from collections.abc import Sequence

import z3

from .installer import _request_formula
from .knowledge_base import KnowledgeBase, build_knowledge_base
from .models import Repository, Requirement


def explain(kb: KnowledgeBase, extra: Sequence[tuple[str, z3.BoolRef]]) -> list[str] | None:
    solver = z3.Solver()
    labels: dict[str, str] = {}
    guards: dict[str, z3.BoolRef] = {}
    items = [(axiom.label, axiom.formula) for axiom in kb.axioms] + list(extra)
    for index, (label, formula) in enumerate(items):
        guard = z3.Bool(f"guard_{index}")
        solver.add(z3.Implies(guard, formula))  # strażnik włącza daną formułę
        guards[str(guard)] = guard
        labels[str(guard)] = label
    status = solver.check(*guards.values())
    if status == z3.sat:
        return None
    if status == z3.unknown:
        raise RuntimeError(f"Solver nie rozstrzygnął problemu: {solver.reason_unknown()}")
    if status != z3.unsat:
        raise RuntimeError(f"Nieoczekiwany wynik solvera: {status}")
    core = [str(g) for g in solver.unsat_core()]
    # Minimalizacja przez usuwanie: jeśli bez elementu nadal jest sprzeczność, element jest zbędny.
    for name in list(core):
        if name not in core:
            continue
        trial = [guards[n] for n in core if n != name]
        status = solver.check(*trial)
        if status == z3.unknown:
            raise RuntimeError(f"Solver nie rozstrzygnął problemu: {solver.reason_unknown()}")
        if status == z3.unsat:
            core = [str(g) for g in solver.unsat_core()]
    return [labels[name] for name in core]


def explain_requests(repository: Repository, requests: Sequence[Requirement]) -> list[str] | None:
    kb = build_knowledge_base(repository)
    extra = [(f"żądanie użytkownika: {r}", _request_formula(r, kb)) for r in requests]
    return explain(kb, extra)