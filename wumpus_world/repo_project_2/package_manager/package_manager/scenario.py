"""Odtwarzalny scenariusz 6.4: losowe operacje na repo_200.json, start od pustego stanu."""

import random
import sys
import time

from .loaders import load_repository
from .knowledge_base import build_knowledge_base
from .models import EnvironmentState
from .operations import install_with_state, remove_packages
from .requirements_parser import parse_requirement
from .verification import verify_state

SEED = 2026


def main(path: str, steps: int = 12) -> None:
    rng = random.Random(SEED)
    repository = load_repository(path)
    kb = build_knowledge_base(repository)
    state = EnvironmentState()
    names = sorted(repository.packages)  # sorted: kolejność nie zależy od haszowania napisów
    print("krok | operacja | zmiany | pakiety | ręczne | czas [s]")
    for step in range(1, steps + 1):
        manual = sorted(p for p, i in state.installed.items() if i.manual)
        # pierwsze trzy kroki są instalacjami
        if step <= 3 or not manual or rng.random() < 0.5:
            target = rng.choice(names)
            label = f"install {target}"
            started = time.perf_counter()
            result = install_with_state(repository, [parse_requirement(target)], state, kb)
        # później jest losowana instalacja albo usuwanie
        else:
            target = rng.choice(manual)
            autoremove = rng.random() < 0.5
            label = f"remove {target}" + (" --autoremove" if autoremove else "")
            started = time.perf_counter()
            result = remove_packages(repository, [target], state, autoremove, kb)
        elapsed = time.perf_counter() - started
        if result is None:
            print(f"{step} | {label} | brak rozwiązania (stan bez zmian) | - | - | {elapsed:.2f}")
            continue
        state = result.state
        assert verify_state(repository, state) == []  # weryfikacja każdego stanu pośredniego
        manual_count = sum(1 for i in state.installed.values() if i.manual)
        print(f"{step} | {label} | {len(result.changes)} | {len(state.installed)} | {manual_count} | {elapsed:.2f}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/repo_200.json")
    