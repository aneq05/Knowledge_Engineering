# Kodowanie bazy wiedzy — punkt 4.2

Dla każdej wersji `v` pakietu `p` tworzona jest zmienna logiczna `p==v`.
Jest ona prawdziwa wtedy, gdy ta wersja pakietu jest zainstalowana. Zmienne
oraz formuły przechowuje `KnowledgeBase` z modułu `package_manager/knowledge_base.py`.

- **A1:** `AtMost(p==v1, ..., p==vn, 1)` dopuszcza najwyżej jedną wersję pakietu.
  Gdy pakiet ma zero lub jedną wersję, osobna formuła nie jest potrzebna.
- **A2:** dla każdego elementu `requires` powstaje implikacja: wybrana wersja
  pakietu implikuje alternatywę wszystkich wersji pasujących do wymagania.
  Znak `|` łączy alternatywne wymagania. Ograniczenia jednej alternatywy, np.
  `>=1.0 <2.0`, muszą być spełnione jednocześnie. Jeśli żadna wersja nie
  pasuje do żadnej alternatywy, prawa strona jest fałszem i tej wersji nie da
  się wybrać.
- **A3:** dla każdej wersji pasującej do konfliktu powstaje implikacja
  `p==v → ¬q==w`.

Wersje porównywane są jako ciągi liczb, np. `1.10 > 1.9`, a `1.0 = 1.0.0`.
Nazwy są porównywane bez uwzględniania wielkości liter, a ciągi znaków `-`,
`_` i `.` są równoważne. Gdy wymaganie nie ma pasującej wersji, pojawia się
ostrzeżenie. Każda formuła ma opis czytelny dla człowieka oraz osobny,
unikalny identyfikator do śledzenia jej przez Z3 w przyszłym wyjaśnianiu
sprzeczności.

Przykładowe formuły dla `repo_example.json`:

```text
A1: AtMost(lib==1.0, lib==1.5, lib==2.0, 1)
A2: app==2.0 → lib==2.0
A2: app==2.0 → (util==1.0 ∨ util==2.0)
A2: tool==1.1 → (json-fast==1.0 ∨ json-fast==2.0 ∨ json-slow==1.0)
A3: json-fast==1.0 → ¬json-slow==1.0
A3: legacy==1.0 → ¬util==2.0
```

Przykład użycia w katalogu `repo_project_2`:

```python
from package_manager.loaders import load_repository
from package_manager.knowledge_base import build_knowledge_base

repo = load_repository("repo_example.json")
kb = build_knowledge_base(repo)
for axiom in kb.axioms:
    print(axiom.label, ":", axiom.formula)
```
