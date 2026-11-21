# Projekt 2 – menedżer pakietów: raport (próg 6 punktów)

**Grupa: k = 26**
**Autorzy:** Milana Ronchyk i Anna Przyłucka

Próg 6 obejmuje także zadania na 4 punkty; ich opis i wyniki są w `raport4.md`. Ten raport dotyczy zadań 6.1–6.4. Surowe wyniki wszystkich sprawdzeń zapisał skrypt `6pkt/check6.py` w katalogu `6pkt/results/`.

## 1. Co zostało dodane

| Zadanie | Gdzie w kodzie |
|---|---|
| wspólne kodowanie zmian względem stanu początkowego | `solving.py` (`Encoding`, `encode`, `solve_lex`, `read_state`) |
| 6.1 instalacja do istniejącego stanu | `operations.py` (`install_with_state`), `loaders.py` (`load_state`), `plan.py` |
| 6.2 usuwanie i autoremove | `operations.py` (`remove_packages`), `loaders.py` (`load_names`) |
| 6.3 wyjaśnianie braku rozwiązania | `explanations.py` (`explain`, `explain_requests`) |
| 6.4 scenariusz losowy | `scenario.py` |
| interfejs wiersza poleceń | `__main__.py` (polecenia `install`, `remove`, `explain`) |

## 2. Wspólne kodowanie (`solving.py`)

Aksjomaty A1–A3 z zadania 4.2 są takie same dla wszystkich operacji. Różnią się twarde ograniczenia i lista kryteriów. Względem stanu początkowego S0 dla każdego pakietu `p` definiujemy wyrażenia logiczne nad zmiennymi `p==v`:

- `installed(p)` – zainstalowana jest którakolwiek wersja `p`, czyli alternatywa wszystkich zmiennych `p==v`,
- `removed(p)` dla `p` z S0: `¬installed(p)`,
- `changed(p)` dla `p` z S0: `installed(p) ∧ ¬(p == wersja z S0)` – pakiet zostaje, ale ma inną wersję (wersje `1.0` i `1.0.0` są tą samą wersją),
- `new(p)` dla `p` spoza S0: `installed(p)`.

Kryteria są sumami `If(wyrażenie, 1, 0)` albo przestarzałości wersji. Optymalizacja leksykograficzna (`z3.Optimize`, `priority="lex"`) minimalizuje je po kolei. Stan początkowy jest najpierw sprawdzany weryfikatorem; niepoprawny stan jest zgłaszany jako błąd. Każdy wynik operacji przechodzi `verify_state` przed zwróceniem (funkcja `_finish`), a program wypisuje plan zmian (instalacja, usunięcie, podniesienie lub obniżenie wersji) i może zapisać nowy stan do pliku. Pakiety żądane stają się ręczne (`manual`), a pakiety już ręczne pozostają ręczne.

## 3. Zadanie 6.1 – instalacja do istniejącego stanu

Kryteria (leksykograficznie): (1) liczba usuniętych pakietów, (2) liczba zmian wersji pakietów, które zostają, (3) przestarzałość żądanych pakietów, które nie były zainstalowane, (4) liczba nowych pakietów, (5) przestarzałość pozostałych nowych pakietów. Żądania są twardymi ograniczeniami.

**Pusty stan.** Kryteria 1 i 2 są wtedy równe zeru, a kryteria 3–5 odpowiadają kryteriom z 4.3 (przestarzałość żądanych, liczba pakietów, przestarzałość pozostałych). Sprawdzenie na repozytorium przykładowym potwierdza, że wynik jest taki sam jak z `install` z zadania 4.3:

| Żądania | Kryteria z 4.3 | Nowe kryteria [1..5] |
|---|---|---|
| `app` | (0, 3, 0) | [0, 0, 0, 3, 0] |
| `tool` | (0, 3, 2) | [0, 0, 0, 3, 2] |
| `app`, `tool` | (1, 4, 2) | [0, 0, 1, 4, 2] |
| `app`, `legacy` | (1, 3, 2) | [0, 0, 1, 3, 2] |
| `app==2.0`, `tool` | brak rozwiązania | brak rozwiązania |

**Przykład z treści zadania.** Stan początkowy (`state_example.txt`): `app 1.0 manual`, `json-slow 1.0`, `lib 1.0`, `tool 1.1 manual`. Żądanie: `app==2.0`. Wynik jest zgodny z tabelą z treści zadania:

```
Plan zmian:
  podniesienie app 1.0 -> 2.0
  podniesienie lib 1.0 -> 2.0
  usunięcie tool 1.1
  instalacja util 2.0
```

Stan końcowy: `app 2.0 manual`, `json-slow 1.0`, `lib 2.0`, `util 2.0`. Kryteria: [1, 2, 0, 1, 0], czyli usunięto jeden pakiet (`tool`, bo wymaga `lib <2.0`, a `app 2.0` wymaga `lib >=2.0`), zmieniono dwie wersje (`app`, `lib`), `app` był już zainstalowany (kryterium 3 równe 0), doinstalowano jeden nowy pakiet (`util`) w najnowszej wersji. Pakiet `json-slow` zostaje, bo zwykła instalacja nie usuwa niepotrzebnych zależności.

## 4. Zadanie 6.2 – usuwanie i autoremove

Dla zbioru `P` (jedna nazwa pakietu w linii pliku) żaden pakiet z `P` nie może pozostać zainstalowany. Kryteria: (1) liczba usuniętych pakietów ręcznych spoza `P`, (2) liczba zmian wersji, (3) liczba nowych pakietów, (4) liczba usuniętych pakietów. Z opcją `autoremove` kryterium 4 to liczba wszystkich zainstalowanych pakietów, co usuwa także zależności, które przestały być potrzebne.

Wyniki dla stanu z `state_example.txt` zgadzają się z treścią zadania:

| Zapytanie | Plan zmian | Kryteria [1..4] |
|---|---|---|
| `remove lib` | usunięcie `app`, `lib`, `tool` | [2, 0, 0, 3] |
| `remove tool` z autoremove | usunięcie `tool`, `json-slow` | [0, 0, 0, 2] |
| `remove tool` bez autoremove | usunięcie `tool` | [0, 0, 0, 1] |

Przy `remove lib` pakiety `app` i `tool` zależą od `lib` w każdej swojej wersji, więc muszą zniknąć, dlatego kryterium 1 równa się 2 (oba są ręczne). Zostaje tylko `json-slow`. Przy `remove tool` bez autoremove zostaje `json-slow`, choć nikt go już nie potrzebuje; z `autoremove` solver minimalizuje liczbę wszystkich pakietów, więc `json-slow` znika, a `app 1.0` i `lib 1.0` zostają, bo `app` jest ręczny, a `lib` jest mu potrzebny.

## 5. Zadanie 6.3 – wyjaśnianie braku rozwiązania

Aksjomaty (z etykietami czytelnymi dla człowieka) i żądania użytkownika zapisujemy jako formuły `g → φ`, gdzie `g` jest zmienną-strażnikiem. Solver `z3.Solver` sprawdza spełnialność przy założeniu wszystkich strażników. Jeśli zbiór jest sprzeczny, `unsat_core` zwraca podzbiór strażników, a my mapujemy je z powrotem na etykiety.

Rdzeń z solvera nie musi być minimalny, więc dodatkowo stosujemy **minimalizację przez usuwanie**: dla każdego elementu sprawdzamy, czy bez niego zbiór nadal jest sprzeczny. Jeśli tak, element jest zbędny i odrzucamy go (rdzeń może się wtedy jeszcze skrócić). Po zakończeniu usunięcie dowolnego elementu daje zbiór spełnialny, czyli rdzeń jest **minimalny względem zawierania** (niekoniecznie najmniejszy liczbowo). Poprawność każdego wyniku sprawdza `check6.py` niezależnym solverem: cały rdzeń jest sprzeczny, a po usunięciu któregokolwiek elementu staje się spełnialny.

W danych grupy 26 (N = 10…1000) wszystkie żądania miały rozwiązanie, więc przypadków bez rozwiązania z zadania 4.5 nie ma. Wyjaśnienia pokazano na przykładzie z treści zadania i trzech skonstruowanych przypadkach (brak rozwiązania w tych przypadkach potwierdzono niezależnie przeglądem wszystkich stanów).

**`app==2.0` + `tool`** (przykład z treści zadania):

- żądanie użytkownika: `app ==2.0`
- żądanie użytkownika: `tool`
- `app==2.0` wymaga `lib >=2.0`
- `tool==1.1` wymaga `lib <2.0`
- `tool==1.0` wymaga `lib <2.0`
- `lib`: co najwyżej jedna wersja

Rdzeń zawiera obie wersje `tool`, ponieważ obie wymagają `lib <2.0`; gdyby jedna z nich nie wymagała, dałoby się ją wybrać. `app 2.0` potrzebuje `lib` w wersji co najmniej 2.0, a żadna wersja `tool` z taką nie współistnieje, a `lib` może być zainstalowany tylko w jednej wersji.

**`legacy` + `web==2.0`:** żądanie `web ==2.0`, żądanie `legacy`, `web==2.0` wymaga `util >=2.0`, `legacy==1.0` konfliktuje z `util >=2.0` (blokuje `util==2.0`).

**`json-fast` + `json-slow`:** oba żądania oraz konflikty `json-fast==1.0` i `json-fast==2.0` z `json-slow` (każda wersja `json-fast` konfliktuje z jedyną wersją `json-slow==1.0`).

**`a==2.0` + `b==2.0`:** oba żądania, `a==2.0` wymaga `b <2.0` oraz `b`: co najwyżej jedna wersja.

Dla żądania spełnialnego (`app`) wyjaśnienie nie jest tworzone.

## 6. Zadanie 6.4 – scenariusz losowy

Scenariusz (`scenario.py`) zaczyna od pustego stanu na `repo_200.json` (grupa 26; 200 pakietów, 4927 wersji) i wykonuje 12 operacji: pierwsze trzy to instalacje, kolejne to losowo instalacja (losowo wybrany pakiet) albo usunięcie losowo wybranego pakietu ręcznego, z `autoremove` lub bez. Ziarno generatora liczb losowych: **2026** (`random.Random(2026)`). Wybór następuje zawsze z posortowanych list, więc scenariusz jest odtwarzalny. Po każdej operacji stan jest weryfikowany przez `verify_state`; błąd przerwałby scenariusz. Żadna operacja nie zakończyła się brakiem rozwiązania. Podczas budowy bazy dla tych danych program zgłasza ostrzeżenia o wymaganiach, którym nie odpowiada żadna wersja (134 ostrzeżenia w całym przebiegu sprawdzenia); takie wersje są po prostu nieinstalowalne.

| Krok | Operacja | Zmiany | Pakiety | Ręczne | Czas [s] |
|---|---|---|---|---|---|
| 1 | install `cffi-fjord` | 2 | 2 | 1 | 2,86 |
| 2 | install `importlib-metadata` | 2 | 4 | 2 | 2,69 |
| 3 | install `pydantic-core` | 2 | 6 | 3 | 2,65 |
| 4 | remove `pydantic-core` | 1 | 5 | 2 | 1,17 |
| 5 | install `colorama-fjord` | 1 | 6 | 3 | 2,56 |
| 6 | remove `importlib-metadata` | 1 | 5 | 2 | 1,23 |
| 7 | remove `colorama-fjord` | 1 | 4 | 1 | 1,24 |
| 8 | remove `cffi-fjord --autoremove` | 4 | 0 | 0 | 2,36 |
| 9 | install `better-exceptions-fork` | 1 | 1 | 1 | 2,93 |
| 10 | install `cached-property` | 1 | 2 | 2 | 2,76 |
| 11 | install `tundra-tools` | 1 | 3 | 3 | 2,48 |
| 12 | install `idna-xenon` | 1 | 4 | 4 | 3,14 |

Obserwacje:

- Instalacja pakietu z zależnościami zmienia kilka pakietów (kroki 1–3: po dwa, bo dochodzi zależność), a pakietu bez zależności jedną (kroki 5 i 9–12).
- Usunięcie bez `autoremove` usuwa tylko wskazany pakiet i zostawia jego zależności (kroki 4, 6, 7: po jednej zmianie, liczba pakietów maleje o jeden, ręcznych o jeden).
- W kroku 8 `autoremove` usuwa pakiet ręczny i wszystkie jego zależności, które nikomu już nie służą: cztery zmiany, a środowisko jest puste. Dlatego po nim liczba pakietów wynosi 0.
- Czas jednej operacji to ok. 1–3 s (łącznie 29 s dla 12 operacji); baza wiedzy jest budowana raz, a każda operacja rozwiązuje zadanie optymalizacji nad ok. 4,9 tys. zmiennych. Zwykłe usunięcia (ok. 1,2 s) były szybsze niż instalacje (ok. 2,6–3,1 s); usunięcie z `autoremove` trwało 2,4 s. Przyczyny tej różnicy nie badaliśmy. Czasy zależą od obciążenia komputera: w jednym z wcześniejszych uruchomień ten sam scenariusz trwał ok. 67 s (3–9 s na operację), przy identycznych liczbach zmian, pakietów i pakietów ręcznych.

## 7. Weryfikacja i uruchomienie

Wszystkie sprawdzenia z tabel powyżej są powtarzalne: `6pkt/check6.py` uruchamia je i zapisuje wyniki w `6pkt/results/`. Wszystkie sprawdzenia 6.1–6.4 przeszły (`00_podsumowanie.txt`: 5 z 5, wynik `PASS` w każdym pliku wyników), a każdy plan zgadza się z tabelą z treści zadania. Wartości kryteriów, plany i tabela scenariusza w tym raporcie pochodzą z ostatniego uruchomienia `check6.py`; czasy mogą się nieznacznie różnić między uruchomieniami.

```
python 6pkt/check6.py
python -m package_manager install examples/repo_example.json examples/req_app2.txt --state examples/state_example.txt
python -m package_manager remove examples/repo_example.json examples/rm_tool.txt --state examples/state_example.txt --autoremove
python -m package_manager explain examples/repo_example.json examples/requests_example.txt
python -m package_manager.scenario data/repo_200.json
```

Zadania na próg 4 (wczytywanie, kodowanie, instalacja do pustego środowiska, weryfikacja, eksperymenty) opisuje `raport4.md`.
