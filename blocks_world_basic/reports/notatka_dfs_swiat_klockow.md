# Świat klocków — notatka do zrozumienia kodu i DFS

**Wariant podstawowy · punkty 1–4 instrukcji · materiał do nauki**

Data opracowania: 19 października 2026 r.

> **Główna idea:** program szuka drogi od układu początkowego do docelowego. Stanem jest cały układ klocków, a jeden legalny ruch prowadzi do kolejnego stanu. DFS wybiera kolejność sprawdzania tych możliwości.

## Spis treści

1. [Istota problemu](#istota-problemu)
2. [Punkt 1 — wczytanie, reprezentacja i walidacja](#punkt-1)
3. [Punkt 2 — DFS z nawrotami, krok po kroku](#punkt-2)
4. [Punkt 3 — weryfikacja planu](#punkt-3)
5. [Punkt 4 — losowe problemy i pomiary](#punkt-4)
6. [Jak wszystko łączy main.py](#main)
7. [Pytania kontrolne i najważniejsze rozróżnienia](#pytania)
8. [Uruchamianie i pliki źródłowe](#uruchamianie)

<a id="istota-problemu"></a>

## 1. Istota problemu

Na stole znajdują się klocki ponumerowane od 1 do N. Każdy klocek stoi na stole albo na innym klocku. Na jednym klocku może stać bezpośrednio najwyżej jeden inny klocek.

**Klocek wolny** to taki, na którym nic nie stoi. Tylko wolny klocek można przenieść.

W wariancie podstawowym dozwolone są dwa rodzaje ruchów:

1. Przeniesienie wolnego klocka z innego klocka na stół.
2. Przeniesienie wolnego klocka ze stołu na inny wolny klocek.

Przeniesienie klocka z jednego klocka na drugi wymaga więc dwóch ruchów: najpierw na stół, potem na nowy klocek.

### Dlaczego to jest problem planowania?

Klocki wzajemnie się blokują. Aby przesunąć dolny klocek, trzeba najpierw zdjąć to, co stoi nad nim. Niektóre ruchy przygotowują możliwość wykonania późniejszych ruchów. Dlatego decyzja o przestawieniu jednego klocka zależy od położenia pozostałych.

Przykład z instrukcji:

- **Start:** wieże `[1 2 4]` oraz `[3 5]`.
- **Cel:** wieża `[5 4 3 2 1]`.

Wieże zapisujemy tutaj **od dołu do góry**. Na początku klocek 4 stoi na 2, klocek 2 na 1, a klocek 5 na 3. Docelowo klocek 5 ma stanowić podstawę, a klocek 1 ma być na samej górze.

### Jak widzi to algorytm?

Problem można przedstawić jako graf:

| Pojęcie | Znaczenie w projekcie |
| --- | --- |
| Wierzchołek | Cały układ wszystkich klocków. |
| Krawędź | Jeden legalny ruch przekształcający układ. |
| Następnik stanu | Układ otrzymany po jednym legalnym ruchu. |
| Ścieżka od startu do celu | Sekwencja ruchów będąca rozwiązaniem. |

Program tworzy kolejne fragmenty tego grafu podczas działania: wyznacza legalne ruchy z bieżącego stanu i oblicza ich skutki. Nie musi wcześniej wypisywać wszystkich możliwych układów.

<a id="punkt-1"></a>

## 2. Punkt 1 instrukcji — wczytanie, reprezentacja i walidacja

**Główne pliki:** [input_reader.py](../src/input_reader.py) i [state.py](../src/state.py).

### 2.1. Jak czytać zapis układu?

Plik wejściowy zawiera dwie linie danych:

```text
0 1 0 2 3
2 3 4 5 0
```

Pierwsza linia to start, druga to cel. **Pozycja oznacza numer klocka, a wartość — numer jego podłoża.** Wartość `0` oznacza stół.

Dla początku `0 1 0 2 3`:

| Klocek | Wartość na jego pozycji | Interpretacja |
| ---: | ---: | --- |
| 1 | 0 | Klocek 1 leży na stole. |
| 2 | 1 | Klocek 2 leży na klocku 1. |
| 3 | 0 | Klocek 3 leży na stole. |
| 4 | 2 | Klocek 4 leży na klocku 2. |
| 5 | 3 | Klocek 5 leży na klocku 3. |

Otrzymujemy wieże `[1 2 4]` i `[3 5]`. Cel `2 3 4 5 0` opisuje wieżę `[5 4 3 2 1]`.

### 2.2. Co robi read_problem()?

Funkcja `read_problem()`:

1. Czyta plik tekstowy w UTF-8.
2. Pomija puste linie i komentarze zaczynające się od `#`.
3. Sprawdza, czy pozostały dokładnie dwie linie danych.
4. Zamienia zapis na liczby całkowite.
5. Tworzy dwa obiekty `BlockWorldState`.
6. Sprawdza, czy start i cel zawierają tyle samo klocków.

Sama konwersja jednej linii wygląda tak:

```python
start_values = tuple(map(int, lines[0].split()))
```

`split()` dzieli tekst na fragmenty, `map(int, ...)` zamienia je na liczby, a `tuple(...)` tworzy krotkę.

### 2.3. Klasa BlockWorldState

```python
@dataclass(frozen=True)
class BlockWorldState:
    supports: tuple[int, ...]
```

`supports` przechowuje podłoża wszystkich klocków, np. `(0, 1, 0, 2, 3)`.

`@dataclass` generuje m.in. inicjalizację obiektu i porównywanie jego pól. Dzięki temu dwa stany z taką samą krotką podłoży są równe.

`frozen=True` sprawia, że stan jest niezmienny. Po wykonaniu ruchu tworzymy nowy obiekt, a wcześniejszy układ pozostaje dostępny. Stan z takim polem można też wykorzystać jako element zbioru `visited` oraz klucz słownika `parent`.

Numery klocków zaczynają się od 1, a indeksy w Pythonie od 0. Dlatego podłoże klocka `block` odczytywane jest przez:

```python
self.supports[block - 1]
```

### 2.4. Walidacja układu

Po utworzeniu obiektu automatycznie uruchamiane jest:

```python
def __post_init__(self):
    self._validate()
```

Walidacja odrzuca cztery rodzaje błędów:

| Błąd | Przykład | Dlaczego jest niepoprawny? |
| --- | --- | --- |
| Klocek na sobie | `(1, 0, 0)` | Klocek 1 wskazuje siebie jako podłoże. |
| Nieistniejące podłoże | `(0, 4, 0)` | Przy trzech klockach klocek 4 nie istnieje. |
| Dwa klocki na jednym | `(0, 1, 1)` | Klocki 2 i 3 stoją bezpośrednio na klocku 1. |
| Cykl | `(2, 1, 0)` | Klocek 1 stoi na 2, a klocek 2 na 1. |

Przy sprawdzaniu powtarzających się podłoży pomijamy `0`, ponieważ na stole może stać wiele klocków.

Przy wykrywaniu cyklu program zaczyna od danego klocka i przechodzi po kolejnych podłożach. Poprawna ścieżka kończy się na stole, czyli na `0`. Jeśli wcześniej ponownie trafi na ten sam klocek, wykrywa cykl.

Lokalny zbiór `visited` w `_validate()` służy do wykrywania cyklu podparcia w jednym układzie. Zbiór `visited` w DFS będzie przechowywał całe odkryte układy — to osobne zastosowania tej samej nazwy.

### 2.5. Jak wyznaczane są wolne klocki?

```python
def clear_blocks(self) -> set[int]:
    occupied = {support for support in self.supports if support != 0}
    return set(range(1, self.size + 1)) - occupied
```

Dla `(0, 1, 0, 2, 3)`:

```text
Wszystkie klocki:                 {1, 2, 3, 4, 5}
Klocki będące podłożem innych:    {1, 2, 3}
Wolne klocki:                    {4, 5}
```

Wolny klocek nie występuje jako podłoże żadnego innego klocka.

### 2.6. legal_moves() i apply()

`legal_moves()` wyznacza ruchy możliwe w danym stanie. Dla naszego początku dostępne są tylko:

```python
(4, 0)
(5, 0)
```

Klocki 4 i 5 są wolne, ale stoją na innych klockach, więc zgodnie z wariantem podstawowym można je teraz przenieść na stół.

`apply(move)` sprawdza legalność wskazanego ruchu: istnienie klocków, wolność przenoszonego klocka, wolność docelowego podłoża, zakaz odkładania na siebie oraz reguły wariantu podstawowego. Odrzuca również pusty ruch polegający na odłożeniu na stół klocka, który już na nim leży.

Jeżeli ruch jest poprawny, tworzy nowy stan:

```python
supports = list(self.supports)
supports[block - 1] = target
return BlockWorldState(tuple(supports))
```

Przykład:

```text
Stan przed ruchem:    0 1 0 2 3
Ruch:                (5, 0)
Stan po ruchu:        0 1 0 2 0
```

Zmienia się podłoże jednego klocka. Powstający obiekt ponownie przechodzi walidację.

<a id="punkt-2"></a>

## 3. Punkt 2 instrukcji — DFS z nawrotami

**Główny plik:** [dfs.py](../src/dfs.py).

### 3.1. Co oznacza przeszukiwanie w głąb?

DFS daje pierwszeństwo dalszym następcom wybranej możliwości. Alternatywne możliwości zachowuje na później.

W tej implementacji decyduje o tym **stos**. Działa według zasady LIFO: ostatni dodany element zostaje pobrany jako pierwszy.

```python
stack.append(state)  # dodanie na wierzchołek
state = stack.pop()  # pobranie z wierzchołka
```

Nowe stany trafiają na wierzchołek, dlatego są rozpatrywane przed starszymi, oczekującymi alternatywami. Tak algorytm schodzi w głąb przestrzeni stanów.

### 3.2. Cztery najważniejsze zmienne

Na początku `solve_dfs()` powstają:

```python
stack = [start]
visited = {start}
parent = {}
expanded = 0
```

| Zmienna | Rola |
| --- | --- |
| `stack` | Stany oczekujące na rozpatrzenie. Każdy element to cały układ klocków. |
| `visited` | Wszystkie odkryte stany, również te nadal czekające na stosie. |
| `parent` | Dla odkrytego stanu zapisuje poprzedni stan i ruch, którym do niego dotarto. |
| `expanded` | Liczba stanów, dla których rozpoczęto generowanie następców. |

> **Do zapamiętania:** stos steruje dalszym wyszukiwaniem, `visited` zapobiega powtórzeniom, a `parent` pozwala później odtworzyć znaleziony plan.

### 3.3. Początek pętli: limity i pobranie stanu

```python
while stack:
    elapsed = perf_counter() - started
    if elapsed >= time_limit_seconds:
        return SearchResult("time_limit", (), expanded, elapsed)
    if expanded >= node_limit:
        return SearchResult("node_limit", (), expanded, elapsed)

    state = stack.pop()
```

Pętla trwa, dopóki na stosie pozostają możliwości. Przed każdą iteracją program sprawdza, czy może jeszcze kontynuować obliczenia, po czym zdejmuje stan ze stosu.

### 3.4. Sprawdzenie celu

```python
if state == goal:
    return SearchResult(
        "solved", _build_plan(start, goal, parent), expanded, elapsed
    )
expanded += 1
```

Jeżeli pobrany stan jest celem, program odtwarza plan i kończy wyszukiwanie.

Jeżeli celem nie jest, zwiększa `expanded` i przechodzi do generowania następców. Zwróć uwagę na kolejność: **stan docelowy nie zwiększa licznika rozwinięć**, ponieważ nie generujemy już jego następców.

### 3.5. Generowanie i zapamiętywanie następców

To kluczowy fragment algorytmu:

```python
moves = _ordered_moves(state, goal)
for move in reversed(moves):
    next_state = state.apply(move)
    if next_state not in visited:
        visited.add(next_state)
        parent[next_state] = (state, move)
        stack.append(next_state)
```

Kolejne linie oznaczają:

1. Wyznacz i uporządkuj legalne ruchy z bieżącego stanu.
2. Dla każdego ruchu utwórz stan będący jego skutkiem.
3. Sprawdź, czy ten układ był już odkryty.
4. Jeśli jest nowy, dopisz go do `visited`.
5. Zapamiętaj jego poprzednika i wykonany ruch w `parent`.
6. Dodaj układ na stos, aby można było później go rozpatrzyć.

Program tworzy następców przez `state.apply(move)`, więc przeszukiwanie korzysta z reguł ruchów zdefiniowanych w klasie stanu.

### 3.6. Dlaczego potrzebne jest visited?

Ruchy mogą prowadzić do wcześniejszych układów:

```text
Klocek 2 stoi na 1.
    ↓ ruch (2, 0)
Klocek 2 stoi na stole.
    ↓ ruch (2, 1)
Klocek 2 ponownie stoi na 1.
```

Bez zapamiętywania stanów algorytm mógłby wielokrotnie rozpatrywać taki sam obieg.

W tym kodzie stan trafia do `visited` już przy dodawaniu na stos. Dzięki temu nie zostanie dodany ponownie nawet wtedy, gdy nadal czeka na rozpatrzenie. Pierwsza zapisana informacja o jego poprzedniku pozostaje w `parent`.

### 3.7. Gdzie są nawroty, skoro nie ma „cofnij ruch”?

Każdy układ jest osobnym, niezmiennym obiektem. Alternatywy pozostają zapisane na stosie.

Jeżeli z bieżącego stanu nie zostaną dodane żadne nowe możliwości, kolejne `pop()` pobierze inną oczekującą możliwość. To realizuje powrót do wcześniejszego rozgałęzienia.

Nie trzeba wykonywać ruchów przeciwnych ani odtwarzać dawnego układu przez modyfikowanie bieżącego obiektu — wcześniej zapisany stan nadal istnieje.

Poniższy przykład jest schematem działania stosu, z umownymi nazwami stanów:

```text
Na stosie: [C, B]        ← wierzchołek jest po prawej

Pobieramy B.
Z B dodajemy D.
Na stosie: [C, D]

Pobieramy D.
Z D nie ma nowych stanów do dodania.
Na stosie: [C]

Pobieramy C i kontynuujemy inną możliwość.
```

`parent` nie steruje tym nawrotem. Jego zadaniem jest odtworzenie końcowej ścieżki po znalezieniu celu.

### 3.8. Porządkowanie ruchów: po co jest settled?

Funkcja `_ordered_moves()` wykorzystuje układ docelowy, aby najpierw rozpatrywać obiecujące ruchy.

Wyznacza zbiór `settled`: klocki ustawione poprawnie **wraz z całym podparciem pod nimi**.

Dla celu `[5 4 3 2 1]`:

- klocek 5 jest ustalony, gdy stoi na stole;
- klocek 4 jest ustalony, gdy stoi na ustalonym klocku 5;
- klocek 3 jest ustalony, gdy stoi na ustalonym klocku 4;
- analogicznie dla kolejnych klocków.

Warunek w kodzie ma postać:

```python
support == goal.support_of(block)
and (support == 0 or support in settled)
```

Samo poprawne bezpośrednie podłoże nie wystarcza. Jeśli podłoże trzeba będzie jeszcze przesunąć, stojący na nim klocek również może wymagać zdjęcia.

Pętla `while changed` powtarza sprawdzanie, ponieważ ustalenie jednego klocka może umożliwić ustalenie kolejnego. Jest to potrzebne również wtedy, gdy numery klocków w docelowej wieży nie odpowiadają kolejności sprawdzania ich w pętli.

### 3.9. Jakie priorytety otrzymują ruchy?

| Priorytet | Rodzaj ruchu | Intencja |
| ---: | --- | --- |
| 0 — najwyższy | Ustawienie klocka spoza `settled` na docelowym, gotowym podłożu. | Budowanie trwałego fragmentu celu. |
| 1 | Zdjęcie na stół klocka spoza `settled`. | Przygotowanie przebudowy i uwalnianie innych klocków. |
| 2 | Inne ruchy klocków spoza `settled`. | Pozostałe możliwości przebudowy. |
| 3 | Ruchy klocków należących do `settled`. | Naruszanie poprawnych fragmentów dopiero na końcu. |

Mniejsza liczba oznacza wcześniejsze rozpatrywanie. Przy równym priorytecie decyduje numer przenoszonego klocka, potem numer celu.

Ważne: porządkowanie zmienia kolejność wszystkich legalnych ruchów. Ruchy o niższym priorytecie nadal pozostają dostępne.

### 3.10. Dlaczego reversed(moves)?

Dla początku `0 1 0 2 3` dostępne ruchy to `(4, 0)` i `(5, 0)`.

Ruch `(5, 0)` ma wyższy priorytet: ustawia klocek 5 na jego docelowym podłożu, czyli na stole. Przygotowuje podstawę przyszłej wieży. Uporządkowana lista wygląda więc tak:

```python
[(5, 0), (4, 0)]
```

Chcemy jako pierwszy sprawdzić wynik `(5, 0)`. Ponieważ stos pobiera ostatni dodany element, stany dodajemy w odwrotnej kolejności:

```text
1. Dodaj stan po (4, 0).
2. Dodaj stan po (5, 0).
3. Następne pop() pobierze stan po (5, 0).
```

Po rozwinięciu startu stos wygląda tak, z wierzchołkiem po prawej:

```text
[(0, 1, 0, 0, 3), (0, 1, 0, 2, 0)]
```

Pierwszy układ czeka jako alternatywa, a drugi zostanie rozpatrzony jako następny.

### 3.11. Pełny przykład z instrukcji

Dla startu `0 1 0 2 3` i celu `2 3 4 5 0` kod znajduje następującą ścieżkę:

| Krok | Ruch | Otrzymany układ | Znaczenie |
| ---: | --- | --- | --- |
| 0 | — | `0 1 0 2 3` | Wieże `[1 2 4]` i `[3 5]`. |
| 1 | `(5, 0)` | `0 1 0 2 0` | Klocek 5 trafia na swoje docelowe podłoże. |
| 2 | `(4, 0)` | `0 1 0 0 0` | Zdjęcie klocka 4 uwalnia klocek 2. |
| 3 | `(4, 5)` | `0 1 0 5 0` | Powstaje docelowa podstawa `[5 4]`. |
| 4 | `(3, 4)` | `0 1 4 5 0` | Wieża rośnie do `[5 4 3]`. |
| 5 | `(2, 0)` | `0 0 4 5 0` | Klocek 2 zostaje zdjęty na stół. |
| 6 | `(2, 3)` | `0 3 4 5 0` | Powstaje wieża `[5 4 3 2]`. |
| 7 | `(1, 2)` | `2 3 4 5 0` | Osiągnięto cel. |

```text
(5, 0) -> (4, 0) -> (4, 5) -> (3, 4) -> (2, 0) -> (2, 3) -> (1, 2)
```

Ta sekwencja ma 7 ruchów. W tym przebiegu algorytm rozwinął 7 stanów: początkowy i sześć pośrednich. Ósmy stan na ścieżce jest celem, więc kończy wyszukiwanie bez kolejnego rozwinięcia.

Podczas rozwijania tych stanów algorytm generował również alternatywy. Pozostawały one na stosie, lecz nie trzeba było ich rozwijać przed znalezieniem celu.

### 3.12. Jak parent odtwarza rozwiązanie?

Przy odkryciu stanu zapisywane jest:

```python
parent[next_state] = (state, move)
```

Przykładowo:

```text
Do stanu:       0 1 0 2 0
Dotarto ze:     0 1 0 2 3
Wykonując ruch: (5, 0)
```

Po znalezieniu celu `_build_plan()` idzie po poprzednikach do początku:

```python
def _build_plan(start, goal, parent) -> tuple[Move, ...]:
    moves = []
    state = goal
    while state != start:
        state, move = parent[state]
        moves.append(move)
    return tuple(reversed(moves))
```

Ruchy są odczytywane od ostatniego do pierwszego. `reversed(moves)` ustawia je na końcu w kolejności od startu do celu.

Stos nie musi zachowywać całej historii przeszukiwania. Informacja potrzebna do odtworzenia rozwiązania pozostaje w `parent`.

### 3.13. Czy DFS znajduje najkrótszą sekwencję?

**DFS nie gwarantuje najkrótszego planu.** Kończy pracę przy pierwszym znalezionym celu. Może znaleźć plan mający 10 ruchów, zanim sprawdzi inną drogę mającą 3 ruchy.

Porządkowanie pomaga wybierać obiecujące ruchy, lecz nie daje ogólnej gwarancji optimum. Dla wariantu na 4 punkty wymagana jest poprawna sekwencja, więc takie rozwiązanie spełnia zakres zadania.

W przykładzie referencyjnym znalezione 7 ruchów zgadza się z podaną w instrukcji długością najkrótszego planu dla tego konkretnego przypadku.

### 3.14. Limity, statystyki i SearchResult

Funkcja `solve_dfs()` ma domyślnie:

```python
node_limit = 200_000
time_limit_seconds = 10.0
```

Wynik przechowuje obiekt `SearchResult`:

| Pole | Znaczenie |
| --- | --- |
| `status` | Sposób zakończenia wyszukiwania. |
| `moves` | Znaleziona sekwencja ruchów. |
| `expanded_nodes` | Liczba rozwiniętych stanów. |
| `elapsed_seconds` | Zmierzony czas wyszukiwania. |

Możliwe statusy to `solved`, `node_limit`, `time_limit` i `no_solution`. Ostatni oznacza wyczerpanie stosu bez odnalezienia celu. Właściwość `result.solved` sprawdza, czy status jest równy `"solved"`.

Pomiar korzysta z `perf_counter()`. Zwracany przy sukcesie czas pochodzi z początku iteracji rozpoznającej cel. Nie obejmuje późniejszej rekonstrukcji planu, weryfikacji ani zapisu wyników.

**Rozwinięte stany a odkryte stany:** podczas jednego rozwinięcia może powstać wiele następców. Dlatego `expanded_nodes`, liczba elementów `visited` i liczba elementów stosu opisują różne rzeczy.

W badanych 65 problemach liczba rozwinięć jest równa długości znalezionego planu. W tych przypadkach program nie rozwinął stanów spoza zwróconej ścieżki. Nadal mógł wygenerować i zapamiętać liczne alternatywy.

<a id="punkt-3"></a>

## 4. Punkt 3 instrukcji — weryfikacja znalezionej sekwencji

**Główny plik:** [verifier.py](../src/verifier.py).

Weryfikator otrzymuje start, cel i listę ruchów. Zaczyna ponownie od stanu początkowego i wykonuje wszystkie ruchy:

```python
state = start

for number, move in enumerate(moves, 1):
    try:
        state = state.apply(move)
    except ValueError as error:
        return False, f"Ruch {number} {move}: {error}"
```

`enumerate(moves, 1)` numeruje ruchy od 1. Jeśli `apply()` zgłosi błąd, weryfikator zwraca numer pierwszego nielegalnego ruchu i przyczynę.

Przykładowo `(4, 5)` jest nielegalne dla naszego początku: klocek 4 stoi na klocku 2, więc w wariancie podstawowym musi najpierw trafić na stół.

Po wykonaniu całej sekwencji sprawdzany jest cel:

```python
if state != goal:
    return False, "Stan końcowy nie jest stanem docelowym."

return True, "Plan jest poprawny."
```

Legalność ruchów i osiągnięcie celu to dwa osobne wymagania. Plan zawierający tylko `(4, 0)` jest legalny, ale niepełny: nie prowadzi do docelowej wieży, więc zostanie odrzucony.

Weryfikator działa osobno od wyszukiwania, lecz współdzieli z nim metodę `apply()`. Sprawdza plan według tego samego modelu ruchów. Poprawność samych reguł dodatkowo sprawdzają testy automatyczne.

<a id="punkt-4"></a>

## 5. Punkt 4 instrukcji — losowe problemy i pomiary

**Główny plik:** [experiments.py](../src/experiments.py).

### 5.1. Generowanie pojedynczego układu

Funkcja `random_state()` zaczyna od numerów klocków i losuje ich kolejność:

```python
blocks = list(range(1, size + 1))
generator.shuffle(blocks)
supports = [0] * size
```

Następnie dla kolejnych par w tej kolejności wybiera, czy następny klocek rozpocznie nową wieżę na stole, czy stanie na poprzednim:

```python
for previous, block in zip(blocks, blocks[1:]):
    supports[block - 1] = 0 if generator.random() < 0.5 else previous
```

Każdy klocek występuje raz w wylosowanej kolejności. Łączenie kolejnych klocków w wieże zapobiega cyklom i ustawieniu dwóch klocków bezpośrednio na jednym podłożu.

Taki generator tworzy poprawne układy, ale nie losuje jednostajnie ze zbioru wszystkich możliwych układów. Sprzyja układom z wieloma krótkimi wieżami.

### 5.2. Ile problemów powstaje i po co jest ziarno?

Domyślne parametry `generate_cases()` to:

```python
seed = 20261017
min_size = 3
max_size = 15
cases_per_size = 5
```

Dla każdego N losowanych jest pięć par start–cel. Daje to:

```text
13 rozmiarów × 5 problemów = 65 problemów
```

Jeśli cel jest identyczny ze startem, zostaje wylosowany ponownie. Stałe ziarno i ten sam kod pozwalają odtworzyć te same przypadki.

### 5.3. Rozwiązanie i zapis wyników

Dla każdego przypadku `save_results()`:

1. Wywołuje `solve_dfs()`.
2. Jeśli znaleziono plan, przekazuje go do `verify_plan()`.
3. Zapisuje start, cel, status, długość planu, liczbę rozwiniętych węzłów, czas i wynik weryfikacji.
4. Dla N ≤ 8 zapisuje również pełną sekwencję ruchów.

Długość planu pochodzi z `len(result.moves)`, liczba rozwinięć z `result.expanded_nodes`, a czas z `result.elapsed_seconds`.

Wyniki trafiają do [results/results.csv](../results/results.csv). W eksperymentach domyślny limit czasu wynosi **2 sekundy na problem** i zastępuje domyślne 10 sekund z `solve_dfs()`. Limit węzłów nadal wynosi 200 000.

W zapisanej próbce wszystkie 65 problemów ma status `solved` i weryfikację `OK`. Komplet pomiarów oraz sekwencje dla N ≤ 8 znajdują się w [raporcie](raport.md).

<a id="main"></a>

## 6. Jak wszystko łączy main.py?

**Plik:** [main.py](../src/main.py).

`main.py` obsługuje jeden problem z pliku. Najpierw wybiera ścieżkę: argument podany przy uruchomieniu albo domyślną wartość `INPUT_FILE`.

```python
input_file = sys.argv[1] if len(sys.argv) > 1 else INPUT_FILE
```

Następnie wczytuje i sprawdza dane:

```python
try:
    start_state, goal_state = read_problem(input_file)
except (OSError, ValueError) as error:
    print("Błąd danych wejściowych:", error)
    return
```

Po poprawnym wczytaniu uruchamia wyszukiwanie:

```python
result = solve_dfs(start_state, goal_state)
```

Jeśli znaleziono rozwiązanie, wypisuje ruchy i weryfikuje plan:

```python
valid, message = verify_plan(start_state, goal_state, result.moves)
```

Cały przepływ wygląda następująco:

```text
Plik wejściowy
    ↓ read_problem()
Poprawne obiekty start i cel
    ↓ solve_dfs()
Sekwencja ruchów i statystyki wyszukiwania
    ↓ verify_plan()
Wynik sprawdzenia i komunikat dla użytkownika
```

`experiments.py` powtarza wyszukiwanie i weryfikację dla wielu losowych problemów. `main.py` służy do uruchomienia pojedynczego przypadku; nie generuje raportu Markdown ani zestawu 65 pomiarów.

<a id="pytania"></a>

## 7. Pytania kontrolne

| Pytanie | Odpowiedź |
| --- | --- |
| Co jest węzłem przeszukiwania? | Cały układ wszystkich klocków. |
| Co jest krawędzią? | Jeden legalny ruch. |
| Dlaczego to jest DFS? | Nowi następcy trafiają na wierzchołek stosu i są pobierani przed starszymi alternatywami. |
| Co zawiera stos? | Odkryte układy oczekujące na rozpatrzenie. |
| Po co jest `visited`? | Aby nie dodawać wielokrotnie tych samych układów i nie krążyć po cyklach. |
| Po co jest `parent`? | Aby po znalezieniu celu odtworzyć ścieżkę od startu. |
| Jak odbywa się nawrót? | Przez pobranie kolejnego oczekującego stanu ze stosu. |
| Dlaczego nie ma cofania ruchów w obiekcie? | Stany są niezmienne; alternatywne układy już istnieją jako osobne obiekty. |
| Po co `reversed(moves)`? | Aby najlepszy ruch został dodany na stos jako ostatni i pobrany jako pierwszy. |
| Co oznacza `settled`? | Klocki poprawnie ustawione wraz z całym podparciem pod nimi. |
| Czy stan odkryty jest już rozwinięty? | Może dopiero czekać na stosie; rozwinięcie oznacza rozpoczęcie generowania jego następców. |
| Czy cel zwiększa `expanded`? | Nie, sprawdzenie celu następuje przed zwiększeniem licznika. |
| Czy DFS gwarantuje najkrótszy plan? | Nie; kończy przy pierwszym znalezionym celu. |
| Co sprawdza weryfikator? | Legalność każdego ruchu i równość końcowego układu z celem. |

### Najważniejsze rozróżnienia

- **Stan a ruch:** stan opisuje cały świat; ruch przekształca jeden stan w następny.
- **Legalność a rozwiązanie:** ruchy mogą być legalne, a plan nadal może nie osiągać celu.
- **Odkrycie a rozwinięcie:** stan można zapamiętać i odłożyć na stos bez generowania jego następców.
- **Stos a ścieżka rozwiązania:** stos zawiera oczekujące możliwości; końcowa ścieżka jest odtwarzana przez `parent`.
- **Porządkowanie a usuwanie ruchów:** priorytet zmienia kolejność, zachowując legalne alternatywy.
- **Poprawność a optymalność:** plan może poprawnie rozwiązywać problem, choć istnieje krótsza sekwencja.

<a id="uruchamianie"></a>

## 8. Uruchamianie i pliki źródłowe

Polecenia wykonuj z katalogu `blocks_world_basic`.

Uruchomienie przykładu z instrukcji:

```powershell
py -3 -m src.main examples/example.txt
```

Uruchomienie istniejących testów:

```powershell
py -3 -m unittest discover -s tests -v
```

Wygenerowanie i rozwiązanie 65 problemów:

```powershell
py -3 -m src.experiments
```

Ostatnie polecenie zastępuje zawartość `results/results.csv` nowymi wynikami. Układy można odtworzyć z tego samego ziarna, natomiast czasy zależą od warunków wykonania.

| Plik | Za co odpowiada? |
| --- | --- |
| [state.py](../src/state.py) | Reprezentacja układu, walidacja, wolne klocki, legalne ruchy i ich wykonanie. |
| [input_reader.py](../src/input_reader.py) | Odczyt dwóch układów z pliku. |
| [dfs.py](../src/dfs.py) | Wyszukiwanie, porządkowanie ruchów, limity i odtwarzanie planu. |
| [verifier.py](../src/verifier.py) | Sprawdzenie legalności sekwencji i osiągnięcia celu. |
| [experiments.py](../src/experiments.py) | Losowanie przypadków, uruchamianie pomiarów i zapis CSV. |
| [main.py](../src/main.py) | Obsługa pojedynczego problemu i wypisywanie wyniku. |
| [raport.md](raport.md) | Szczegółowe wyniki eksperymentów i ich interpretacja. |
| [projekt1.pdf](../../projekt1.pdf) | Instrukcja projektu i wymagania dla poszczególnych progów. |

Notatka jest samodzielnym materiałem do nauki; odsyłacze do kodu działają po otwarciu jej w katalogu `blocks_world_basic/reports` w projekcie.
