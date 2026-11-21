import z3

from collections.abc import Iterable
from dataclasses import dataclass

from .knowledge_base import KnowledgeBase
from .models import EnvironmentState, InstalledPackage, Repository
from .verification import verify_state
from .versions import version_key

# na 6
def total(terms: Iterable[z3.ArithRef]) -> z3.ArithRef:
    terms = list(terms)
    return z3.Sum(terms) if terms else z3.IntVal(0)


@dataclass
class Encoding:
    repository: Repository
    kb: KnowledgeBase
    initial: EnvironmentState
    rank: dict  # (pakiet, wersja) -> przestarzałość (0 = najnowsza)
    installed: dict  # pakiet -> "którakolwiek wersja jest zainstalowana"
    removed: dict  # tylko pakiety ze stanu początkowego: zostały usunięte
    changed: dict  # tylko pakiety ze stanu początkowego: zostały, ale zmieniła się wersja
    new: dict  # tylko pakiety spoza stanu początkowego: zostały zainstalowane

    # na 6
    def count(self, flags: Iterable[z3.BoolRef]) -> z3.ArithRef:
        return total(z3.If(flag, 1, 0) for flag in flags)

    # na 6
    def staleness(self, packages: Iterable[str]) -> z3.ArithRef:
        # Suma przestarzałości zainstalowanych wersji wskazanych pakietów.
        return total(
            z3.If(self.kb.variables[p, v], self.rank[p, v], 0)
            for p in packages
            for v in self.repository.packages[p]
        )


# na 6
def encode(repository: Repository, kb: KnowledgeBase, initial: EnvironmentState) -> Encoding:
    # sprawdzenie stanu początkowego
    errors = verify_state(repository, initial)
    if errors:
        raise ValueError("Niepoprawny stan początkowy:\n" + "\n".join(errors))
    
    # wyznaczenie rang wersji
    rank = {}
    for package, versions in repository.packages.items():
        for position, version in enumerate(sorted(versions, key=version_key, reverse=True)):
            rank[package, version] = position
            
    enc = Encoding(repository, kb, initial, rank, {}, {}, {}, {})
    for package, versions in repository.packages.items():
        any_version = z3.Or([kb.variables[package, v] for v in versions])
        enc.installed[package] = any_version
        
        # rozpoznanie nowych pakietów
        old = initial.installed.get(package)
        if old is None:
            enc.new[package] = any_version
        else:
            # musimy sprawdzić czy zostanie usunięty albo zmieni wersję
            # Wersja w stanie może być zapisana jako 1.0.0, a w repozytorium jako 1.0.
            old_var = next(
                kb.variables[package, v] for v in versions if version_key(v) == version_key(old.version)
            )
            enc.removed[package] = z3.Not(any_version)
            enc.changed[package] = z3.And(any_version, z3.Not(old_var))
    return enc


# na 6
def solve_lex(enc: Encoding, hard: list, objectives: list):
    optimizer = z3.Optimize()
    # optymalizacja leksykograficzna
    optimizer.set(priority="lex")
    for axiom in enc.kb.axioms:
        optimizer.add(axiom.formula)
    # hard zawiera żądania użytkownika
    for formula in hard:
        optimizer.add(formula)
    # dodanie celów - kolejność listy objectives jest kolejnością priorytetów
    for objective in objectives:
        optimizer.minimize(objective)
    status = optimizer.check()
    if status == z3.unsat:
        return None
    if status != z3.sat:
        raise RuntimeError(f"Solver nie rozstrzygnął problemu: {optimizer.reason_unknown()}")
    # model i wartości kryteriów zwracamy
    model = optimizer.model()
    return model, [model.eval(o, model_completion=True).as_long() for o in objectives]


# na 6
def read_state(enc: Encoding, model: z3.ModelRef, requested: set[str]) -> EnvironmentState:
    installed = {}
    for (package, version), variable in enc.kb.variables.items():
        if z3.is_true(model.eval(variable, model_completion=True)):
            old = enc.initial.installed.get(package)
            # Pakiet żądany lub już wcześniej ręczny pozostaje ręczny.
            manual = package in requested or (old is not None and old.manual)
            installed[package] = InstalledPackage(package, version, manual)
    return EnvironmentState(installed)