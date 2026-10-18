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

Przykłady obejmują prosty problem dla `N=3`, problem referencyjny dla `N=5`,
większy problem dla `N=8` oraz niepoprawny układ z cyklem demonstrujący walidację.

## Uruchomienie

W folderze projektu:

```powershell
py -3 -m src.main
```

Można też wskazać plik bez zmieniania kodu:

```powershell
py -3 -m src.main examples/simple_3.txt
```

Plik wejściowy wybiera się przez zmianę stałej `INPUT_FILE` w `src/main.py`,
na przykład:

```python
INPUT_FILE = "examples/simple_3.txt"
```

Testy:

```powershell
py -3 -m unittest discover -s tests -v
```

`main.py` uruchamia wyłącznie algorytm. Raport nie jest generowany podczas
zwykłego uruchomienia programu. DFS nie gwarantuje najkrótszej sekwencji;
taki wymóg pojawia się dopiero w wariancie rozszerzonym na 6 punktów.
