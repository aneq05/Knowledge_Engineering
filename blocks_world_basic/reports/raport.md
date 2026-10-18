# Raport z projektu „Świat klocków”

**Wariant podstawowy (4 punkty) · DFS z nawrotami · N = 3–15**  
Data opracowania: 18 października 2026 r.

## 1. Cel i zakres projektu

Celem projektu było napisanie programu, który znajduje sekwencję legalnych ruchów przekształcającą zadany układ początkowy klocków w układ docelowy. Opracowanie obejmuje zadania 1–4 dla wariantu podstawowego z [instrukcji projektu](../projekt1.pdf): reprezentację i walidację stanów, przeszukiwanie DFS z nawrotami i limitami, weryfikację planu oraz eksperymenty losowe.

W tej wersji jeden ruch polega na przeniesieniu wolnego klocka z innego klocka na stół albo ze stołu na inny wolny klocek. Bezpośrednie przeniesienie klocka z jednego klocka na drugi wymaga dwóch ruchów: najpierw na stół, a następnie na docelowy klocek. Znaleziona sekwencja ma być poprawna; wariant podstawowy nie wymaga gwarancji jej najkrótszej długości.

Podstawą części wynikowej jest plik [results/results.csv](results/results.csv). Zawiera on **65 problemów: po 5 dla każdej liczby klocków od 3 do 15**. Wszystkie rozwiązano i zweryfikowano poprawnie. Poniżej przedstawiono komplet pomiarów oraz pełne sekwencje dla wszystkich 30 problemów z N ≤ 8.

## 2. Reprezentacja problemu i sprawdzanie danych

### 2.1. Zapis układu i ruchu

Klocki mają numery od 1 do N. Stan opisuje ciąg `s₁ s₂ … sₙ`, w którym wartość na pozycji i oznacza podłoże klocka i:

- `sᵢ = 0` oznacza, że klocek i leży na stole;
- `sᵢ = j` oznacza, że klocek i leży bezpośrednio na klocku j.

Na przykład układ `0 1 0 2 3` oznacza dwie wieże: `[1 2 4]` i `[3 5]`, zapisane **od dołu do góry**. Kolejność wież na stole nie ma znaczenia. W tabelach wyników wszystkie układy zapisano jako ciągi podłoży, zgodnie z formatem wejściowym.

Ruch zapisuje się jako parę `(klocek, cel)`. Przykładowo `(4, 0)` oznacza przełożenie klocka 4 na stół, a `(4, 5)` oznacza przełożenie go ze stołu na klocek 5. Długość sekwencji to liczba takich par; każdy ruch ma jednostkowy koszt.

### 2.2. Klasa stanu i walidacja

Stan reprezentuje klasa `BlockWorldState` z modułu [src/state.py](src/state.py). Przechowuje ona niezmienną krotkę `supports`, dzięki czemu stany można porównywać i umieszczać w zbiorze odwiedzonych stanów. Konstruktor odrzuca układy zawierające:

- klocek położony na samym sobie;
- odwołanie do nieistniejącego podłoża;
- dwa klocki leżące bezpośrednio na tym samym klocku;
- cykl zależności, np. „1 na 2, 2 na 1”.

Moduł [src/input_reader.py](src/input_reader.py) wczytuje dwie linie danych, pomijając puste linie i komentarze zaczynające się od `#`. Sprawdza też zapis liczb całkowitych, liczbę linii oraz zgodność liczby klocków w układzie początkowym i docelowym. Błędy wejścia są przekazywane użytkownikowi przez komunikat w `main.py`.

Metoda `clear_blocks()` wyznacza klocki wolne, czyli takie, które nie są podłożem żadnego innego klocka. `legal_moves()` generuje ruchy zgodne z wariantem podstawowym, a `apply()` sprawdza ich warunki i tworzy nowy stan. W szczególności nie wolno ruszać klocka zajętego, odkładać klocka na zajęte podłoże ani przenosić go bezpośrednio pomiędzy dwoma klockami.

## 3. Algorytm wyszukiwania rozwiązania

### 3.1. DFS z nawrotami

Funkcja `solve_dfs()` z [src/dfs.py](src/dfs.py) realizuje iteracyjne przeszukiwanie w głąb. Zamiast rekurencji używa stosu stanów. Najpierw umieszcza na nim stan początkowy, a następnie powtarza następujące czynności:

1. Sprawdza limit czasu i limit rozwiniętych węzłów.
2. Zdejmuje stan ze stosu i porównuje go z celem.
3. Jeśli nie osiągnięto celu, zwiększa licznik rozwiniętych węzłów.
4. Generuje i porządkuje legalne ruchy, tworzy stany następcze i dodaje nieodwiedzone stany na stos.
5. Po znalezieniu celu odtwarza sekwencję, korzystając ze słownika poprzedników `parent`.

Zbiór `visited` jest uzupełniany już przy dodaniu nowego stanu na stos. Dzięki temu ten sam układ nie jest ponownie dodawany inną drogą, co zapobiega zapętlaniu przeszukiwania. Gdy dana gałąź się wyczerpie, algorytm wraca do oczekujących stanów na stosie i kontynuuje wyszukiwanie.

### 3.2. Kolejność rozpatrywania ruchów

Zastosowano porządkowanie zależne od układu docelowego, dozwolone w instrukcji. Funkcja `_ordered_moves()` najpierw wyznacza zbiór `settled`, czyli klocków ustawionych już poprawnie wraz z całym podparciem pod nimi. Klocek należy do tego zbioru, jeśli ma docelowe podłoże, a podłoże jest stołem albo innym klockiem z `settled`. Samo poprawne położenie na klocku, który będzie jeszcze przestawiany, nie wystarcza.

Ruchy otrzymują następujące priorytety, od najwyższego:

1. **Ustawienie klocka na docelowym podłożu**, jeśli podłoże jest już gotowe, a klocek nie należy do `settled`.
2. **Odłożenie na stół klocka spoza `settled`**, aby uwolnić inne klocki lub przygotować dalszą przebudowę.
3. Pozostałe ruchy klocków spoza `settled`.
4. Ruchy naruszające już poprawnie ustawione klocki.

Przy równym priorytecie o kolejności decydują numer przenoszonego klocka, a następnie numer celu. Ruchy są dodawane na stos w odwróconej kolejności, tak aby ruch o najwyższym priorytecie został rozpatrzony jako pierwszy. Jest to porządkowanie wszystkich legalnych ruchów, a nie usuwanie ruchów o niższym priorytecie.

Takie podejście kieruje DFS ku budowaniu wież od dołu i ogranicza przedwczesne ustawianie klocków na podłożach, które trzeba będzie jeszcze przesunąć. **Nie daje jednak ogólnej gwarancji najkrótszej sekwencji**. W projekcie nie zastosowano algorytmu optymalnego, z którym można byłoby porównać długości wszystkich 65 planów.

### 3.3. Znaczenie statystyk i limitów

| Wielkość | Sposób wyznaczania |
| --- | --- |
| Długość sekwencji L | Liczba ruchów w znalezionym planie. |
| Rozwinięte węzły E | Liczba stanów zdjętych ze stosu, dla których rozpoczęto generowanie następców. Stan docelowy nie zwiększa licznika. |
| Czas [s] | Różnica wskazań `perf_counter()` od początku `solve_dfs()` do początku iteracji, w której rozpoznano cel. |
| Weryfikacja | Wynik ponownego wykonania planu od stanu początkowego i porównania stanu końcowego z celem. |

Licznik E nie oznacza liczby wszystkich wygenerowanych ani zapamiętanych stanów. Podczas jednego rozwinięcia na stos może trafić wiele stanów, które nie zostaną rozwinięte przed znalezieniem celu. Pomiar czasu nie obejmuje wczytywania pliku, rekonstrukcji znalezionego planu, późniejszej weryfikacji ani zapisu CSV.

Domyślne limity funkcji eksperymentalnej `save_results()` wynoszą **200 000 rozwiniętych węzłów i 2,0 s na problem**. Bezpośrednio wywołana funkcja `solve_dfs()`, używana też przez `main.py`, domyślnie ma ten sam limit węzłów i limit czasu 10,0 s. Algorytm rozróżnia statusy `solved`, `node_limit`, `time_limit` oraz `no_solution`.

CSV nie zapisuje parametrów limitów ani środowiska wykonania; powyższe wartości dla eksperymentów wynikają z domyślnych argumentów w kodzie. W zapisanych wynikach wszystkie statusy to `solved`, więc nie odnotowano przerwania żadnego wyszukiwania przez limit.

## 4. Weryfikacja poprawności

Funkcja `verify_plan()` z [src/verifier.py](src/verifier.py) otrzymuje stan początkowy, stan docelowy i sekwencję ruchów. Wykonuje ruchy po kolei, a następnie sprawdza dokładną równość otrzymanego stanu z celem. Przy nielegalnym ruchu zwraca numer pierwszego błędnego kroku i przyczynę. Legalna, ale niepełna sekwencja również zostaje odrzucona.

Weryfikator działa poza procedurą wyszukiwania, ale korzysta z tej samej metody `BlockWorldState.apply()`. Potwierdza zatem poprawność wykonania planu według zaimplementowanych reguł; same reguły dodatkowo sprawdzają testy automatyczne. Nie jest to druga, niezależna implementacja modelu ruchów.

Podczas przygotowania raportu:

- uruchomiono istniejący zestaw testów: **17 testów zakończyło się powodzeniem**;
- odtworzono wszystkie 65 par układów z zadanym ziarnem i potwierdzono ich zgodność z CSV;
- ponowiono wyszukiwanie dla tych samych problemów: statusy, długości i liczby rozwiniętych węzłów zgadzały się z zapisanymi wynikami, a wszystkie otrzymane plany przeszły weryfikację;
- sprawdzono wszystkie 30 zapisanych w CSV sekwencji dla N ≤ 8: zgadzały się z odtworzonymi planami i prowadziły do odpowiednich celów.

Sprawdzenie wykonano w Pythonie 3.13.3. Jest to informacja o kontroli raportu, a nie o środowisku pierwotnego pomiaru. **Czasy w raporcie pochodzą wyłącznie z istniejącego CSV; nie zastąpiono ich czasami ponownych uruchomień.**

## 5. Metodyka eksperymentów

Przypadki przygotowano funkcją `generate_cases()` z [src/experiments.py](src/experiments.py), korzystającą z lokalnego generatora `random.Random`.

| Parametr | Wartość |
| --- | --- |
| Ziarno generatora | `20261017` |
| Liczba klocków N | Kolejne wartości od 3 do 15, włącznie. |
| Problemy dla jednego N | 5 par: układ początkowy i docelowy. |
| Łączna liczba problemów | 13 × 5 = 65. |
| Wariant ruchów | Podstawowy: z klocka na stół albo ze stołu na klocek. |
| Algorytm | DFS z opisanym porządkowaniem ruchów. |
| Liczba pomiarów czasu | Jeden zapisany pomiar dla każdego problemu. |
| Pełne plany w danych | Wszystkie 30 sekwencji dla N od 3 do 8. |

Aby utworzyć pojedynczy układ, generator losowo przestawia listę klocków, po czym dla każdej kolejnej pary w tej kolejności z prawdopodobieństwem 0,5 rozpoczyna nową wieżę albo dokłada następny klocek na poprzednim. Pierwszy klocek leży na stole. Pozwala to tworzyć poprawne, rozłączne wieże bez cykli. Układ docelowy jest losowany ponownie, jeśli okazał się identyczny z początkowym.

Losowanie nie jest jednostajne w zbiorze wszystkich możliwych układów. Ten sposób generowania sprzyja układom z wieloma krótkimi wieżami. Wyniki opisują więc konkretną próbkę uzyskaną tym generatorem i ziarnem, a nie pełną trudność wszystkich problemów dla danego N.

W tabelach szczegółowych czas podano w sekundach, zachowując sześć miejsc po przecinku z pliku CSV. Zastosowano polski separator dziesiętny. Identyfikator `N.nr`, np. `8.4`, wskazuje czwarty problem dla ośmiu klocków. `OK` oznacza, że wszystkie ruchy były legalne, a stan końcowy był równy celowi. **Każdy problem w poniższych tabelach ma status `solved`.**

## 6. Szczegółowe wyniki wszystkich problemów

W kolumnach „Start” i „Cel” i-ta liczba jest podłożem klocka i, a `0` oznacza stół. L to długość planu, E to liczba rozwiniętych węzłów. Wypisane pod tabelami ruchy wykonuje się od lewej do prawej.

### 6.1. N = 3

| Problem | Start | Cel | L | E | Czas [s] | Weryfikacja |
| --- | --- | --- | ---: | ---: | ---: | :---: |
| 3.1 | `0 1 0` | `0 0 1` | 2 | 2 | 0,000314 | OK |
| 3.2 | `0 1 0` | `0 0 0` | 1 | 1 | 0,000061 | OK |
| 3.3 | `3 0 0` | `3 0 2` | 3 | 3 | 0,000375 | OK |
| 3.4 | `0 0 1` | `0 0 0` | 1 | 1 | 0,000440 | OK |
| 3.5 | `0 0 0` | `3 0 2` | 2 | 2 | 0,000294 | OK |

**Pełne sekwencje ruchów:**

- **3.1:** `(2, 0) -> (3, 1)`
- **3.2:** `(2, 0)`
- **3.3:** `(1, 0) -> (3, 2) -> (1, 3)`
- **3.4:** `(3, 0)`
- **3.5:** `(3, 2) -> (1, 3)`

### 6.2. N = 4

| Problem | Start | Cel | L | E | Czas [s] | Weryfikacja |
| --- | --- | --- | ---: | ---: | ---: | :---: |
| 4.1 | `0 4 0 0` | `0 3 0 0` | 2 | 2 | 0,000352 | OK |
| 4.2 | `0 4 1 0` | `4 0 0 0` | 3 | 3 | 0,000345 | OK |
| 4.3 | `0 4 1 0` | `2 0 0 1` | 4 | 4 | 0,000894 | OK |
| 4.4 | `0 0 4 2` | `0 0 4 0` | 3 | 3 | 0,002258 | OK |
| 4.5 | `0 0 1 0` | `4 0 1 0` | 3 | 3 | 0,000649 | OK |

**Pełne sekwencje ruchów:**

- **4.1:** `(2, 0) -> (2, 3)`
- **4.2:** `(2, 0) -> (3, 0) -> (1, 4)`
- **4.3:** `(2, 0) -> (3, 0) -> (1, 2) -> (4, 1)`
- **4.4:** `(3, 0) -> (4, 0) -> (3, 4)`
- **4.5:** `(3, 0) -> (1, 4) -> (3, 1)`

### 6.3. N = 5

| Problem | Start | Cel | L | E | Czas [s] | Weryfikacja |
| --- | --- | --- | ---: | ---: | ---: | :---: |
| 5.1 | `0 0 0 0 0` | `4 0 0 0 3` | 2 | 2 | 0,000897 | OK |
| 5.2 | `0 0 0 1 3` | `0 0 0 2 1` | 4 | 4 | 0,001145 | OK |
| 5.3 | `0 0 0 0 0` | `0 0 2 5 3` | 3 | 3 | 0,001314 | OK |
| 5.4 | `0 0 0 1 0` | `2 0 1 0 4` | 4 | 4 | 0,001785 | OK |
| 5.5 | `0 0 0 2 0` | `2 0 1 0 4` | 4 | 4 | 0,001057 | OK |

**Pełne sekwencje ruchów:**

- **5.1:** `(1, 4) -> (5, 3)`
- **5.2:** `(4, 0) -> (4, 2) -> (5, 0) -> (5, 1)`
- **5.3:** `(3, 2) -> (5, 3) -> (4, 5)`
- **5.4:** `(4, 0) -> (1, 2) -> (3, 1) -> (5, 4)`
- **5.5:** `(4, 0) -> (1, 2) -> (3, 1) -> (5, 4)`

### 6.4. N = 6

| Problem | Start | Cel | L | E | Czas [s] | Weryfikacja |
| --- | --- | --- | ---: | ---: | ---: | :---: |
| 6.1 | `0 0 2 5 0 0` | `0 0 5 0 0 4` | 4 | 4 | 0,000993 | OK |
| 6.2 | `0 0 0 0 1 0` | `2 4 5 0 0 0` | 4 | 4 | 0,001203 | OK |
| 6.3 | `5 0 0 0 2 0` | `2 0 0 6 0 0` | 4 | 4 | 0,001326 | OK |
| 6.4 | `0 0 4 2 6 1` | `2 0 0 0 3 0` | 6 | 6 | 0,002076 | OK |
| 6.5 | `0 0 0 0 0 0` | `0 0 0 1 0 3` | 2 | 2 | 0,001033 | OK |

**Pełne sekwencje ruchów:**

- **6.1:** `(4, 0) -> (6, 4) -> (3, 0) -> (3, 5)`
- **6.2:** `(2, 4) -> (5, 0) -> (1, 2) -> (3, 5)`
- **6.3:** `(4, 6) -> (1, 0) -> (5, 0) -> (1, 2)`
- **6.4:** `(3, 0) -> (4, 0) -> (5, 0) -> (5, 3) -> (6, 0) -> (1, 2)`
- **6.5:** `(4, 1) -> (6, 3)`

### 6.5. N = 7

| Problem | Start | Cel | L | E | Czas [s] | Weryfikacja |
| --- | --- | --- | ---: | ---: | ---: | :---: |
| 7.1 | `5 3 0 2 4 0 0` | `4 0 6 0 0 2 0` | 7 | 7 | 0,004344 | OK |
| 7.2 | `7 0 2 3 0 4 6` | `5 0 0 0 4 0 1` | 8 | 8 | 0,003805 | OK |
| 7.3 | `0 6 2 5 1 0 4` | `0 3 6 0 4 5 0` | 9 | 9 | 0,004310 | OK |
| 7.4 | `7 0 4 6 3 0 5` | `0 7 1 0 2 0 0` | 8 | 8 | 0,001261 | OK |
| 7.5 | `0 0 0 0 7 0 0` | `7 4 0 1 2 0 6` | 6 | 6 | 0,002482 | OK |

**Pełne sekwencje ruchów:**

- **7.1:** `(1, 0) -> (5, 0) -> (4, 0) -> (1, 4) -> (2, 0) -> (6, 2) -> (3, 6)`
- **7.2:** `(1, 0) -> (7, 0) -> (6, 0) -> (4, 0) -> (3, 0) -> (5, 4) -> (1, 5) -> (7, 1)`
- **7.3:** `(7, 0) -> (4, 0) -> (3, 0) -> (2, 0) -> (5, 0) -> (5, 4) -> (6, 5) -> (3, 6) -> (2, 3)`
- **7.4:** `(1, 0) -> (7, 0) -> (2, 7) -> (5, 0) -> (5, 2) -> (3, 0) -> (3, 1) -> (4, 0)`
- **7.5:** `(5, 0) -> (7, 6) -> (1, 7) -> (4, 1) -> (2, 4) -> (5, 2)`

### 6.6. N = 8

| Problem | Start | Cel | L | E | Czas [s] | Weryfikacja |
| --- | --- | --- | ---: | ---: | ---: | :---: |
| 8.1 | `2 6 1 5 7 0 0 0` | `0 0 1 3 4 0 6 2` | 10 | 10 | 0,002135 | OK |
| 8.2 | `0 0 0 2 0 8 6 0` | `0 3 6 0 0 0 8 1` | 7 | 7 | 0,004968 | OK |
| 8.3 | `0 0 0 0 2 5 0 7` | `3 1 4 8 0 0 2 0` | 8 | 8 | 0,005503 | OK |
| 8.4 | `7 6 0 1 0 5 2 3` | `5 0 1 6 8 7 3 2` | 13 | 13 | 0,008053 | OK |
| 8.5 | `0 0 0 2 0 0 4 0` | `0 0 8 1 3 0 0 0` | 5 | 5 | 0,002282 | OK |

**Pełne sekwencje ruchów:**

- **8.1:** `(3, 0) -> (1, 0) -> (2, 0) -> (3, 1) -> (8, 2) -> (4, 0) -> (4, 3) -> (5, 0) -> (5, 4) -> (7, 6)`
- **8.2:** `(4, 0) -> (7, 0) -> (6, 0) -> (3, 6) -> (2, 3) -> (8, 1) -> (7, 8)`
- **8.3:** `(6, 0) -> (5, 0) -> (8, 0) -> (4, 8) -> (3, 4) -> (1, 3) -> (2, 1) -> (7, 2)`
- **8.4:** `(4, 0) -> (1, 0) -> (7, 0) -> (2, 0) -> (6, 0) -> (8, 0) -> (8, 2) -> (5, 8) -> (1, 5) -> (3, 1) -> (7, 3) -> (6, 7) -> (4, 6)`
- **8.5:** `(3, 8) -> (5, 3) -> (7, 0) -> (4, 0) -> (4, 1)`

### 6.7. N = 9

| Problem | Start | Cel | L | E | Czas [s] | Weryfikacja |
| --- | --- | --- | ---: | ---: | ---: | :---: |
| 9.1 | `7 0 0 3 0 9 0 1 0` | `4 0 0 0 0 0 0 0 7` | 6 | 6 | 0,005548 | OK |
| 9.2 | `0 0 0 8 0 4 0 0 5` | `2 3 0 0 4 0 0 7 0` | 7 | 7 | 0,003111 | OK |
| 9.3 | `6 5 0 1 9 0 2 0 4` | `0 4 5 9 0 0 2 0 8` | 11 | 11 | 0,004594 | OK |
| 9.4 | `0 0 1 0 7 9 0 0 0` | `0 4 0 0 6 0 0 1 7` | 7 | 7 | 0,007514 | OK |
| 9.5 | `5 1 7 0 8 0 0 6 0` | `0 5 0 0 9 7 0 0 0` | 8 | 8 | 0,008266 | OK |

### 6.8. N = 10

| Problem | Start | Cel | L | E | Czas [s] | Weryfikacja |
| --- | --- | --- | ---: | ---: | ---: | :---: |
| 10.1 | `10 6 4 0 0 9 0 1 0 5` | `0 0 0 3 6 0 0 0 0 0` | 8 | 8 | 0,007340 | OK |
| 10.2 | `0 7 10 5 1 0 9 6 3 0` | `7 0 10 2 0 0 0 1 8 9` | 13 | 13 | 0,006505 | OK |
| 10.3 | `0 0 0 0 8 1 2 0 0 5` | `0 8 0 0 7 1 0 6 0 0` | 6 | 6 | 0,006797 | OK |
| 10.4 | `0 9 0 5 0 2 0 0 4 0` | `0 6 4 0 7 8 10 1 2 0` | 11 | 11 | 0,006576 | OK |
| 10.5 | `0 0 4 0 0 0 0 0 3 1` | `6 0 0 0 0 5 4 9 0 7` | 8 | 8 | 0,007425 | OK |

### 6.9. N = 11

| Problem | Start | Cel | L | E | Czas [s] | Weryfikacja |
| --- | --- | --- | ---: | ---: | ---: | :---: |
| 11.1 | `11 0 0 0 1 0 0 3 0 9 10` | `8 0 9 6 4 11 0 2 0 0 3` | 12 | 12 | 0,016666 | OK |
| 11.2 | `9 0 8 0 0 0 0 1 11 4 2` | `7 6 4 9 0 0 0 3 0 0 0` | 11 | 11 | 0,013107 | OK |
| 11.3 | `4 0 0 0 0 10 5 11 0 7 0` | `7 0 0 0 0 0 11 1 0 0 4` | 9 | 9 | 0,009638 | OK |
| 11.4 | `0 7 0 0 11 5 9 2 0 0 0` | `5 10 0 11 0 1 0 0 0 0 3` | 10 | 10 | 0,014591 | OK |
| 11.5 | `7 3 4 6 0 0 10 0 2 0 8` | `0 0 0 0 2 9 1 0 5 0 0` | 11 | 11 | 0,008108 | OK |

### 6.10. N = 12

| Problem | Start | Cel | L | E | Czas [s] | Weryfikacja |
| --- | --- | --- | ---: | ---: | ---: | :---: |
| 12.1 | `2 10 0 0 12 4 0 9 0 5 0 0` | `0 9 0 1 3 0 0 10 0 11 0 0` | 11 | 11 | 0,013209 | OK |
| 12.2 | `0 3 0 0 8 12 5 10 1 0 9 0` | `0 0 0 0 12 7 0 4 0 0 0 0` | 10 | 10 | 0,026840 | OK |
| 12.3 | `8 1 2 11 3 0 0 4 0 5 0 9` | `2 5 0 6 10 0 0 0 0 0 12 0` | 13 | 13 | 0,026626 | OK |
| 12.4 | `0 0 0 0 3 4 1 0 0 0 12 5` | `0 0 0 0 0 0 1 0 3 0 0 0` | 5 | 5 | 0,012185 | OK |
| 12.5 | `2 9 0 0 0 12 5 0 10 0 0 4` | `11 4 0 0 0 0 12 9 0 6 0 2` | 12 | 12 | 0,016574 | OK |

### 6.11. N = 13

| Problem | Start | Cel | L | E | Czas [s] | Weryfikacja |
| --- | --- | --- | ---: | ---: | ---: | :---: |
| 13.1 | `6 0 0 12 0 0 0 4 7 3 0 0 0` | `7 0 2 0 0 0 0 9 0 12 0 1 0` | 10 | 10 | 0,027907 | OK |
| 13.2 | `12 0 8 7 0 0 0 0 0 0 4 6 0` | `0 0 0 12 0 0 0 5 0 0 4 7 6` | 10 | 10 | 0,034720 | OK |
| 13.3 | `6 0 10 0 1 0 0 0 0 5 2 13 0` | `13 0 1 0 0 0 0 0 0 12 0 0 0` | 9 | 9 | 0,030644 | OK |
| 13.4 | `4 9 1 11 0 12 2 0 0 13 5 0 6` | `0 12 0 0 7 3 0 13 0 4 0 9 11` | 16 | 16 | 0,024030 | OK |
| 13.5 | `0 5 12 3 0 0 0 0 11 0 0 10 2` | `0 0 10 5 0 13 12 0 1 7 9 0 2` | 14 | 14 | 0,015879 | OK |

### 6.12. N = 14

| Problem | Start | Cel | L | E | Czas [s] | Weryfikacja |
| --- | --- | --- | ---: | ---: | ---: | :---: |
| 14.1 | `4 3 11 9 2 0 0 0 0 1 0 0 0 8` | `0 12 8 0 0 7 0 0 0 0 4 0 0 10` | 12 | 12 | 0,020238 | OK |
| 14.2 | `5 9 0 0 0 0 0 0 11 4 0 7 0 3` | `0 8 0 7 0 11 1 12 5 13 4 3 0 0` | 15 | 15 | 0,035770 | OK |
| 14.3 | `0 13 0 9 10 11 0 0 2 4 3 0 12 0` | `0 12 2 0 0 0 0 6 0 7 13 0 8 3` | 15 | 15 | 0,014231 | OK |
| 14.4 | `0 0 11 0 7 0 14 0 0 5 0 0 0 9` | `9 0 0 0 14 0 4 0 5 0 0 0 1 0` | 10 | 10 | 0,022429 | OK |
| 14.5 | `0 0 4 0 13 0 0 3 0 1 0 8 10 0` | `14 0 0 8 0 12 6 0 0 7 0 0 0 13` | 12 | 12 | 0,015051 | OK |

### 6.13. N = 15

| Problem | Start | Cel | L | E | Czas [s] | Weryfikacja |
| --- | --- | --- | ---: | ---: | ---: | :---: |
| 15.1 | `8 0 14 0 12 0 6 15 0 0 0 9 0 0 0` | `0 0 0 0 1 9 0 14 8 0 2 0 4 0 5` | 13 | 13 | 0,036759 | OK |
| 15.2 | `0 6 2 0 12 0 0 0 0 5 0 0 14 3 0` | `13 0 9 0 3 8 14 0 10 2 7 1 15 4 0` | 17 | 17 | 0,049189 | OK |
| 15.3 | `0 0 11 12 0 7 0 0 0 0 14 0 4 15 1` | `0 0 0 7 14 2 0 5 12 1 8 0 11 0 0` | 15 | 15 | 0,038974 | OK |
| 15.4 | `0 0 0 1 0 14 0 0 12 11 2 0 10 0 3` | `0 0 0 0 0 0 0 0 2 0 15 0 0 0 9` | 10 | 10 | 0,053833 | OK |
| 15.5 | `12 0 5 0 0 7 13 10 4 6 0 15 2 0 8` | `0 0 9 0 6 13 15 12 5 4 0 0 0 0 0` | 17 | 17 | 0,051551 | OK |

## 7. Zestawienie zbiorcze i interpretacja

Średnie obliczono osobno dla pięciu problemów przy każdym N. Są to średnie pomiędzy różnymi problemami, a nie średnie z powtórzeń pomiaru tego samego problemu. Dla czytelności w tym zestawieniu czas przeliczono na milisekundy: 1 ms = 0,001 s.

| N | Problemy | Średnie L | Średnie E | Średni czas [ms] | Maks. czas [ms] | Weryfikacja OK |
| ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| 3 | 5 | 1,8 | 1,8 | 0,2968 | 0,440 | 5/5 |
| 4 | 5 | 3,0 | 3,0 | 0,8996 | 2,258 | 5/5 |
| 5 | 5 | 3,4 | 3,4 | 1,2396 | 1,785 | 5/5 |
| 6 | 5 | 4,0 | 4,0 | 1,3262 | 2,076 | 5/5 |
| 7 | 5 | 7,6 | 7,6 | 3,2404 | 4,344 | 5/5 |
| 8 | 5 | 8,6 | 8,6 | 4,5882 | 8,053 | 5/5 |
| 9 | 5 | 7,8 | 7,8 | 5,8066 | 8,266 | 5/5 |
| 10 | 5 | 9,2 | 9,2 | 6,9286 | 7,425 | 5/5 |
| 11 | 5 | 10,6 | 10,6 | 12,4220 | 16,666 | 5/5 |
| 12 | 5 | 10,2 | 10,2 | 19,0868 | 26,840 | 5/5 |
| 13 | 5 | 11,8 | 11,8 | 26,6360 | 34,720 | 5/5 |
| 14 | 5 | 12,8 | 12,8 | 21,5438 | 35,770 | 5/5 |
| 15 | 5 | 14,4 | 14,4 | 46,0612 | 53,833 | 5/5 |

Łącznie otrzymano **526 ruchów w 65 planach** i **526 rozwiniętych węzłów**. Suma zapisanych czasów wyszukiwania wyniosła **0,750379 s**; nie jest to czas wykonania całego programu eksperymentalnego, ponieważ nie uwzględnia m.in. generowania problemów, weryfikacji i zapisu wyników. Skuteczność w tej próbce wyniosła **65/65, czyli 100%**.

### 7.1. Długości planów i rozwinięte węzły

Najkrótsze znalezione plany miały po jednym ruchu (problemy 3.2 i 3.4), a najdłuższe po 17 ruchów (15.2 i 15.5). Średnia długość wzrosła z 1,8 ruchu dla N = 3 do 14,4 ruchu dla N = 15. Zależność nie jest ściśle rosnąca: przykładowo średnia dla N = 9 jest mniejsza niż dla N = 8, ponieważ trudność zależy też od konkretnego układu.

W każdym zapisanym problemie E = L. Oznacza to, że przed znalezieniem celu algorytm nie rozwinął dodatkowych stanów poza ścieżką zwróconego rozwiązania. Jest to zgodne z korzystnym działaniem zastosowanego porządkowania w tej próbce. Nie oznacza, że wygenerowano tylko L stanów: podczas rozwijania kolejnych węzłów powstawały także alternatywne stany odkładane na stos i zapisywane w `visited`.

Nie przeprowadzono porównania z DFS bez porządkowania ruchów ani z algorytmem gwarantującym optimum. Na podstawie tych wyników nie można więc określić wielkości przyspieszenia dzięki porządkowaniu ani uznać wszystkich planów za najkrótsze.

### 7.2. Czas działania

Najkrótszy zapisany czas wyniósł 0,000061 s dla problemu 3.2, a najdłuższy 0,053833 s dla 15.4. Średni czas dla N = 15 wyniósł 46,0612 ms, podczas gdy dla N = 3 było to 0,2968 ms. Dla N = 14 średni czas był jednak niższy niż dla N = 13, co pokazuje, że sam wzrost N nie wyznacza jednoznacznie czasu konkretnej próbki.

Koszt jednego rozwinięcia obejmuje wyznaczenie wolnych klocków, ustalenie priorytetów, utworzenie wszystkich legalnych następców i walidację nowych stanów. Z tego powodu sama liczba rozwiniętych węzłów nie opisuje całego nakładu obliczeń. Najdłuższy czas uzyskano dla planu o 10 ruchach, chociaż inne plany miały po 17 ruchów. Przy pojedynczych, krótkich pomiarach na wynik może wpływać również bieżące obciążenie komputera.

### 7.3. Zakres wniosków

Wszystkie problemy rozwiązano znacznie poniżej domyślnego limitu 2 s, a liczba rozwiniętych węzłów nie przekroczyła 17. Potwierdza to skuteczność implementacji dla zapisanych danych. Pięć problemów na rozmiar, jeden pomiar czasu na problem i brak danych o sprzęcie nie pozwalają jednak wyznaczyć wiarygodnej ogólnej zależności czasu od N. W eksperymentach nie mierzono też maksymalnej liczby przechowywanych stanów ani zużycia pamięci.

## 8. Przykład działania: układ referencyjny z instrukcji

Poniższy przykład objaśnia sposób działania programu i odpowiada plikowi [examples/example.txt](examples/example.txt). Jest przykładem kontrolnym, odrębnym od 65 losowych pomiarów z tabel.

- **Start:** `0 1 0 2 3`, czyli wieże `[1 2 4]` oraz `[3 5]`.
- **Cel:** `2 3 4 5 0`, czyli wieża `[5 4 3 2 1]`.

Program zwrócił następującą sekwencję:

```text
(5, 0) -> (4, 0) -> (4, 5) -> (3, 4) -> (2, 0) -> (2, 3) -> (1, 2)
```

| Krok | Ruch | Otrzymany układ | Znaczenie |
| ---: | --- | --- | --- |
| 0 | Stan początkowy | `0 1 0 2 3` | Dwie wieże: `[1 2 4]` i `[3 5]`. |
| 1 | `(5, 0)` | `0 1 0 2 0` | Klocek 5 trafia na stół, czyli na swoje docelowe podłoże. |
| 2 | `(4, 0)` | `0 1 0 0 0` | Zdjęcie klocka 4 uwalnia klocek 2. |
| 3 | `(4, 5)` | `0 1 0 5 0` | Powstaje docelowa podstawa `[5 4]`. |
| 4 | `(3, 4)` | `0 1 4 5 0` | Wieża rośnie do `[5 4 3]`. |
| 5 | `(2, 0)` | `0 0 4 5 0` | Klocek 2 zostaje zdjęty z klocka 1 na stół. |
| 6 | `(2, 3)` | `0 3 4 5 0` | Powstaje wieża `[5 4 3 2]`. |
| 7 | `(1, 2)` | `2 3 4 5 0` | Osiągnięto układ docelowy. |

Plan ma 7 ruchów, algorytm rozwinął 7 węzłów, a weryfikator potwierdził jego poprawność. Długość zgadza się z podaną w instrukcji długością najkrótszego planu dla tego przykładu w wariancie podstawowym. Jest to kontrola konkretnego przypadku, a nie dowód optymalności DFS dla dowolnych danych.

## 9. Odtworzenie działania programu

Wszystkie poniższe polecenia należy wykonywać z katalogu `blocks_world_basic`.

Uruchomienie przykładu referencyjnego:

```powershell
py -3 -m src.main examples/example.txt
```

Uruchomienie testów automatycznych:

```powershell
py -3 -m unittest discover -s tests -v
```

Ponowne wygenerowanie i rozwiązanie 65 problemów z domyślnym ziarnem:

```powershell
py -3 -m src.experiments
```

Ostatnie polecenie zapisuje wyniki do `results/results.csv`, zastępując poprzednią zawartość pliku. Dla tego samego ziarna i opisanej implementacji można odtworzyć te same układy i kolejność przeszukiwania; ponowne czasy będą zależeć od warunków uruchomienia. Samo uruchomienie `src.main` wypisuje rozwiązanie i wynik weryfikacji, ale nie generuje tego raportu.

## 10. Wnioski

Implementacja realizuje zakres wariantu podstawowego: odrzuca wskazane niepoprawne układy, generuje legalne ruchy, unika ponownego dodawania odwiedzonych stanów, respektuje limity i sprawdza znalezione sekwencje.

W badanej próbce porządkowany DFS rozwiązał wszystkie 65 problemów, a każdy plan przeszedł weryfikację. Priorytet budowania poprawnych wież od dołu pozwolił w tych przypadkach dojść do celu bez rozwijania stanów spoza zwróconej ścieżki. Wynik jest korzystny dla zastosowanych danych, ale nie stanowi gwarancji krótkiego czasu ani minimalnej długości planu dla wszystkich możliwych układów.

Raport zawiera wymagane układy, długości planów, liczby rozwiniętych węzłów, czasy i wyniki weryfikacji dla każdego problemu oraz pełne sekwencje dla N ≤ 8. Dane źródłowe pozostają w [results/results.csv](results/results.csv), a szczegóły implementacji w modułach [src/state.py](src/state.py), [src/dfs.py](src/dfs.py), [src/verifier.py](src/verifier.py) i [src/experiments.py](src/experiments.py).
