# Blocks World — wariant podstawowy (4 punkty)

Projekt realizuje punkty 1–4 z instrukcji: wczytywanie i walidację układów,
DFS z backtrackingiem i limitami, niezależną weryfikację planu oraz powtarzalne
eksperymenty dla `N=3..15`.

## Struktura

- `src/blocks_world.py` — klasa stanu, walidacja, ruchy, wejście i weryfikacja,
- `src/dfs.py` — DFS z backtrackingiem, statystyki i limity,
- `src/experiments.py` — losowe przypadki, pomiary i raport Markdown/CSV,
- `src/main.py` — interfejs programu,
- `tests/` — automatyczne testy jednostkowe,
- `examples/` — przykładowe dane z instrukcji.

## Uruchomienie

W folderze projektu:

```powershell
py -3 -m src.main solve examples/example.txt
```

Zmiana limitów:

```powershell
py -3 -m src.main solve examples/example.txt --node-limit 200000 --time-limit 10
```

Testy:

```powershell
py -3 -m unittest discover -s tests -v
```

Raport dla 65 problemów (5 przypadków dla każdego `N=3..15`):

```powershell
py -3 -m src.main report --output reports --seed 20261017
```

Przekroczenie limitu dla dużego `N` jest prawidłowym wynikiem eksperymentu.
DFS nie gwarantuje najkrótszej sekwencji; taki wymóg pojawia się dopiero w
wariancie rozszerzonym na 6 punktów.
