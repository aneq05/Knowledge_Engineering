# Projekt 2 – menedżer pakietów

Rozwiązanie projektu 2 z inżynierii wiedzy (opis zadań: [projekt2.pdf](projekt2.pdf)).
Repozytorium pakietów jest zapisane jako baza wiedzy w logice zdań, a zapytania
(instalacja, usuwanie, wyjaśnianie braku rozwiązania) rozwiązuje solver Z3.
**Grupa: k = 26.** Autorki: Milana Ronchyk i Anna Przyłucka.

## Stan prac

| Próg | Zadania | Status | Raport i wyniki |
| --- | --- | --- | --- |
| 4 punkty | 4.1–4.5 | zrobione | [4pkt/raport4.md](4pkt/raport4.md), [4pkt/results](4pkt/results) |
| 6 punktów | 6.1–6.4 | zrobione | [6pkt/raport6.md](6pkt/raport6.md), [6pkt/results](6pkt/results) |

Dokładny opis każdego pliku i funkcji (z podziałem na progi) jest w [opis_kodu.md](opis_kodu.md).

## Uruchomienie

Wymagany jest Python 3.11 lub nowszy. W katalogu głównym projektu (najlepiej
w wirtualnym środowisku) zainstaluj zależność solvera; do testów potrzebny jest
jeszcze `pytest`:

```powershell
python -m pip install -r requirements.txt
python -m pip install pytest
```

Instalacja do pustego środowiska (próg 4) i do istniejącego stanu (próg 6):

```powershell
python -m package_manager install examples/repo_example.json examples/requests_example.txt
python -m package_manager install examples/repo_example.json examples/req_app2.txt --state examples/state_example.txt
python -m package_manager install data/repo_10.json data/requests_10.txt
```

Usuwanie (opcja `--autoremove` usuwa także zbędne zależności) i wyjaśnianie braku rozwiązania:

```powershell
python -m package_manager remove  examples/repo_example.json examples/rm_tool.txt --state examples/state_example.txt [--autoremove]
python -m package_manager explain examples/repo_example.json examples/requests_example.txt
```

Opcja `--output PLIK` zapisuje nowy stan do pliku w formacie `NAZWA WERSJA [manual]`.
Każdy wynik przechodzi niezależną weryfikację bez solvera (`verification.verify_state`).

Pliki wejściowe: plik żądań ma jedno żądanie w linii (np. `app==2.0`; puste linie i
komentarze po `#` są pomijane), plik pakietów do usunięcia ma jedną nazwę w linii.

Eksperymenty, scenariusz losowy i sprawdzenia, które zapisują wyniki do raportów:

```powershell
python -m package_manager.experiments data --group 26 --timeout 600
python -m package_manager.scenario data/repo_200.json
python 4pkt/check4.py
python 6pkt/check6.py
python -m pytest
```

Polecenia `python -m ...` uruchamiaj w katalogu głównym projektu (z aktywnym `(venv)`).
Skrypty `check4.py` i `check6.py` można też uruchomić przyciskiem ▶ w VS Code.

## Układ katalogów

| Katalog / plik | Zawartość |
| --- | --- |
| `package_manager/` | kod programu |
| `data/` | repozytoria i pliki żądań grupy 26 (`repo_N.json`, `requests_N.txt`) |
| `examples/` | pliki przykładowe z treści zadania oraz małe pliki żądań do poleceń powyżej |
| `tests/` | testy automatyczne (`python -m pytest`, 30 testów) |
| `4pkt/`, `6pkt/` | skrypty sprawdzające (`check4.py`, `check6.py`), ich wyniki w `results/` i raporty |

## Moduły (`package_manager/`)

| Plik | Odpowiedzialność | Próg |
| --- | --- | --- |
| `models.py`, `versions.py`, `requirements_parser.py` | klasy repozytorium, wymagań i stanu; porównywanie wersji; parsowanie i normalizacja nazw | 4 |
| `json_reader.py`, `loaders.py` | wczytywanie repozytorium, żądań, stanu i list pakietów z walidacją i czytelnymi komunikatami błędów | 4, 6 |
| `knowledge_base.py` | zmienne `p==v` i aksjomaty A1–A3 z etykietami | 4 |
| `installer.py` | instalacja do pustego środowiska (kryteria z 4.3) | 4 |
| `verification.py` | weryfikacja stanu bez solvera | 4 |
| `experiments.py` | eksperyment 4.5 | 4 |
| `plan.py` | plan zmian między stanami i zapis stanu | 6 |
| `solving.py` | wspólne kodowanie zmian względem stanu początkowego i optymalizacja leksykograficzna | 6 |
| `operations.py` | instalacja do stanu (6.1), usuwanie i autoremove (6.2) | 6 |
| `explanations.py` | minimalny sprzeczny podzbiór aksjomatów i żądań (6.3) | 6 |
| `scenario.py` | scenariusz losowy 6.4 (ziarno 2026) | 6 |
| `__main__.py` | wiersz poleceń (`install`, `remove`, `explain`) | 4, 6 |

## Kryteria optymalizacji

Wszystkie operacje stosują te same aksjomaty (A1: co najwyżej jedna wersja pakietu,
A2: zależności, A3: konflikty) i minimalizują kryteria leksykograficznie.
Przestarzałość wersji to jej pozycja na liście wersji pakietu posortowanej od najnowszej
(0 = najnowsza); dla zbioru pakietów jest to suma.

| Operacja | Kryteria (po kolei) |
| --- | --- |
| instalacja do pustego środowiska (4.3) | przestarzałość żądanych; liczba pakietów; przestarzałość pozostałych |
| instalacja do stanu (6.1) | usunięte pakiety; zmiany wersji pakietów, które zostają; przestarzałość żądanych, które nie były zainstalowane; nowe pakiety; przestarzałość pozostałych nowych |
| usuwanie (6.2) | usunięte pakiety ręczne spoza P; zmiany wersji; nowe pakiety; usunięte pakiety (z `--autoremove`: liczba wszystkich zainstalowanych pakietów) |

## Wyniki w skrócie

Wszystkie przykłady z treści zadania dają wyniki zgodne z tabelami z polecenia
(instalacja do pustego środowiska, `install`, `remove`, `remove --autoremove`), a
każdy wynik przeszedł niezależną weryfikację. Eksperyment 4.5 (grupa 26) rozwiązuje
największe repozytorium (21 096 wersji, 14 776 aksjomatów) w ok. 3,5 s budowy bazy i 6 s
rozwiązania; scenariusz 6.4 (12 operacji na `repo_200.json`) trwa ok. 29 s. Szczegóły
i komentarze są w raportach.
