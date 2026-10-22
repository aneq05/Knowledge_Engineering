# Inżynieria wiedzy

> Repozytorium projektów, eksperymentów i notatek z przedmiotu **Inżynieria
> wiedzy**.

To repo będzie rozwijane przez cały semestr — kolejne laboratoria i projekty
będą pojawiać się tutaj jako osobne katalogi. Oprócz kodu znajdują się tu
raporty, materiały pomocnicze, przykładowe dane oraz interaktywne wizualizacje,
które pomagają prześledzić działanie algorytmów krok po kroku.

## Zawartość

| Projekt | Temat | Najważniejsze elementy |
| --- | --- | --- |
| [`blocks_world_basic/`](./blocks_world_basic/) | **Świat klocków** | walidacja stanów, DFS z backtrackingiem, weryfikacja planu, eksperymenty i wizualizacja |
| [`wumpus_world/`](./wumpus_world/) | **Świat Wumpusa** | agent, wnioskowanie w Clingo/ASP, strategie ryzyka, gra i wizualizator webowy |
| [`wumpus_world/repo_project_2/`](./wumpus_world/repo_project_2/) | **Menedżer pakietów** | przykładowe repozytoria pakietów, zależności, konflikty i dane do projektu 2 |

### 1. Świat klocków

Implementacja podstawowego problemu planowania: z układu początkowego trzeba
przejść do układu docelowego, wykonując poprawne ruchy. Projekt zawiera:

- model stanu oraz reguły przenoszenia klocków,
- sprawdzanie niepoprawnych danych wejściowych, między innymi cykli i
  nieistniejących klocków,
- przeszukiwanie DFS z backtrackingiem,
- niezależną weryfikację znalezionego planu,
- testy jednostkowe i eksperymenty dla różnych rozmiarów problemu,
- interaktywną wizualizację DFS „krok po kroku”.

Szczegóły uruchamiania znajdują się w
[`blocks_world_basic/README.md`](./blocks_world_basic/README.md).

### 2. Świat Wumpusa

Interaktywna implementacja klasycznego środowiska z książki Russella i Norviga.
Agent otrzymuje wyłącznie percepcje ze świata i na ich podstawie buduje wiedzę
o bezpiecznych oraz potencjalnie niebezpiecznych polach. W projekcie można:

- grać ręcznie albo obserwować działanie agenta,
- porównywać strategie ostrożną, ryzykowną i opartą na zliczaniu modeli,
- uruchamiać świat AIMA, scenariusz porównania ryzyka lub losową jaskinię,
- śledzić percepcje, wnioski, plan i fakty ASP,
- wykonywać symulacje seryjne i zbierać statystyki.

Szczegółowy opis obsługi, skrótów klawiszowych i testów jest w
[`wumpus_world/README.md`](./wumpus_world/README.md).

### 3. Menedżer pakietów

Katalog [`repo_project_2/`](./wumpus_world/repo_project_2/) zawiera dane
wykorzystywane w projekcie dotyczącym rozwiązywania zależności pakietów:

- przykładowy opis repozytorium w JSON,
- przykładowy stan środowiska,
- przykładowe żądania instalacji,
- wygenerowane zbiory repozytoriów o różnych rozmiarach,
- treść instrukcji projektu w pliku PDF.

## Szybki start

### Wymagania

- Python **3.10+**,
- PowerShell lub inny terminal,
- `clingo` **5.7–5.x** dla projektu Świat Wumpusa.

Najbezpieczniej używać osobnego środowiska wirtualnego dla każdego projektu,
ponieważ tylko Świat Wumpusa ma obecnie dodatkową zależność Pythonową.

### Świat klocków

```powershell
cd blocks_world_basic
py -3 -m src.main examples/simple_3.txt
py -3 -m unittest discover -s tests -v
```

Interaktywną wizualizację można otworzyć bez serwera:

```powershell
start other_resources/visualizations/dfs-krok-po-kroku.html
```

### Świat Wumpusa

```powershell
py -3 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe visualizer.py
```

Po uruchomieniu wizualizator będzie dostępny pod adresem
`http://127.0.0.1:8765`. Alternatywnie można uruchomić symulację terminalową:

```powershell
.venv/Scripts/python.exe simulate.py --aima
```

## Organizacja repozytorium

```text
.
├── blocks_world_basic/
│   ├── src/                 # implementacja algorytmu
│   ├── tests/               # testy automatyczne
│   ├── examples/            # dane wejściowe
│   ├── reports/             # raporty i notatki
│   └── other_resources/     # wizualizacje i materiały dodatkowe
├── wumpus_world/
│   ├── agent.py             # agent i jego wiedza
│   ├── inference.py         # wnioskowanie
│   ├── world.py             # środowisko
│   ├── visualizer.py        # lokalny serwer gry
│   └── repo_project_2/      # dane projektu menedżera pakietów
└── requirements.txt
```

## Podejście do projektów

Wspólnym motywem repozytorium jest reprezentowanie wiedzy o świecie i
wykorzystywanie jej do podejmowania decyzji:

1. **modelowanie** — stan, reguły i ograniczenia problemu,
2. **wnioskowanie lub przeszukiwanie** — DFS, backtracking, ASP i Clingo,
3. **weryfikacja** — testy, niezależne sprawdzanie planów i eksperymenty,
4. **wizualizacja** — prezentowanie wyników w sposób łatwy do prześledzenia.

## Status

| Obszar | Status |
| --- | --- |
| Świat klocków — wariant podstawowy | gotowy |
| Świat Wumpusa — agent i wizualizator | gotowy |
| Menedżer pakietów — dane do projektu | w toku |
| Kolejne projekty z zajęć | planowane |

## Rozwój repozytorium

Nowe projekty będą dodawane w osobnych katalogach. Każdy z nich powinien mieć
własny README z krótkim opisem, instrukcją uruchomienia, testami i informacją o
strukturze plików. Dzięki temu główny README pozostanie mapą repozytorium, a
szczegóły nie będą mieszać się z opisem pozostałych projektów.

---

Repozytorium ma charakter edukacyjny i będzie na bieżąco uzupełniane wraz z
kolejnymi tematami realizowanymi na zajęciach.
