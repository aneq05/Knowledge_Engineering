# Blocks World — opis problemu i podejścia do rozwiązania

## Na czym polega problem?

**Blocks World** (świat klocków) to klasyczny problem planowania w sztucznej inteligencji. Środowisko składa się ze stołu, zbioru nazwanych klocków oraz robota z jednym chwytakiem. Klocki mogą leżeć bezpośrednio na stole albo jeden na drugim, tworząc wieże. Chwytak może trzymać najwyżej jeden klocek naraz.

Zadaniem systemu planującego jest znalezienie skończonej sekwencji dozwolonych działań, która przekształci stan początkowy w stan spełniający wszystkie warunki celu. Problem dobrze ilustruje podstawowe zagadnienia planowania: reprezentację wiedzy, warunki wykonania i skutki działań, zależności między podcelami oraz przeszukiwanie przestrzeni stanów.

## Reprezentacja stanu

Stan świata opisujemy za pomocą predykatów logicznych. W bibliotece `unified-planning` są one reprezentowane jako fluenty boolowskie:

- `on(x, y)` — klocek `x` leży bezpośrednio na klocku `y`,
- `on_table(x)` — klocek `x` leży bezpośrednio na stole,
- `clear(x)` — na klocku `x` nic nie leży, więc można go podnieść lub coś na nim położyć,
- `holding(x)` — chwytak trzyma klocek `x`,
- `hand_empty` — chwytak jest pusty.

Kompletny stan musi być logicznie spójny. Klocek nie powinien na przykład jednocześnie leżeć na stole i na innym klocku. Jeżeli prawdziwe jest `holding(A)`, wartość `hand_empty` musi być fałszywa. W modelu użytym w notatniku fluenty bez jawnie podanej wartości początkowej otrzymują domyślnie wartość `False`, dlatego wszystkie prawdziwe fakty początkowe trzeba określić wprost.

## Operatory i model STRIPS

Każde działanie jest opisane przez **warunki wstępne** (*preconditions*) i **efekty**. Warunki muszą być spełnione przed wykonaniem działania. Efekty określają fakty, które po wykonaniu działania stają się prawdziwe albo fałszywe. Fakty niewymienione w efektach zachowują dotychczasową wartość — jest to założenie ramowe (*frame assumption*).

Standardowy model zawiera cztery operatory:

1. `pick_up(x)` — podniesienie wolnego klocka `x` ze stołu,
2. `put_down(x)` — odłożenie trzymanego klocka `x` na stół,
3. `stack(x, y)` — położenie trzymanego klocka `x` na wolnym klocku `y`,
4. `unstack(x, y)` — zdjęcie wolnego klocka `x` z klocka `y`.

Poprawność definicji operatorów jest kluczowa. Jeden pominięty efekt, na przykład brak usunięcia `on(x, y)` podczas `unstack`, może stworzyć niemożliwy stan, w którym klocek jest jednocześnie trzymany i nadal leży na innym klocku.

## Anomalia Sussmana

Instancja wykorzystana w notatniku jest znana jako **anomalia Sussmana**. Początkowo `C` leży na `A`, natomiast `A` i `B` znajdują się na stole. Celem jest zbudowanie wieży, w której `A` leży na `B`, a `B` na `C`.

```text
Stan początkowy       Stan docelowy
                          A
    C                     B
    A   B                 C
  ---------             -----
```

Podcele `on(A, B)` i `on(B, C)` nie są niezależne. Próba trwałego osiągnięcia pierwszego z nich może utrudnić osiągnięcie drugiego. Najpierw należy zdjąć `C` z `A`, następnie zbudować `B` na `C`, a dopiero na końcu położyć `A` na `B`.

Minimalny plan ma sześć działań:

```text
unstack(C, A)
put_down(C)
pick_up(B)
stack(B, C)
pick_up(A)
stack(A, B)
```

Przykład pokazuje, dlaczego proste wykonywanie podcelów po kolei, bez możliwości zmiany wcześniejszych decyzji, nie zawsze działa. Planista musi uwzględniać interakcje między podcelami.

## Podejścia do rozwiązania

### Przeszukiwanie progresywne (forward search)

Algorytm rozpoczyna od stanu początkowego, generuje wszystkie legalne działania i przechodzi do kolejnych stanów aż do osiągnięcia celu. BFS znajduje plan o minimalnej liczbie kroków przy jednakowych kosztach działań, ale może zużywać dużo pamięci. A* ogranicza liczbę odwiedzonych stanów za pomocą heurystyki oceniającej odległość od celu.

### Przeszukiwanie regresywne (backward search)

Przeszukiwanie zaczyna się od warunków celu. Algorytm ustala, jakie działania mogą je wytworzyć i jakie warunki muszą być wcześniej spełnione. Pozwala to skupić się na działaniach istotnych dla celu, ale wymaga ostrożnego uwzględniania zależności między podcelami.

### Planowanie w przestrzeni planów (partial-order planning)

Zamiast natychmiast ustalać pełną kolejność działań, tworzy się częściowo uporządkowany plan. Ograniczenia kolejności są dodawane tylko wtedy, gdy są konieczne. Podejście dobrze pokazuje konflikty i zależności między podcelami anomalii Sussmana.

### Planowanie heurystyczne

Nowoczesne planery, takie jak Fast Downward, przekształcają problem i wykorzystują heurystyki do wyboru najbardziej obiecujących stanów. Dzięki temu nie muszą wyczerpująco sprawdzać całej przestrzeni stanów.

### Kodowanie jako SAT lub CSP

Istnienie planu o określonej długości można zapisać jako problem spełnialności logicznej SAT albo problem spełniania ograniczeń CSP. Jeżeli dla danej długości rozwiązanie nie istnieje, limit jest zwiększany i problem rozwiązuje się ponownie.

## Podejście zastosowane w notatniku

Notatnik wykorzystuje planowanie klasyczne, czyli przyjmuje następujące założenia:

- środowisko jest w pełni obserwowalne,
- działania są deterministyczne,
- stan zmienia się wyłącznie wskutek wykonywanych działań,
- planner zna pełny stan początkowy i warunki celu.

`OneshotPlanner` wybiera silnik zgodny z rodzajem problemu. Metryka `MinimizeSequentialPlanLength` służy do znalezienia planu z minimalną liczbą działań. Otrzymany plan można zweryfikować za pomocą `SequentialSimulator`, wykonując kolejne działania od stanu początkowego i sprawdzając, czy stan końcowy spełnia cel.
