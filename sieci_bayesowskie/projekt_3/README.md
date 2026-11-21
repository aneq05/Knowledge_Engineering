# Sieć bayesowska studentów — zestaw k26 (4 + 6 pkt)

Wymagany Python **3.10–3.13**, `pgmpy==1.1.2`. Projekt implementuje polecenie na **6 punktów kumulatywnie** (czyli zachowuje też zadania na 4 pkt). Oryginalne dane są w `data/k26/`. Plik `test.csv` służy **wyłącznie do oceny**.

## Uruchomienie (Windows / PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
$env:PYTHONHASHSEED = "0"
python -m student_bn --level 6
python -m pytest -q
```

Na Linuksie/macOS: `source .venv/bin/activate` i `PYTHONHASHSEED=0 python -m student_bn --level 6`.

`PYTHONHASHSEED=0` ustaw **przed uruchomieniem** Pythona (dla powtarzalności rozstrzygania remisów w HillClimbSearch). Próbkowanie i losowe inicjalizacje EM są dodatkowo deterministyczne przez `--seed`.

> Możesz uruchomić poprzedni zakres bez eksperymentów na 6 pkt: `python -m student_bn --level 4`.

### Parametry

```powershell
python -m student_bn --level 6 --em-starts 5 --em-iterations 100 --imputation-rounds 2 --seed 42 --samples 20000
```

- `--em-starts`: **minimum 5** losowych inicjalizacji EM na grafie eksperckim (domyślnie 5).
- `--em-iterations`: maksymalna liczba aktualizacji EM (domyślnie 100).
- `--imputation-rounds`: liczba powtórzeń EM → uzupełnienie → HillClimbSearch (domyślnie 2).
- `--seed`: ziarno dla EM i losowania stanów brakujących (domyślnie 42).
- `--samples`: liczba próbek dla części dotyczącej próbkowania na 8 pkt; `0` pomija (domyślnie 20000).
- `--dataset`, `--output`: opcjonalne katalogi wejścia/wyjścia.

## Struktura kodu

```text
student_bn_k26/
├── data/k26/               # opis.json, dane.csv, test.csv, zapytania.txt, ograniczenia.txt
├── student_bn/
│   ├── __main__.py          # Jedna orkiestracja: dane -> uczenie -> ocena -> raport
│   ├── data.py              # Description/Variable + walidacja JSON/CSV
│   ├── joint.py             # Kodowanie stanów, joint, marginalizacja, próbkowanie
│   ├── learning.py          # DiscreteMLE, własne EM, 5+ losowych startów
│   ├── structure.py         # 3 warianty HC/BIC, imputacja a posteriori, grafy
│   ├── queries.py           # P / MAP, VariableElimination, bezpieczne AST
│   ├── evaluation.py        # Log-wiarygodność, dokładność, marginesy, TV
│   └── report.py            # Składanie raportu Markdown i zapis JSON
├── tests/                   # Testy bez pgmpy + opcjonalna integracja
├── results/                 # Wygenerowany raport i odpowiedzi
└── pyproject.toml
```

**Co zostało zmienione względem wersji na 4 pkt?** Istniejące `learning.py`, `__main__.py`, `evaluation.py`, `report.py` rozszerzono. **Dodano tylko `structure.py`** dla metod stricte związanych z uczeniem grafu; `data.py`, `queries.py`, `joint.py` nie wymagają przerabiania ani kopiowania. Rozbudowano testy.

## 6.1 — EM dla danych z brakami

`learning.fit_em` realizuje podany w instrukcji pseudokod dla skończonych zmiennych dyskretnych:

1. Inicjuje każdą kolumnę CPD jako **dodatni rozkład Dirichleta** (`initialization="random"`) lub lekko wygładzone MLE rodzinne (`"mle"`).
2. **E-krok:** dla każdego unikalnego wzorca zaobserwowanych wartości wybiera zgodne konfiguracje braków; wylicza `p[h]` jako iloczyn CPD, `p_r = sum_h p[h]`, dopisuje `liczność_wzorca * log(p_r)` do L i oczekiwane zliczenia `N[X][x,u] += liczność_wzorca * p[h]/p_r`.
3. **M-krok:** normalizuje zliczenia osobno dla każdej konfiguracji rodziców. Jeśli konfiguracja nie wystąpiła, wpisuje rozkład jednostajny.
4. Zapisuje log-wiarygodność **po każdej aktualizacji** i sprawdza, że nie maleje.
5. Kończy, gdy `abs(L_new-L_old) < 1e-6 * liczba_wierszy` lub po limicie iteracji.
6. `fit_em_multistart` uruchamia co najmniej **5 niezależnych losowych punktów startowych** i zachowuje model o najwyższej końcowej log-wiarygodności danych obserwowanych.

**Nie używamy `DiscreteEM`.** Ta klasa w `pgmpy 1.1.2` nie uczy poprawnie z częściowo niekompletnych wierszy: usuwa takie wiersze, a ukryte stany zakłada tylko dla całkowicie nieobserwowanych kolumn. To jest wprost wyjaśnione w raporcie.

Raport zestawia **MLE z pełnych wierszy**, **MLE po rodzinach** i **EM**: testową log-wiarygodność i trafność G, log-wiarygodność obserwowaną dla danych treningowych, **wszystkie rozkłady brzegowe** wobec test.csv i odpowiedzi na `zapytania.txt`.

## 6.2 — trzy strategie uczenia struktury

W `structure.py` wykorzystujemy **jedną wspólną funkcję `learn_dag`** (`HillClimbSearch(scoring_method="bic-d", return_type="dag")`):

| Wariant | Dane dla BIC | Ograniczenia |
|---|---|---|
| HC (complete, free) | Tylko kompletne TRAIN wiersze | Brak |
| HC (complete, expert) | Tylko kompletne TRAIN wiersze | `ExpertKnowledge`: required/forbidden/tiers |
| HC (EM + imputation) | Jeden uzupełniony wiersz na każdy oryginalny TRAIN wiersz | `ExpertKnowledge` |

Metoda trzecia działa iteracyjnie:

```text
model = najlepszy EM na grafie eksperckim
powtórz R razy:
    pełne_dane = próbkuj P(brakujące | obserwowane, model)
    # dokładnie jeden wiersz na studenta; bez powielania N
    nowy_DAG = HillClimbSearch(BIC, pełne_dane, ExpertKnowledge)
    model = EM(oryginalne_niepełne_dane, nowy_DAG)
```

**Ważne:** każdy z trzech wyuczonych grafów otrzymuje CPD za pomocą **tej samej procedury EM**, z tej samej inicjalizacji opartej na lekko wygładzonym rodzinnym MLE, z identyczną tolerancją i limitem iteracji. Natomiast osobne 5 losowych startów na grafie eksperckim sprawdza podatność EM na optima lokalne, tak jak wymaga punkt 6.1.

Dla każdego grafu raportuje się: krawędzie, dodane/usunięte/odwrócone krawędzie względem eksperta, liczbę swobodnych parametrów `sum_X (r_X-1)∏_Pa(X) r_Pa(X)`, log P(obserwowane TRAIN), sumaryczną i średnią log P(TEST), skuteczność G, oraz równoważność Markowa (szkielet i v-struktury). Porównanie odpowiedzi na `zapytania.txt` wykorzystuje odległość TV **pełnych rozkładów zapytań**. Raport wybiera model końcowy i opisuje kryterium.

## Pliki wynikowe

Po uruchomieniu `--level 6` otrzymasz m.in.:

```text
results/
  report.md                         # Raport 4+6 pkt, wszystkie porównania
  answers_mle.json                  # MLE rodzinne + warunki na 8 pkt
  answers_em.json                   # Najlepszy EM + warunki na 8 pkt
  answers_mle_complete.json         # MLE z pełnych wierszy
  answers_structure_free.json       # BIC bez ograniczeń
  answers_structure_expert.json     # BIC z ograniczeniami
  answers_structure_em_imputed.json # BIC na imputowanych danych
  level6_numeric_validation.md      # Niezależna weryfikacja NumPy (pomocnicza)
```

Ważne: `report.md` i pliki JSON są generowane przez pełny przebieg z `pgmpy`. `level6_numeric_validation.md` jest **niezależną kontrolą obliczeń NumPy**, nie zastępuje pełnego porównania trzech grafów.

## Testowanie i ograniczenia

```powershell
python -m pytest -q
```

Testy niezależne od `pgmpy` sprawdzają walidację plików, AST, EM na realnym k26, **5 losowych startów**, monotoniczność L, zgodność osi CPD, imputację z warunkowego rozkładu i porównania grafów. Testy integracyjne wymagają `pgmpy`.

Dane pochodzą z ankiet z brakami; **MCAR / MAR / MNAR** wpływają na interpretację wyników. EM nie leczy automatycznie mechanizmu MNAR. Wysokie dopasowanie i BIC nie są dowodem kierunku przyczynowości. Ponieważ warianty structure learning używają różnych danych (367 kompletnych wierszy vs 2000 imputowanych), ich wartości BIC nie powinny być bezpośrednio porównywane jako jeden ranking między różnymi zbiorami obserwacji.

### Pełny test integracyjny z `pgmpy`

Domyślne `pytest` wykonuje szybkie testy jednostkowe, a osobny test pełnego przebiegu (3 wyszukiwania BIC) uruchomisz świadomie po instalacji biblioteki:

```powershell
$env:RUN_FULL_INTEGRATION = "1"
python -m pytest -q tests/test_full_pipeline.py
```

Pełny test jest dodatkowy; do właściwego eksperymentu użyj `python -m student_bn --level 6` z domyślnym limitem 100 iteracji EM.
