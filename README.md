# Inżynieria wiedzy

Projekty i materiały z przedmiotu **Inżynieria wiedzy**. Repozytorium obejmuje
planowanie, wnioskowanie logiczne, rozwiązywanie zależności oraz modelowanie
probabilistyczne.

## Projekty

| Projekt | Zadanie | Metody i narzędzia |
| --- | --- | --- |
| [Projekt 1 – Świat klocków](blocks_world_basic/README.md) | Znalezienie planu przejścia od układu początkowego do docelowego | DFS z nawrotami, weryfikacja planu |
| [Świat Wumpusa](wumpus_world/README.md) | Planowanie działań agenta na podstawie obserwacji w jaskini | ASP, Clingo, porównanie strategii ryzyka |
| [Projekt 2 – Menedżer pakietów](wumpus_world/repo_project_2/README.md) | Dobór wersji pakietów spełniających żądania, zależności i konflikty | Z3, optymalizacja leksykograficzna, niezależny weryfikator |
| [Projekt 3 – Sieć bayesowska studentów](sieci_bayesowskie/projekt_3/README.md) | Uczenie modelu z niepełnych danych i odpowiadanie na zapytania probabilistyczne | pgmpy, MLE, EM, Hill Climb z BIC, zapytania P i MAP |

Każdy przykład uruchamiania zaczyna się w głównym katalogu repozytorium
i korzysta z PowerShella oraz Pythona 3.11.

## Świat klocków

Program wczytuje i sprawdza oba układy klocków, wyszukuje sekwencję legalnych
ruchów i sprawdza ją niezależnym weryfikatorem. Katalog zawiera przykłady
poprawnych i błędnych stanów, eksperymenty oraz wizualizację DFS krok po kroku.
[Raport](blocks_world_basic/reports/raport.md) · [Wizualizacja](blocks_world_basic/other_resources/visualizations/dfs-krok-po-kroku.html)

```powershell
Set-Location blocks_world_basic
py -3.11 -m src.main examples/simple_3.txt
```

## Świat Wumpusa

Agent używa obserwacji oraz reguł ASP do wnioskowania o bezpiecznych polach
i zagrożeniach. Można grać ręcznie, obserwować decyzje agenta albo porównać
strategie ostrożną, heurystyczną i opartą na zliczaniu modeli.
[Instrukcja wizualizatora](wumpus_world/README.md) · [Notatnik laboratoryjny](wumpus_world/lab.ipynb)

```powershell
Set-Location wumpus_world
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe visualizer.py
```

Plansza działa pod adresem `http://127.0.0.1:8765`. Symulację w terminalu
można uruchomić poleceniem `.\.venv\Scripts\python.exe simulate.py --aima`.

## Menedżer pakietów

Instalator wczytuje repozytorium JSON oraz listę żądań, po czym wybiera wersje
pakietów dla pustego środowiska. Uwzględnia zależności alternatywne i konflikty,
optymalizuje dobór pakietów w Z3 i weryfikuje znalezione rozwiązanie.
W katalogu są dane przykładowe i zestaw `k26` do eksperymentów.
[Zakres projektu i aktualny stan](wumpus_world/repo_project_2/README.md) · [Kodowanie bazy wiedzy](wumpus_world/repo_project_2/kodowanie_bazy_wiedzy.md)

```powershell
Set-Location wumpus_world/repo_project_2
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m package_manager repo_example.json requests_example.txt
```

## Sieć bayesowska studentów

Program wczytuje zestaw `k26`, uczy sieć z danych z brakami i ocenia ją na
oddzielnym zbiorze. Wariant na 4 pkt obejmuje model ekspercki, zapytania
o prawdopodobieństwo i MAP oraz ocenę predykcji. Wariant na 6 pkt dodatkowo
porównuje estymatory MLE i EM oraz trzy metody uczenia struktury. Program
zapisuje raport Markdown i odpowiedzi w JSON-ie.
[Opis kodu](sieci_bayesowskie/projekt_3/OPIS_KODU.md) · [Wyniki dla 4 pkt](sieci_bayesowskie/projekt_3/results/4_pkt/report.md) · [Wyniki dla 6 pkt](sieci_bayesowskie/projekt_3/results/6_pkt/report.md) · [Wprowadzenie do pgmpy](sieci_bayesowskie/pgmpy_intro.ipynb)

Opcja `--output` kieruje nowe wyniki do dwóch osobnych katalogów.

```powershell
Set-Location sieci_bayesowskie/projekt_3
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install "pgmpy==1.1.2"
$env:PYTHONHASHSEED = "0"
.\.venv\Scripts\python.exe -m student_bn --level 4 --output results/local_4_pkt
.\.venv\Scripts\python.exe -m student_bn --level 6 --output results/local_6_pkt
```
