# Projekt 2 - menedżer pakietów

Zakres zadań opisuje [projekt2.pdf](projekt2.pdf). Oznaczenie **4.2** oznacza
zadanie 2 z progu na 4 punkty; analogicznie używamy numerów 6.1 i 8.1.
Progi są kumulatywne: na 6 punktów trzeba wykonać również zadania na 4,
a na 8 punktów także zadania na 4 i 6.

**Aktualnie program instaluje pakiety do pustego środowiska.** Zaimplementowane
są główne elementy 4.1-4.4. Do zamknięcia progu 4 brakuje eksperymentów 4.5,
końcowego raportu oraz drobnego uzupełnienia walidacji opisanego poniżej.
Operacje na istniejącym stanie, usuwanie, wyjaśnianie i aktualizacja pozostają
do dodania.

## Uruchomienie

Wymagany jest Python 3.11 lub nowszy.

W katalogu `repo_project_2` zainstaluj zależność i uruchom program:

```powershell
python -m pip install -r requirements.txt
python -m package_manager repo_example.json requests_example.txt
python -m package_manager repos/repos/k26/repo_10.json repos/repos/k26/requests_10.txt
```

Pierwszy argument to plik repozytorium JSON, a drugi to plik żądań — jedno
żądanie na wiersz. Program wypisuje wybrane wersje i wartości trzech kryteriów.
Jeśli żadna instalacja nie spełnia żądań, wypisuje informację o braku rozwiązania.

`installer.install(repo, requests)` zwraca `InstallationResult` lub `None`,
gdy rozwiązanie nie istnieje. Przed zwróceniem wyniku sprawdza go funkcją
`verification.verify_state(repo, state, requests)`. Weryfikator nie używa Z3
i zwraca listę wszystkich wykrytych naruszeń. Przy pustej liście stan jest
poprawny. Można wywołać go również bez żądań, podając tylko repozytorium i stan.

Kryteria optymalizacji są stosowane kolejno: suma przestarzałości żądanych
pakietów, liczba wszystkich zainstalowanych pakietów, a następnie suma
przestarzałości pozostałych. Przestarzałość wersji to jej pozycja wśród wersji
danego pakietu posortowanych od najnowszej, zaczynając od zera.

## Walidacja i modele

Loader odrzuca powtórzone klucze JSON, nieznane pola, błędne typy, nazwy,
wersje i operatory, równoważne duplikaty oraz zależności i konflikty pakietu
z samym sobą. Komunikat zawiera nazwę pliku i ścieżkę, np.
`packages['app'].versions['2.0'].requires[1]`. Błędy składni JSON wskazują
linię i kolumnę, a błędy plików żądań i stanu — numer linii.

Żądania i wymagania w repozytorium korzystają z jednej klasy `Requirement`.
Jej ograniczenia są obiektami `VersionConstraint`. `Dependency` przechowuje
alternatywy rozdzielone w pliku znakiem `|`. Parsowanie odbywa się podczas
wczytywania; solver i weryfikator używają już gotowych obiektów.

Walidacja repozytorium i normalizacja nazw odbywają się w `load_repository`.
Baza wiedzy i weryfikator oczekują repozytorium w tej postaci, więc nie
powtarzają sprawdzania jego formatu. Przy ręcznym tworzeniu obiektu
`Repository` w kodzie trzeba zachować te same zasady, w tym znormalizowane
nazwy jako klucze słownika `packages` i brak równoważnych duplikatów wersji.

Przy tworzeniu żądań w kodzie użyj parsera:

```python
from package_manager.installer import install
from package_manager.loaders import load_repository
from package_manager.requirements_parser import parse_requirement

result = install(load_repository("repo_example.json"), [parse_requirement("app >=1.0")])
```

## Zadania na 4 punkty: co jest zrobione i gdzie

| Punkt | Status | Miejsce w kodzie i odpowiedzialność |
| --- | --- | --- |
| **4.1 - wczytywanie, modele, walidacja** | Zrealizowane; uwaga o pustym `versions` poniżej | [models.py](package_manager/models.py): `Repository`, `PackageVersion`, `Requirement`, `VersionConstraint`, `Dependency`, `EnvironmentState`, `InstalledPackage`. [json_reader.py](package_manager/json_reader.py): `read_json`, `_ObjectPairs`, `_convert_object` wykrywają błędy JSON i duplikaty kluczy. [loaders.py](package_manager/loaders.py): `load_repository`, `load_requests`, `load_state` oraz pomocnicze funkcje walidacji. [requirements_parser.py](package_manager/requirements_parser.py): parsowanie i normalizacja nazw. [versions.py](package_manager/versions.py): `version_key`, czyli numeryczne porównywanie wersji. |
| **4.2 - baza wiedzy A1-A3** | Zrealizowane | [knowledge_base.py](package_manager/knowledge_base.py): `build_knowledge_base` i `_KnowledgeBaseBuilder`. `create_variables` tworzy zmienne `p==v`, `add_single_version_axiom` realizuje A1, `add_dependencies` A2, a `add_conflicts` A3. `Axiom` przechowuje formułę, identyfikator i czytelną etykietę. |
| **4.3 - optymalna instalacja** | Zrealizowane dla pustego środowiska | [installer.py](package_manager/installer.py): `install` uruchamia `z3.Optimize` z kolejnością `lex`; `_request_formula` wymusza żądania, `_costs` buduje trzy kryteria, a `_read_state` odczytuje wynik. `None` oznacza brak rozwiązania; stan `unknown` solvera jest zgłaszany jako błąd. [__main__.py](package_manager/__main__.py): `main` przyjmuje pliki i wypisuje wynik albo informację o braku rozwiązania. |
| **4.4 - weryfikacja bez solvera** | Zrealizowane | [verification.py](package_manager/verification.py): `verify_state`, `_find_version`, `_check_dependencies`, `_check_conflicts` sprawdzają stan i opcjonalne żądania. Weryfikator zwraca wszystkie wykryte naruszenia. `install` wywołuje go przed zwróceniem każdego znalezionego stanu; przy błędach zgłasza całą ich listę, którą CLI wypisuje. |
| **4.5 - eksperymenty i raport** | Do zrobienia | Dane są w [repos/repos/k26](repos/repos/k26). Brakuje skryptu zbierającego pomiary, tabeli wyników i komentarza o skalowaniu. Sprawdzenie przykładów i uruchomienie małego repozytorium nie zastępują tego eksperymentu. |

Opis kodowania oraz konkretne formuły wymagane w 4.2 są już w
[kodowanie_bazy_wiedzy.md](kodowanie_bazy_wiedzy.md). Trzeba włączyć ten
materiał do końcowego raportu.

**Uwaga do 4.1:** PDF opisuje pakiet jako posiadający co najmniej jedną wersję.
Obecne `_load_versions` dopuszcza pusty obiekt `versions: {}`. Do pełnego
domknięcia walidacji należy go odrzucać z lokalizacją
`packages['nazwa'].versions` i dodać odpowiedni test.

### Co jeszcze trzeba zrobić w 4.5

- [ ] Dla `N = 10, 30, 100, 300, 1000` wykonać instalację z pary
  `repo_N.json` i `requests_N.txt` grupy **k26**.
- [ ] Dla każdego przypadku zapisać liczbę wersji i aksjomatów oraz żądania.
- [ ] Zapisać liczbę zainstalowanych pakietów i ich przestarzałość lub brak rozwiązania.
- [ ] Zmierzyć czas budowy bazy wiedzy **łącznie z wczytaniem pliku** oraz osobno czas rozwiązania.
- [ ] Zapisać wynik niezależnej weryfikacji; dla braku rozwiązania zaznaczyć, że nie ma stanu do sprawdzenia.
- [ ] W raporcie podać numer grupy 26 i skomentować zależność czasów od rozmiaru repozytorium.

Można dodać moduł `experiments.py`, który zbierze te dane do CSV i tabeli raportu.
Taki moduł jeszcze nie istnieje. `repo_200.json` jest przeznaczony do zadania
6.4 i nie należy do zestawu rozmiarów z 4.5.

## Zadania na 6 punktów: przygotowane elementy i brakujące funkcje

### 6.1 - instalacja do istniejącego stanu

**Już jest:** `load_state`, klasy stanu, flaga `manual`, wspólna baza wiedzy
i weryfikator. Przy instalacji do pustego środowiska pakiety żądane dostają
`manual=True`.

**Do dodania:**

- [ ] Przekazywanie stanu początkowego do instalatora oraz odczyt i zapis stanu z CLI.
- [ ] Zachowywanie informacji o pakietach ręcznych i oznaczanie żądanych pakietów jako ręczne.
- [ ] Plan zmian: instalacja, usunięcie, podniesienie albo obniżenie wersji.
- [ ] Pięć kryteriów, minimalizowanych w poniższej kolejności:

1. Liczba usuniętych pakietów.
2. Liczba zmian wersji pakietów, które pozostają zainstalowane.
3. Przestarzałość żądanych pakietów, które nie były zainstalowane.
4. Liczba nowych pakietów.
5. Przestarzałość pozostałych nowych pakietów.

Dla pustego stanu wynik ma odpowiadać kryteriom 4.3. Obecne `install`
nie przyjmuje stanu początkowego, a zapis stanu do pliku nie jest zaimplementowany.
Główne miejsca do rozszerzenia: `installer.py`, `loaders.py` i `__main__.py`.

### 6.2 - usuwanie i autoremove

**Do dodania:** operacja usuwania zbioru pakietów `P`, odczytywanego z pliku
z jedną nazwą pakietu w linii. Żaden pakiet z `P` nie może pozostać
zainstalowany. Pakiety zależne trzeba usunąć lub zmienić ich wersję.

Kryteria minimalizowane kolejno:

1. Liczba usuniętych pakietów ręcznych spoza `P`.
2. Liczba zmian wersji.
3. Liczba nowych pakietów.
4. Liczba usuniętych pakietów.

Opcja `autoremove` zmienia **czwarte** kryterium na minimalizację liczby
wszystkich zainstalowanych pakietów. Dzięki temu znikają też niepotrzebne
zależności. Każdy wynik musi przejść `verify_state` i mieć plan zmian.
Możliwy nowy moduł: `remover.py`; obecnie go nie ma.

### 6.3 - wyjaśnianie braku rozwiązania

**Już jest:** czytelne etykiety `Axiom.label`, identyfikatory `Axiom.name`
oraz `KnowledgeBase.add_to_solver(..., tracked=True)` do śledzenia aksjomatów.

**Do dodania:**

- [ ] Osobne sprawdzanie sprzeczności za pomocą `z3.Solver`, ze śledzeniem również żądań użytkownika.
- [ ] Odczyt `unsat_core` i mapowanie jego elementów na czytelne etykiety.
- [ ] Zapewnienie minimalności: po usunięciu dowolnego elementu rdzenia pozostałe warunki mają być spełnialne.
- [ ] Wypisanie wyjaśnienia dla `app==2.0` razem z `tool` w repozytorium przykładowym.
- [ ] Wyjaśnienia przypadków bez rozwiązania z 4.5; jeśli ich nie ma, skonstruowanie kilku przykładów.

Chodzi o rdzeń **minimalny względem zawierania**, a nie koniecznie rdzeń
o najmniejszej liczbie elementów. Samo posiadanie etykiet i `tracked=True`
nie realizuje jeszcze tego zadania. Możliwy nowy moduł: `explanations.py`.

### 6.4 - odtwarzalny scenariusz operacji

- [ ] Na [repo_200.json](repos/repos/k26/repo_200.json) zacząć od pustego stanu.
- [ ] Wykonać co najmniej 10 losowych operacji: instalacje oraz usunięcia z `autoremove` i bez niego.
- [ ] Ustalić i podać ziarno generatora losowego.
- [ ] Zweryfikować każdy stan pośredni funkcją `verify_state`.
- [ ] W raporcie podać dla każdej operacji liczbę zmian, liczbę pakietów,
  liczbę pakietów ręcznych i czas.

Ten eksperyment wymaga najpierw ukończenia 6.1 i 6.2. Można go dołączyć
do planowanego modułu `experiments.py`.

## Zadania na 8 punktów: co trzeba dodać

### 8.1 - aktualizacja

**Do dodania:** aktualizacja zbioru zainstalowanych pakietów `P` podanego
w pliku. Brak pliku oznacza aktualizację wszystkich pakietów.
Pakiety ręczne oraz pakiety z `P` muszą pozostać zainstalowane.

Kryteria minimalizowane kolejno:

1. Przestarzałość pakietów z `P`.
2. Liczba usuniętych pakietów.
3. Liczba zmian wersji pakietów spoza `P`.
4. Liczba nowych pakietów.
5. Przestarzałość wszystkich pakietów.

Do wykorzystania będą baza wiedzy, weryfikator i obsługa stanów z 6.1.
Potrzebne są nowe ograniczenia, cele optymalizacji i komenda CLI.
Możliwy nowy moduł: `updater.py`.

### 8.2 - konflikty aktualizacji i front Pareto

- [ ] Dla każdego pakietu z `P` znaleźć najnowszą wersję osiągalną osobno,
  przy zachowaniu pakietów ręcznych.
- [ ] Sprawdzić, czy te wersje da się zainstalować jednocześnie.
- [ ] Jeśli nie, zgłosić konflikt i wyjaśnić go rdzeniem sprzeczności z 6.3.
- [ ] Wypisać wszystkie rozwiązania nieporównywalne, czyli front Pareto
  względem przestarzałości pakietów w konflikcie.

Przykład kontrolny z PDF: dla stanu `a 1.0 manual`, `b 1.0 manual`
front składa się z `{a 2.0, b 1.0}` i `{a 1.1, b 2.0}`.
Aktualizacja samego `a` powinna umożliwić `a 2.0` bez tego konfliktu.
Obecne `priority="lex"` wybiera jeden kompromis i nie wyznacza frontu Pareto.

### 8.3 - dane z PyPI

**Do dodania:** obsługa `pypi_data.json` opisanego w instrukcji
(92 pakiety, 3330 wersji). Tego pliku nie ma obecnie w katalogu projektu;
trzeba pozyskać go z materiałów do zadania.

- [ ] Odczyt pól `requires_dist`, `requires_python` i `meta.environment`.
- [ ] Interpretacja wersji i wymagań zgodnie z PEP 440 / PEP 508 przez bibliotekę `packaging`.
- [ ] Pomijanie wersji niezgodnych ze środowiskiem docelowym przez `requires_python`.
- [ ] Obliczanie znaczników środowiska dla danych z `meta.environment`.
- [ ] Pomijanie dodatków `extras`, zgodnie z poleceniem.
- [ ] Zachowanie działania instalacji, usuwania, aktualizacji, weryfikacji i wyjaśnień na nowych danych.
- [ ] Scenariusz w raporcie z czasami wczytania i rozwiązania, np. instalacja
  najstarszych dostępnych `pandas` i `requests`, doinstalowanie `boto3` oraz
  `aiobotocore`, aktualizacje, usunięcie `botocore` i wyjaśnienie sprzeczności
  najnowszego `boto3` z najstarszym `botocore`.

Aktualny parser i `versions.py` obsługują uproszczony format projektu,
więc nie wystarczą do danych PyPI. Potrzebny będzie osobny loader/adapter
(np. `pypi_loader.py`) oraz rozszerzenie porównywania wersji i dopasowywania
wymagań. Oryginalny loader powinien nadal walidować format z poziomu 4.

## Proponowana kolejność dalszej pracy

1. Domknąć walidację 4.1, wykonać pomiary 4.5 i zebrać raport dla progu 4.
2. Dodać zapis stanu i plan zmian, następnie instalację do istniejącego stanu (6.1).
3. Dodać usuwanie z `autoremove` (6.2) oraz wyjaśnianie sprzeczności (6.3).
4. Przeprowadzić scenariusz 6.4.
5. Dodać aktualizację 8.1, następnie analizę konfliktów i front Pareto 8.2.
6. Obsłużyć dane PyPI i wykonać scenariusz 8.3.

Do oddania na wybranym progu potrzebne są kod z instrukcją uruchomienia,
przykładowe pliki wejściowe oraz raport z wynikami i komentarzem. Projekt
trzeba także zaprezentować prowadzącemu. Zalecane testy automatyczne są już
w [tests](tests). Dowód NP-zupełności z końca PDF jest zadaniem dodatkowym,
nieobowiązkowym.

## Testy

```powershell
python -m unittest discover -s tests -v
```

Testy obejmują walidację błędnych plików, przykłady z instrukcji oraz
porównanie solvera i weryfikatora z wyczerpującym przeglądem stanów małych
repozytoriów. Nie wymagają dodatkowych bibliotek poza `z3-solver`.

Sprawdzenie stylu i typów (konfiguracja w `pyproject.toml`):

```powershell
python -m pip install -r requirements-dev.txt
python -m ruff check package_manager tests
python -m ruff format --check package_manager tests
python -m mypy
```

Kontrola typów pomija brak deklaracji typów w zewnętrznej bibliotece Z3;
pozostałe moduły projektu są sprawdzane w trybie strict.
