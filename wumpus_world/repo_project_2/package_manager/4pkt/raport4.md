# Projekt 2 – menedżer pakietów: raport (próg 4 punkty)

**Grupa: k = 26**
**Autorzy:** Milana Ronchyk i Anna Przyłucka
**Narzędzia:** Python 3.12, solver Z3 (`z3-solver`), testy `pytest`

Surowe wyniki wszystkich sprawdzeń zapisał skrypt `4pkt/check4.py` w katalogu `4pkt/results/` (wynik: 6 z 6 sprawdzeń `PASS`).

## 1. Zakres

Zrealizowano zadania 4.1–4.5 (instalacja zbioru żądań do pustego środowiska):

| Zadanie | Gdzie w kodzie |
|---|---|
| 4.1 wczytywanie, klasy, walidacja | `models.py`, `json_reader.py`, `loaders.py`, `requirements_parser.py`, `versions.py` |
| 4.2 baza wiedzy A1–A3 | `knowledge_base.py` |
| 4.3 optymalna instalacja | `installer.py` (`install`, `solve`) |
| 4.4 weryfikacja bez solvera | `verification.py` |
| 4.5 eksperymenty | `experiments.py` |

## 2. Wczytywanie i walidacja (4.1)

Repozytorium, wymagania i stan mają własne klasy (`Repository`, `PackageVersion`, `Requirement`, `VersionConstraint`, `Dependency`, `EnvironmentState`, `InstalledPackage`). Pliki są sprawdzane podczas wczytywania, a komunikat zawiera nazwę pliku i miejsce błędu, np. `packages['app'].versions['2.0'].requires[1]`. Błędy składni JSON wskazują linię i kolumnę, a błędy w pliku żądań – numer linii.

Odrzucane są: niepoprawny JSON, powtórzone klucze obiektu (przez `object_pairs_hook`), brak pola `packages`, nieznane pola, wartości złego typu, niepoprawne nazwy, wersje i operatory, powtórzone wersje (także `1.0` i `1.0.0`), powtórzone pakiety (także `Foo_Bar` i `foo-bar`), pakiet wymagający samego siebie lub z sobą konfliktujący oraz pakiet bez żadnej wersji. Plik z BOM (zapisany np. w Notatniku) jest poprawnie odczytywany. Wymaganie, któremu nie odpowiada żadna wersja, jest dozwolone i powoduje ostrzeżenie; taka wersja jest po prostu nieinstalowalna.

Przykładowe komunikaty (z `4pkt/results/4_1_walidacja.txt`, gdzie jest 14 niepoprawnych plików):

| Błąd w pliku | Komunikat |
| --- | --- |
| niepoprawny JSON | `repo.json:1:14: Expecting value` |
| brak pola `packages` | `$.packages: brak wymaganego pola.` |
| `requires` nie jest listą | `packages['a'].versions['1.0'].requires: oczekiwano listy napisów.` |
| niepoprawny operator w drugim wymaganiu | `packages['app'].versions['2.0'].requires[1]: Niepoprawne ograniczenie wersji w wymaganiu 'x =>1'` |
| wersje `1.0` i `1.0.0` | `packages['a'].versions['1.0.0']: wersja powtarza '1.0'.` |
| pakiety `Foo_Bar` i `foo-bar` | `packages['foo-bar']: powtórzony pakiet po normalizacji nazwy: 'foo-bar'.` |
| pakiet wymaga samego siebie | `packages['a'].versions['1.0'].requires[0]: pakiet nie może wymagać samego siebie.` |
| powtórzony klucz obiektu | `packages['a'].versions['1.0']: powtórzony klucz '1.0'.` |
| pusty obiekt `versions` | `packages['a'].versions: pakiet musi mieć co najmniej jedną wersję.` |
| błędne żądanie w pliku żądań | `requests.txt:4: Niepoprawne ograniczenie wersji w wymaganiu 'lib =>1'` |

Nazwy są normalizowane (wielkość liter, `-`, `_` i `.` są równoważne), a wersje porównywane jako ciągi liczb po usunięciu końcowych zer, więc `1.10 > 1.9` oraz `1.0 = 1.0.0`.

## 3. Kodowanie w logice zdań (4.2)

Dla każdej wersji `v` pakietu `p` w repozytorium tworzymy zmienną logiczną `p==v` („zainstalowano pakiet p w wersji v”). Aksjomaty:

- **A1 (co najwyżej jedna wersja):** dla pakietu o więcej niż jednej wersji `AtMost(p==v1, p==v2, …, 1)`.
- **A2 (zależności):** dla wersji `p==v` i każdego elementu jej listy `requires` mamy `p==v → (x1 ∨ x2 ∨ …)`, gdzie `xi` to wszystkie zmienne wersji spełniających którąkolwiek alternatywę wymagania. Gdy nic nie pasuje, alternatywa jest pusta (`Or()` jest fałszem), więc `p==v` nie da się zainstalować.
- **A3 (konflikty):** dla każdego elementu `conflicts` i każdej pasującej wersji `q==w` mamy `p==v → ¬(q==w)`.

Każdy aksjomat ma czytelną etykietę (`Axiom.label`), użyteczną później w wyjaśnianiu braku rozwiązania, np. `app==2.0 wymaga lib >=2.0` albo `legacy==1.0 konfliktuje z util >=2.0 (blokuje util==2.0)`.

### Przykładowe formuły dla `repo_example.json` (20 wersji, 24 aksjomaty)

| Aksjomat | Formuła |
|---|---|
| A1, `lib` | `AtMost(lib==1.0, lib==1.5, lib==2.0, 1)` |
| A1, `util` | `AtMost(util==1.0, util==2.0, 1)` |
| A2, `app==1.0` wymaga `lib <2.0` | `app==1.0 → (lib==1.0 ∨ lib==1.5)` |
| A2, `app==2.0` wymaga `lib >=2.0` | `app==2.0 → lib==2.0` |
| A2, `app==2.0` wymaga `util` | `app==2.0 → (util==1.0 ∨ util==2.0)` |
| A2, `lib==2.0` wymaga `util >=2.0` | `lib==2.0 → util==2.0` |
| A2, `tool==1.1` wymaga `json-fast \| json-slow >=1.0` | `tool==1.1 → (json-fast==1.0 ∨ json-fast==2.0 ∨ json-slow==1.0)` |
| A2, `a==2.0` wymaga `b <2.0` | `a==2.0 → b==1.0` |
| A3, `legacy==1.0` konfliktuje z `util >=2.0` | `legacy==1.0 → ¬util==2.0` |
| A3, `json-fast==1.0` konfliktuje z `json-slow` | `json-fast==1.0 → ¬json-slow==1.0` |

W tym repozytorium jest 8 aksjomatów A1, 13 aksjomatów A2 i 3 aksjomaty A3.

## 4. Instalacja do pustego środowiska (4.3)

Żądania są twardymi ograniczeniami: dla żądania `r` dodajemy alternatywę zmiennych wszystkich wersji pasujących do `r`. Całość rozwiązuje `z3.Optimize` z `priority="lex"`, czyli kryteria są minimalizowane leksykograficznie:

1. przestarzałość pakietów żądanych,
2. liczba wszystkich zainstalowanych pakietów,
3. przestarzałość pozostałych pakietów.

Przestarzałość wersji to jej pozycja na liście wersji pakietu posortowanej od najnowszej (0 = najnowsza), a dla zbioru pakietów – suma po zainstalowanych wersjach. Jeśli nie ma rozwiązania (`unsat`), program wypisuje „Brak rozwiązania dla podanych żądań”; wynik `unknown` (np. przekroczenie limitu czasu) jest zgłaszany jako błąd.

Wyniki dla przykładowego repozytorium zgadzają się z tabelą z treści zadania:

| Żądanie | Wynik |
|---|---|
| `app` | app 2.0, lib 2.0, util 2.0 |
| `tool` | tool 1.1, lib 1.0, json-slow 1.0 |
| `app`, `tool` | app 1.0, tool 1.1, lib 1.0, json-slow 1.0 |
| `app`, `legacy` | app 1.0, legacy 1.0, lib 1.0 |
| `app==2.0`, `tool` | brak rozwiązania |

## 5. Weryfikacja bez solvera (4.4)

`verification.verify_state` nie używa Z3. Sprawdza, czy każda zainstalowana wersja istnieje w repozytorium, czy żaden pakiet nie występuje dwa razy, czy spełnione są wszystkie wymagania i czy nie ma konfliktów, a opcjonalnie także czy spełnione są żądania. Zwraca listę wszystkich naruszeń. `installer.solve` wywołuje ją na każdym stanie zwróconym przez solver; przy niepustej liście zgłasza błąd.

Sprawdzenie weryfikatora na stanach z błędami (`4pkt/results/4_4_weryfikacja.txt`); poprawny stan nie daje żadnego naruszenia, a w pozostałych wszystkie naruszenia są wypisane:

| Stan | Wykryte naruszenie |
| --- | --- |
| `app 2.0` samo | `app==2.0 wymaga lib >=2.0.` oraz `app==2.0 wymaga util.` |
| `legacy 1.0` z `util 2.0` | `legacy==1.0 konfliktuje z util==2.0 (util >=2.0).` |
| `ghost 1.0` | `Brak ghost==1.0 w repozytorium.` |
| `util 9.9` | `Brak util==9.9 w repozytorium.` |
| `util 1.0` przy żądaniu `app` | `Niespełnione żądanie: app.` |
| `util` zainstalowany dwa razy | `Pakiet util jest zainstalowany więcej niż raz.` |

## 6. Testy

Polecenie `python -m pytest` uruchamia 30 testów (wszystkie przechodzą):

- 13 niepoprawnych plików repozytorium z oczekiwanym komunikatem, ścieżka błędu w dokumencie, plik z BOM, numer linii w pliku żądań oraz komentarze i puste linie,
- cała tabela wyników z treści zadania,
- porównanie wyniku solvera z **przeglądem wszystkich stanów** (repozytorium przykładowe ma ok. 46 tys. stanów) dla sześciu zestawów żądań – trzy kryteria są identyczne,
- plan zmian i zapis stanu.

## 7. Eksperyment (4.5)

Dane: katalog `data/` (to samo co `repos/k26` z materiałów prowadzącego). Dla każdego N zainstalowano w pustym środowisku zbiór żądań z `requests_N.txt` w repozytorium `repo_N.json`. Czas budowy bazy wiedzy obejmuje wczytanie plików. Polecenie:

```
python -m package_manager.experiments data --group 26 --timeout 600
```

Wyniki zapisuje `4pkt/results/4_5_eksperyment.txt`.

| N | wersje | aksjomaty (A1+A2+A3) | ostrzeżenia | żądanie |
|---|---|---|---|---|
| 10 | 46 | 36 (10+13+13) | 0 | `pycparser`, `toml`, `krypton-tools` |
| 30 | 198 | 187 (27+160+0) | 3 | `rfc3986`, `six`, `xenon-tools` |
| 100 | 1318 | 1442 (95+1317+30) | 141 | `rfc3987`, `iniconfig-jasper`, `zephyr-kit` |
| 300 | 6604 | 5784 (294+5432+58) | 148 | `cffi`, `jsonschema-krypton`, `thistle-client` |
| 1000 | 21096 | 14776 (992+13726+58) | 473 | `typing-extensions`, `dragonmapper-jasper`, `mosaic-kit` |

**Wyniki** (w każdym z pięciu przypadków rozwiązanie istnieje, a zwrócony stan przeszedł niezależną weryfikację bez naruszeń):

| N | liczba pakietów | przestarzałość żądanych | przestarzałość pozostałych | czas budowy bazy [s] | czas rozwiązania [s] | weryfikacja |
|---|---|---|---|---|---|---|
| 10 | 4 | 0 | 0 | 0,004 | 0,020 | OK |
| 30 | 4 | 0 | 1 | 0,024 | 0,073 | OK |
| 100 | 4 | 0 | 0 | 0,248 | 0,969 | OK |
| 300 | 38 | 0 | 19 | 1,504 | 4,554 | OK |
| 1000 | 6 | 0 | 2 | 3,495 | 5,924 | OK |

Czasy zależą od komputera i od jego obciążenia, więc różnią się między uruchomieniami (patrz komentarz poniżej).

### Komentarz

**Czas budowy bazy wiedzy** rośnie z rozmiarem repozytorium mniej więcej proporcjonalnie do liczby wersji i zależności. Od N = 100 do N = 1000 liczba wersji rośnie 16 razy, a czas budowy 14 razy; od N = 300 do N = 1000 wersji jest 3,2 razy więcej, a czas budowy rośnie 2,3 razy. Wartość dla N = 10 (0,004 s) jest zbyt mała, żeby wyciągać z niej wnioski o proporcjach.

**Czas rozwiązania** w tym pomiarze rośnie z rozmiarem, ale wolniej niż liczba wersji na dużych repozytoriach: od N = 100 do N = 300 wersji jest 5 razy więcej, a czas rośnie 4,7 razy; od N = 300 do N = 1000 wersji jest 3,2 razy więcej, a czas tylko 1,3 razy. Czas zależy też od struktury żądań, a nie tylko od rozmiaru: dla N = 300 potrzeba 38 pakietów (przestarzałość pozostałych 19), a dla N = 1000 tylko 6 pakietów. Na to wskazuje również wcześniejszy pomiar na tym samym komputerze, w którym czas dla N = 300 (8,3 s) był dłuższy niż dla N = 1000 (6,2 s); wahania wynikają więc także z obciążenia komputera. Mimo że problem instalowalności jest NP-zupełny, na tych danych nie obserwujemy gwałtownego wzrostu czasu: największy przypadek (21 tys. wersji) rozwiązuje się w ok. 6 s. Wniosek opiera się na jednym repozytorium dla każdego rozmiaru, więc należy go traktować ostrożnie.

Dane zawierają „trudne sytuacje”: ostrzeżenia dotyczą wymagań i konfliktów, którym nie odpowiada żadna wersja w repozytorium. Takie wersje są nieinstalowalne, ale nie przeszkadzają w pozostałej części problemu. W żadnym z pięciu przypadków nie wystąpił brak rozwiązania.

## 8. Uruchomienie

```
python -m pip install -r requirements.txt
python -m package_manager examples/repo_example.json examples/requests_example.txt
python -m package_manager data/repo_10.json data/requests_10.txt
python -m package_manager.experiments data --group 26 --timeout 600
python -m pytest
python 4pkt/check4.py
```

Skrypt `4pkt/check4.py` uruchamia wszystkie sprawdzenia progu 4 i zapisuje wyniki w katalogu `4pkt/results/` (walidacja z komunikatami błędów, formuły bazy wiedzy, tabela z treści zadania, weryfikator na niepoprawnych stanach, eksperyment, wynik `pytest`).
