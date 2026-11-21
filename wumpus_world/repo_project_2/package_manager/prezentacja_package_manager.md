# Prezentacja projektu `package_manager`

## Ogólna idea projektu

Projekt jest menedżerem pakietów wykorzystującym solver Z3. Program otrzymuje:

1. repozytorium pakietów z wersjami, zależnościami i konfliktami,
2. żądania użytkownika,
3. opcjonalnie istniejący stan środowiska.

Następnie:

1. wczytuje i waliduje dane,
2. tworzy zmienną logiczną dla każdej możliwej wersji pakietu,
3. buduje bazę wiedzy z aksjomatami,
4. dodaje żądania użytkownika jako twarde ograniczenia,
5. szuka rozwiązania spełniającego wszystkie warunki,
6. wybiera najlepsze rozwiązanie według kryteriów leksykograficznych,
7. niezależnie weryfikuje otrzymany stan,
8. pokazuje plan zmian i końcowy stan.

Najważniejsze rozróżnienie:

- **aksjomaty** opisują zasady repozytorium i mówią, co jest dozwolone,
- **twarde ograniczenia** opisują bezpośrednie żądania użytkownika,
- **kryteria** określają, które poprawne rozwiązanie jest najlepsze.

Przykładowo:

- aksjomat zabrania instalacji dwóch wersji tego samego pakietu,
- żądanie wymusza instalację `app==2.0`,
- kryterium rozstrzyga, czy spośród kilku poprawnych rozwiązań wybrać nowszą wersję albo mniejszą liczbę pakietów.

---

# CZĘŚĆ I — OSOBA 1

## 1. Krótkie wprowadzenie

### Gotowa wypowiedź

> Nasz projekt to menedżer pakietów oparty na logice zdań i solverze Z3. Repozytorium opisuje pakiety, ich wersje, zależności oraz konflikty. Dla każdej wersji tworzymy zmienną logiczną, na przykład `app==2.0`, która oznacza, że ta wersja może zostać zainstalowana. Następnie tworzymy aksjomaty opisujące reguły repozytorium. Solver wyszukuje stan spełniający te reguły oraz żądania użytkownika. Jeśli istnieje wiele poprawnych stanów, wybieramy najlepszy według uporządkowanych kryteriów.

> W progu 4 rozwiązujemy instalację do pustego środowiska. W progu 6 rozszerzamy ten mechanizm o istniejący stan, dlatego musimy również uwzględniać usuwanie pakietów, zmiany wersji i zachowanie dotychczasowego środowiska.

## 2. Modele danych — `models.py`

Plik: [`package_manager/models.py`](package_manager/models.py)

### Najważniejsze elementy

#### `ComparisonOperator`

Enum przechowujący dozwolone operatory:

```text
==, !=, <, <=, >, >=
```

#### `VersionConstraint`

Reprezentuje jedno ograniczenie wersji, na przykład:

```text
>=2.0
```

Metoda `matches` porównuje rzeczywistą wersję z ograniczeniem za pomocą `version_key`.

#### `Requirement`

Reprezentuje wymaganie składające się z nazwy pakietu i ograniczeń wersji.

Przykłady:

```text
app
app==2.0
lib>=1.0 <2.0
```

Metoda `matches` sprawdza, czy dana wersja spełnia wszystkie ograniczenia. Używamy tej samej klasy zarówno dla żądań użytkownika, jak i dla zależności w repozytorium.

#### `Dependency`

Przechowuje alternatywy wymagania rozdzielone znakiem `|`.

Przykład:

```text
json-fast | json-slow
```

Spełnienie jednej alternatywy wystarcza do spełnienia całej zależności.

#### `PackageVersion`

Opisuje jedną wersję pakietu:

- nazwę,
- numer wersji,
- listę zależności `requires`,
- listę konfliktów `conflicts`.

#### `Repository`

Przechowuje wszystkie pakiety i ich wersje.

#### `InstalledPackage` i `EnvironmentState`

Opisują stan środowiska. `InstalledPackage` zawiera również flagę `manual`, która odróżnia pakiet wskazany bezpośrednio przez użytkownika od pakietu zainstalowanego jako zależność.

### Gotowa wypowiedź

> Najpierw zdefiniowaliśmy osobne modele danych. Dzięki temu repozytorium, wymaganie, zależność i stan środowiska nie są reprezentowane przez przypadkowe słowniki w wielu miejscach. Każdy model ma jednoznaczną odpowiedzialność, a pozostałe moduły mogą operować na tych samych obiektach.

## 3. Wersje — `versions.py`

Plik: [`package_manager/versions.py`](package_manager/versions.py)

### Funkcja `version_key`

Funkcja:

- rozdziela wersję na liczby,
- zwraca krotkę liczb,
- usuwa końcowe zera,
- odrzuca niepoprawne wersje.

Przykłady:

```text
1.10 -> (1, 10)
1.9  -> (1, 9)
1.0  -> (1,)
1.0.0 -> (1,)
```

Dzięki temu:

```text
1.10 > 1.9
1.0 = 1.0.0
```

### Gotowa wypowiedź

> Nie porównujemy wersji jako napisów, ponieważ porównanie tekstowe byłoby błędne dla wartości takich jak `1.10` i `1.9`. Funkcja `version_key` zamienia wersję na krotkę liczb. Jest również używana przy sprawdzaniu, czy dwie wersje zapisane różnym formatem są faktycznie tą samą wersją.

## 4. Parsowanie wymagań — `requirements_parser.py`

Plik: [`package_manager/requirements_parser.py`](package_manager/requirements_parser.py)

### `normalize_name`

Funkcja:

- sprawdza poprawność nazwy,
- zamienia nazwę na małe litery,
- zamienia ciągi `-`, `_` i `.` na pojedynczy myślnik.

Przykładowo nazwy `Foo_Bar`, `foo-bar` i `foo.bar` są normalizowane do tej samej postaci.

### `parse_requirement`

Parsuje wymaganie użytkownika lub wymaganie zapisane w repozytorium.

Przykład:

```text
lib >=1.0, <2.0
```

zostaje zamieniony na obiekt `Requirement` zawierający dwa `VersionConstraint`.

### `parse_dependency`

Dzieli tekst po `|` i tworzy obiekt `Dependency` z alternatywami.

### `_parse_constraints` i `_after_constraint`

Funkcje pomocnicze:

- odczytują kolejne ograniczenia,
- sprawdzają operatory,
- kontrolują separatory,
- odrzucają niepoprawny zapis, na przykład przecinek na końcu.

### Gotowa wypowiedź

> Parsowanie jest wykonywane raz, na wejściu. Późniejsze moduły nie muszą analizować napisów, tylko pracują na obiektach `Requirement`, `Dependency` i `VersionConstraint`.

## 5. Wczytywanie i walidacja — `json_reader.py` i `loaders.py`

Pliki:

- [`package_manager/json_reader.py`](package_manager/json_reader.py)
- [`package_manager/loaders.py`](package_manager/loaders.py)

### `json_reader.py`

Moduł odpowiada za bezpieczne odczytanie JSON-a. Wykrywa:

- błędy składni,
- powtórzone klucze,
- błędne typy,
- niedozwolone stałe,
- miejsce błędu w strukturze dokumentu.

### `loaders.py`

#### `load_repository`

Wczytuje repozytorium i sprawdza jego strukturę. Weryfikuje między innymi:

- obecność pola `packages`,
- poprawność nazw pakietów,
- poprawność wersji,
- niepowtarzalność pakietów i wersji,
- poprawność `requires` i `conflicts`,
- brak samozależności,
- brak konfliktu pakietu z samym sobą.

#### `_read_lines`

Czyta pliki tekstowe, pomija puste linie i komentarze oraz zachowuje numery linii.

#### `load_requests`

Wczytuje żądania użytkownika.

#### `load_state`

Wczytuje stan początkowy w formacie:

```text
NAZWA WERSJA [manual]
```

#### `load_names`

Wczytuje listę nazw pakietów przeznaczonych do usunięcia.

### Gotowa wypowiedź

> Walidujemy dane możliwie wcześnie i zgłaszamy błędy z miejscem ich wystąpienia. Dzięki temu solver otrzymuje już poprawne obiekty, a błędy strukturalne nie mieszają się z błędami logicznymi.

## 6. Baza wiedzy — `knowledge_base.py`

Plik: [`package_manager/knowledge_base.py`](package_manager/knowledge_base.py)

## 6.1. Klasa `Axiom`

Przechowuje:

- techniczną nazwę aksjomatu,
- czytelną etykietę,
- formułę Z3.

Etykiety są potrzebne później do wyjaśnienia braku rozwiązania.

## 6.2. Klasa `KnowledgeBase`

Przechowuje:

- słownik zmiennych logicznych,
- listę aksjomatów.

### `add_axiom`

Dodaje aksjomat do listy i nadaje mu nazwę `axiom_0`, `axiom_1` itd.

### `add_to_solver`

Dodaje wszystkie aksjomaty do solvera. Opcjonalnie używa `assert_and_track`, aby można było śledzić, który aksjomat uczestniczy w sprzeczności.

## 6.3. `build_knowledge_base`

Tworzy obiekt `_KnowledgeBaseBuilder`, a następnie wywołuje:

1. `create_variables`,
2. `add_axioms`.

## 6.4. `create_variables`

Dla każdej pary pakiet–wersja tworzy zmienną:

```text
package==version
```

Przykład:

```text
app==1.0
app==2.0
lib==1.0
lib==2.0
```

## 6.5. `matching_versions`

Zwraca wszystkie zmienne odpowiadające wersjom spełniającym wymaganie.

Jeśli żadna wersja nie pasuje, funkcja ostrzega, ale nie przerywa budowy bazy. Wtedy dana zależność staje się niemożliwa do spełnienia.

## 6.6. Aksjomat A1 — `add_single_version_axiom`

Kod tworzy:

```python
z3.AtMost(*variables, 1)
```

Przykład logiczny:

```text
AtMost(lib==1.0, lib==1.5, lib==2.0, 1)
```

Znaczenie:

> Można zainstalować najwyżej jedną wersję tego samego pakietu.

## 6.7. Aksjomat A2 — `add_dependencies`

Dla każdej zależności tworzy:

```text
p==v -> (x1 or x2 or ...)
```

Przykład:

```text
app==2.0 -> lib==2.0
```

Jeśli istnieją alternatywy:

```text
tool==1.1 -> (json-fast==1.0 or json-slow==1.0)
```

Jeżeli lista pasujących wersji jest pusta, `z3.Or([])` jest fałszem. Wtedy dana wersja pakietu nie może zostać wybrana.

## 6.8. Aksjomat A3 — `add_conflicts`

Dla każdego konfliktu tworzy:

```text
p==v -> not(q==w)
```

Przykład:

```text
legacy==1.0 -> not(util==2.0)
```

Znaczenie:

> Wybranie jednej wersji blokuje każdą pasującą konfliktującą wersję.

### Gotowa wypowiedź podsumowująca

> Aksjomaty nie są kryteriami. One definiują zbiór poprawnych stanów. A1 pilnuje, żeby nie instalować dwóch wersji pakietu, A2 wymusza zależności, a A3 zabrania konfliktów. Wszystkie aksjomaty powstają na podstawie repozytorium, więc baza wiedzy działa dla różnych danych wejściowych.

## 7. Instalacja do pustego środowiska — `installer.py`, próg 4.3

Plik: [`package_manager/installer.py`](package_manager/installer.py)

### `install`

Buduje bazę wiedzy i wywołuje `solve`.

### `_request_formula`

Zamienia wymaganie użytkownika na formułę będącą alternatywą wszystkich pasujących wersji.

Dla:

```text
app
```

otrzymujemy:

```text
app==1.0 or app==2.0
```

Dla:

```text
app==2.0
```

zostaje tylko właściwa wersja.

### `_costs`

Buduje trzy koszty:

1. `requested_staleness` — przestarzałość pakietów żądanych,
2. `package_count` — liczba wszystkich zainstalowanych pakietów,
3. `dependency_staleness` — przestarzałość pozostałych pakietów.

Wersja najnowsza ma rangę `0`, kolejna `1` itd.

## Jak obliczana jest przestarzałość wersji?

W projekcie przestarzałość nie oznacza wieku wersji ani różnicy między numerami
wersji. Jest to **pozycja wersji w uporządkowanej liście wersji danego pakietu**.
Lista jest sortowana od najnowszej do najstarszej, a następnie wersje otrzymują
rangi:

| Wersja | Ranga przestarzałości |
|---|---:|
| `3.0` | `0` |
| `2.0` | `1` |
| `1.5` | `2` |
| `1.0` | `3` |

Ranga `0` oznacza więc wersję najnowszą. Im większa ranga, tym starsza jest
wybrana wersja i tym większy jest koszt optymalizacji.

### Gdzie jest to obliczane?

W instalacji do pustego środowiska funkcja `_costs` wykonuje:

```python
ordered_versions = sorted(versions, key=version_key, reverse=True)
```

Następnie `enumerate` przypisuje rangę:

```python
for rank, version in enumerate(ordered_versions):
```

Dla każdej możliwej wersji tworzony jest koszt:

```python
z3.If(selected, rank, 0)
```

Znaczenie tego wyrażenia jest następujące:

- jeśli wersja jest wybrana przez solver, do kosztu dodajemy jej rangę,
- jeśli wersja nie jest wybrana, dodajemy `0`.

Aksjomat A1 gwarantuje, że dla jednego pakietu wybrana może być najwyżej jedna
wersja, więc do sumy trafia koszt właściwie wybranej wersji.

### Jak powstaje suma przestarzałości?

Przykład dla pakietu `lib`:

```text
lib==3.0 -> koszt 0
lib==2.0 -> koszt 1
lib==1.5 -> koszt 2
lib==1.0 -> koszt 3
```

Jeżeli solver wybierze `lib==1.5`, koszt tego pakietu wynosi `2`.

Jeżeli kilka pakietów ma być ocenionych razem, ich rangi są sumowane. Na
przykład:

```text
lib==2.0  -> 1
util==1.0 -> 2
łączna przestarzałość -> 1 + 2 = 3
```

Funkcja `_sum_costs` zwraca sumę wszystkich składników. Jeżeli lista jest
pusta, zwraca `0`, dzięki czemu brak pakietów w danej grupie nie powoduje błędu.

### Pakiety żądane i pozostałe

Funkcja `_costs` dzieli koszty na dwie grupy:

- `requested_costs` — pakiety wskazane przez użytkownika,
- `other_costs` — pozostałe pakiety, zwykle zależności.

Decyzję podejmuje ten fragment:

```python
costs = requested_costs \
    if normalize_name(package) in requested_names \
    else other_costs
```

Dlatego w instalacji do pustego środowiska kolejność kryteriów ma znaczenie:

1. najpierw minimalizowana jest przestarzałość pakietów żądanych,
2. potem liczba wszystkich pakietów,
3. dopiero na końcu przestarzałość zależności.

Przykładowo solver może wybrać starszą zależność, jeśli dzięki temu nadal
spełni żądanie, ale nie może wybrać starszej wersji pakietu żądanego, jeżeli
istnieje rozwiązanie z nowszą wersją i wcześniejsze kryteria są spełnione.

### Przykład pełnego porównania

Załóżmy, że istnieją dwa poprawne rozwiązania:

| Rozwiązanie | Przestarzałość żądanych | Liczba pakietów | Przestarzałość zależności |
|---|---:|---:|---:|
| A | `0` | `4` | `3` |
| B | `1` | `3` | `0` |

Solver wybierze rozwiązanie **A**, ponieważ pierwsze kryterium ma najwyższy
priorytet. Mniejsza liczba pakietów w rozwiązaniu B nie może zrekompensować
starszej wersji pakietu żądanego.

### Ranga wersji a `version_key`

Ranga jest wyznaczana przez `version_key` z pliku
[`package_manager/versions.py`](package_manager/versions.py), a nie przez
porównanie napisów. Dzięki temu sortowanie jest poprawne:

```text
1.10 > 1.9
1.0 = 1.0.0
```

Jeśli repozytorium zawiera wersje:

```text
1.9, 1.10, 2.0
```

to kolejność i rangi są następujące:

```text
2.0  -> 0
1.10 -> 1
1.9  -> 2
```

### Gotowa wypowiedź

> Przestarzałość wersji obliczamy jako jej rangę na liście wersji tego samego
> pakietu posortowanej od najnowszej. Najnowsza wersja ma koszt zero, druga
> koszt jeden itd. Dla każdej wersji solver dodaje jej rangę tylko wtedy, gdy
> ta wersja została wybrana. Następnie rangi są sumowane dla odpowiedniej grupy
> pakietów. W instalacji do pustego środowiska najpierw minimalizujemy
> przestarzałość pakietów żądanych, a dopiero później przestarzałość zależności.
> To powoduje, że bezpośrednie żądanie użytkownika ma większy priorytet niż
> wybór najnowszych wersji pakietów pomocniczych.

### `solve`

W tej funkcji:

1. tworzymy `z3.Optimize`,
2. ustawiamy `priority="lex"`,
3. dodajemy aksjomaty,
4. dodajemy żądania jako twarde ograniczenia,
5. minimalizujemy koszty w określonej kolejności,
6. sprawdzamy wynik,
7. odczytujemy model,
8. niezależnie weryfikujemy wynik.

### `_read_state`

Odczytuje z modelu Z3 wybrane zmienne i buduje `EnvironmentState`.

Pakiety żądane przez użytkownika są oznaczane jako `manual`.

### `_sum_costs`

Sumuje koszty. Dla pustej listy zwraca zero zamiast pustego wyrażenia.

### `InstallationResult`

Przechowuje:

- końcowy stan,
- przestarzałość żądanych pakietów,
- liczbę pakietów,
- przestarzałość zależności.

### Gotowa wypowiedź

> W progu 4 nie mamy stanu początkowego. Dlatego program wybiera najnowsze wersje żądanych pakietów, następnie minimalizuje liczbę pakietów, a na końcu wybiera możliwie nowe zależności. Kolejność jest ważna, ponieważ `priority="lex"` oznacza, że późniejsze kryterium nie może pogorszyć wcześniejszego.

## 8. Weryfikacja bez solvera — `verification.py`

Plik: [`package_manager/verification.py`](package_manager/verification.py)

### `_satisfies`

Sprawdza, czy wśród zainstalowanych pakietów istnieje wersja spełniająca wymaganie.

### `_index_installed`

Buduje indeks zainstalowanych pakietów według znormalizowanej nazwy. Wykrywa również podwójne zainstalowanie pakietu.

### `_find_version`

Szuka konkretnej wersji w repozytorium, porównując ją przez `version_key`.

### `_check_dependencies`

Sprawdza wszystkie zależności wybranej wersji.

### `_check_conflicts`

Sprawdza wszystkie konflikty wybranej wersji.

### `verify_state`

Łączy wszystkie sprawdzenia i zwraca listę błędów. Pusta lista oznacza poprawny stan.

### Gotowa wypowiedź

> Weryfikator nie używa Z3. Jest niezależnym sprawdzeniem wyniku solvera. Dzięki temu nie zakładamy, że solver lub nasze kodowanie zawsze są poprawne. Każdy zwrócony stan przechodzi przez ten drugi mechanizm.

## 9. Eksperymenty — `experiments.py`, próg 4.5

Plik: [`package_manager/experiments.py`](package_manager/experiments.py)

### `run_case`

Dla jednego rozmiaru repozytorium:

1. wczytuje repozytorium,
2. wczytuje żądania,
3. buduje bazę wiedzy,
4. mierzy czas budowy,
5. uruchamia solver,
6. mierzy czas rozwiązania,
7. weryfikuje wynik,
8. zwraca słownik z wynikami.

Zapisywane są między innymi:

- liczba wersji,
- liczba aksjomatów,
- liczba ostrzeżeń,
- wynik,
- liczba pakietów,
- wartości kryteriów,
- czas budowy,
- czas rozwiązania.

### `write_outputs`

Zapisuje wyniki do CSV oraz tabeli Markdown.

### `main`

Obsługuje argumenty wiersza poleceń i uruchamia pomiary dla:

```text
10, 30, 100, 300, 1000
```

### Gotowa wypowiedź

> Eksperyment nie zmienia logiki instalacji. Mierzy, jak liczba zmiennych i aksjomatów oraz czas działania rosną wraz z rozmiarem repozytorium.

---

# CZĘŚĆ II — OSOBA 2

## 1. Przejście od progu 4 do progu 6

### Gotowa wypowiedź

> W progu 4 instalowaliśmy pakiety do pustego środowiska. W progu 6 pojawia się stan początkowy. Nie możemy już patrzeć tylko na to, czy końcowy stan spełnia żądanie. Musimy dodatkowo ograniczać liczbę zmian: nie usuwać pakietów bez potrzeby, nie zmieniać ich wersji bez potrzeby i uwzględniać pakiety ręczne.

> Aksjomaty A1–A3 pozostają bez zmian. Zmienia się natomiast sposób opisania stanu początkowego oraz lista kryteriów.

## 2. Wspólny szkielet — `solving.py`

Plik: [`package_manager/solving.py`](package_manager/solving.py)

### `total`

Sumuje wyrażenia arytmetyczne, a dla pustej kolekcji zwraca zero.

### Klasa `Encoding`

Przechowuje:

- repozytorium,
- bazę wiedzy,
- stan początkowy,
- rangi przestarzałości,
- wyrażenia `installed`, `removed`, `changed`, `new`.

### `count`

Liczy, ile flag logicznych jest prawdziwych:

```text
If(flag, 1, 0)
```

### `staleness`

Sumuje rangi przestarzałości zainstalowanych wersji dla wskazanych pakietów.
W `encode` słownik `rank` jest tworzony tak samo jak w instalacji do pustego
środowiska:

```python
for position, version in enumerate(
    sorted(versions, key=version_key, reverse=True)
):
    rank[package, version] = position
```

Metoda `staleness` korzysta następnie z tego słownika:

```python
z3.If(self.kb.variables[p, v], self.rank[p, v], 0)
```

Oznacza to, że w progu 6 mechanizm liczenia przestarzałości jest dokładnie
spójny z progiem 4. Różnica polega na tym, że w progu 6 wybieramy tylko te
grupy pakietów, które odpowiadają konkretnemu kryterium.

Przykładowo w `install_with_state`:

```python
enc.staleness(sorted((requested - old) & known))
```

liczy przestarzałość tylko tych żądanych pakietów, które:

- są żądane teraz,
- nie były wcześniej zainstalowane,
- istnieją w repozytorium.

Natomiast:

```python
enc.staleness(sorted(known - old - requested))
```

liczy przestarzałość pozostałych nowych pakietów, czyli zależności, które
pojawiły się podczas instalacji.

### Gotowa wypowiedź

> W progu 6 wykorzystujemy ten sam sposób obliczania rangi, ale stosujemy go
> bardziej selektywnie. Osobno liczymy przestarzałość nowych pakietów
> żądanych przez użytkownika i osobno przestarzałość pozostałych nowych
> pakietów. Dzięki temu kryteria dokładnie odzwierciedlają priorytet: najpierw
> jakość wersji żądanych, później liczba nowych pakietów, a na końcu jakość
> zależności.

### `encode`

Najpierw sprawdza stan początkowy przez `verify_state`.

Następnie tworzy:

#### `installed[p]`

Dowolna wersja pakietu `p` jest zainstalowana.

#### `removed[p]`

Pakiet był w stanie początkowym, ale nie ma go w stanie końcowym.

#### `changed[p]`

Pakiet pozostał zainstalowany, ale zmienił wersję.

#### `new[p]`

Pakiet nie był w stanie początkowym, a pojawił się w stanie końcowym.

### `solve_lex`

Wspólny mechanizm:

1. dodaje aksjomaty,
2. dodaje twarde ograniczenia,
3. dodaje cele,
4. minimalizuje cele leksykograficznie,
5. zwraca model i wartości kryteriów.

### `read_state`

Odczytuje z modelu końcowy stan. Pakiet żądany przez użytkownika albo wcześniej oznaczony jako ręczny pozostaje ręczny.

### Gotowa wypowiedź

> `solving.py` oddziela wspólny mechanizm od szczegółów konkretnej operacji. Dzięki temu instalacja i usuwanie korzystają z tych samych aksjomatów, tego samego kodowania i tej samej weryfikacji. W `operations.py` zmieniają się głównie ograniczenia oraz kolejność kryteriów.

## 3. Instalacja do istniejącego stanu — `operations.py`, próg 6.1

Plik: [`package_manager/operations.py`](package_manager/operations.py)

### `install_with_state`

Funkcja:

1. buduje lub otrzymuje bazę wiedzy,
2. koduje stan początkowy przez `encode`,
3. tworzy twarde ograniczenia dla żądań,
4. definiuje pięć kryteriów,
5. wywołuje `solve_lex`,
6. przekazuje wynik do `_finish`.

### Kryteria instalacji do istniejącego stanu

Kolejność:

1. liczba usuniętych pakietów,
2. liczba zmienionych wersji pakietów, które pozostają,
3. przestarzałość żądanych pakietów, które nie były wcześniej zainstalowane,
4. liczba nowych pakietów,
5. przestarzałość pozostałych nowych pakietów.

Interpretacja:

> Najpierw chronimy istniejące środowisko. Program minimalizuje usunięcia, potem zmiany wersji. Dopiero gdy te wartości są optymalne, wybiera nowsze wersje i ogranicza liczbę nowych zależności.

### Związek z progiem 4

Dla pustego stanu:

- kryterium usunięć jest równe zero,
- kryterium zmian wersji jest równe zero.

Pozostałe kryteria odpowiadają:

1. przestarzałości żądanych pakietów,
2. liczbie pakietów,
3. przestarzałości pozostałych pakietów.

Oznacza to, że implementacja progu 6 zachowuje zgodność z instalacją z progu 4.

## 4. Plan zmian i zapis stanu — `plan.py`

Plik: [`package_manager/plan.py`](package_manager/plan.py)

### Klasa `Change`

Opisuje zmianę:

- `install`,
- `remove`,
- `upgrade`,
- `downgrade`.

### `__str__`

Zamienia zmianę na czytelny komunikat po polsku, na przykład:

```text
podniesienie app 1.0 -> 2.0
```

### `diff_states`

Porównuje stan stary i nowy. Wersje porównuje przez `version_key`, więc `1.0` i `1.0.0` nie są uznawane za zmianę.

### `save_state`

Zapisuje stan do pliku:

```text
NAZWA WERSJA
NAZWA WERSJA manual
```

### Gotowa wypowiedź

> Solver zwraca stan, ale użytkownik potrzebuje informacji, co konkretnie się wydarzyło. `plan.py` tłumaczy różnicę między stanami na instalacje, usunięcia oraz podniesienia i obniżenia wersji.

## 5. Usuwanie i autoremove — `operations.py`, próg 6.2

### `remove_packages`

Funkcja:

1. buduje bazę wiedzy,
2. koduje stan początkowy,
3. tworzy twarde warunki, że wskazane pakiety nie mogą pozostać,
4. tworzy kryteria usuwania,
5. uruchamia `solve_lex`,
6. kończy przez `_finish`.

### Twarde ograniczenie

Dla każdego pakietu z listy `P` dodawane jest:

```text
not installed[p]
```

Czyli wskazany pakiet musi zniknąć ze stanu końcowego.

### Kryteria usuwania

1. minimalizacja usuniętych ręcznych pakietów spoza listy,
2. minimalizacja zmian wersji,
3. minimalizacja nowych pakietów,
4. minimalizacja usuniętych pakietów.

Przy `autoremove` ostatnie kryterium działa inaczej i preferuje usunięcie wszystkich niepotrzebnych pakietów.

### Różnica między zwykłym usuwaniem i `autoremove`

Bez `autoremove`:

> Usuwamy wskazany pakiet, ale nie musimy usuwać zależności, które stały się zbędne.

Z `autoremove`:

> Solver może usunąć również pakiety zainstalowane automatycznie, jeżeli nie są już potrzebne.

## 6. `_finish` i `OperationResult`

### `_finish`

Wspólne zakończenie operacji:

1. obsługa braku rozwiązania,
2. odczyt modelu,
3. utworzenie nowego stanu,
4. niezależna weryfikacja,
5. wyliczenie zmian przez `diff_states`,
6. utworzenie wyniku.

### `OperationResult`

Przechowuje:

- `state`,
- `changes`,
- `costs`.

### Gotowa wypowiedź

> Dzięki `_finish` instalacja i usuwanie kończą się w ten sam sposób. Nie powielamy kodu odczytu modelu, weryfikacji i tworzenia planu zmian.

## 7. Wyjaśnianie braku rozwiązania — `explanations.py`, próg 6.3

Plik: [`package_manager/explanations.py`](package_manager/explanations.py)

### `explain`

Funkcja otrzymuje bazę wiedzy oraz dodatkowe formuły. Każdą formułę opakowuje zmienną-strażnikiem:

```text
guard -> formula
```

Następnie zakłada wszystkie strażniki. Jeśli solver zwróci `unsat`, pobierany jest rdzeń sprzeczności.

### Minimalizacja rdzenia

Sam `unsat_core` nie musi być minimalny. Dlatego kod:

1. bierze element z rdzenia,
2. tymczasowo go usuwa,
3. ponownie sprawdza sprzeczność,
4. pozostawia element tylko wtedy, gdy jest potrzebny.

Wynikiem są czytelne etykiety, np.:

```text
app==2.0 wymaga lib >=2.0
żądanie użytkownika: app==2.0
```

### `explain_requests`

Jest wygodnym interfejsem dla samych żądań użytkownika. Buduje bazę wiedzy, zamienia żądania na formuły i wywołuje `explain`.

### Gotowa wypowiedź

> Moduł wyjaśnień odpowiada nie tylko na pytanie, czy rozwiązanie istnieje, ale również dlaczego go nie ma. Dzięki etykietom aksjomatów użytkownik otrzymuje opis przyczyny, a nie tylko techniczny komunikat `unsat`.

## 8. Scenariusz — `scenario.py`, próg 6.4

Plik: [`package_manager/scenario.py`](package_manager/scenario.py)

### `main`

Uruchamia powtarzalny scenariusz operacji na większym repozytorium.

Scenariusz:

1. rozpoczyna od pustego lub przygotowanego stanu,
2. wykonuje pierwsze instalacje,
3. następnie losuje instalacje i usuwanie,
4. czasami używa `autoremove`,
5. po każdym kroku weryfikuje stan,
6. zapisuje liczbę zmian, pakietów, pakietów ręcznych i czas.

Używane ziarno `2026` zapewnia powtarzalność.

### Gotowa wypowiedź

> Scenariusz sprawdza nie tylko pojedynczą operację, ale całą sekwencję zmian. Ustalone ziarno losowania pozwala uzyskać te same operacje przy każdym uruchomieniu i porównywać wyniki.

## 9. Interfejs programu — `__main__.py`

Plik: [`package_manager/__main__.py`](package_manager/__main__.py)

### `main`

Obsługuje polecenia:

- `install`,
- `remove`,
- `update`,
- `explain`.

Przyjmuje opcje:

- `--state`,
- `--output`,
- `--autoremove`.

Wczytuje repozytorium i odpowiedni plik wejściowy, a następnie uruchamia właściwą operację.

### `_show`

Wyświetla:

- plan zmian,
- stan końcowy,
- wartości kryteriów,
- potwierdzenie niezależnej weryfikacji.

Obsługuje również sytuację braku rozwiązania.

### Obsługa błędów

`main` przechwytuje błędy typu:

- `ValueError`,
- `RuntimeError`,
- `OSError`.

Następnie wypisuje czytelny komunikat na standardowe wyjście błędów i zwraca kod zakończenia.

## 10. `__init__.py`

Plik: [`package_manager/__init__.py`](package_manager/__init__.py)

Jest technicznym plikiem pakietu Pythona. Dzięki niemu katalog `package_manager` może być używany jako pakiet, na przykład przez:

```powershell
python -m package_manager
```

Nie zawiera głównej logiki solvera.

---

# Wspólne podsumowanie prezentacji

## Gotowa wypowiedź końcowa

> W projekcie oddzieliliśmy trzy poziomy działania. Najpierw walidujemy dane i budujemy modele. Następnie tworzymy bazę wiedzy z trzema rodzajami aksjomatów: A1 odpowiada za najwyżej jedną wersję, A2 za zależności, a A3 za konflikty. Później dodajemy żądania użytkownika jako twarde ograniczenia i wybieramy najlepszy poprawny stan według kryteriów optymalizacji.

> W progu 4 instalujemy pakiety do pustego środowiska. Kryteria dotyczą najnowszych wersji i liczby pakietów. W progu 6 korzystamy ze stanu początkowego. Wtedy najważniejsze jest ograniczenie liczby zmian, a dopiero później wybór nowych wersji i zależności.

> Wspólny mechanizm znajduje się w `solving.py`, operacje w `operations.py`, a wynik jest przekształcany na plan zmian przez `plan.py`. Każdy wynik przechodzi niezależną weryfikację, a w przypadku sprzeczności możemy wygenerować minimalne wyjaśnienie przez `explanations.py`.

## Najważniejsze pytania, które mogą paść

### Dlaczego potrzebujemy aksjomatów?

> Aksjomaty opisują zasady poprawności repozytorium. Bez nich solver mógłby wybrać jednocześnie dwie wersje pakietu, pominąć zależność albo zaakceptować konflikt.

### Czym aksjomat różni się od kryterium?

> Aksjomat odrzuca niedozwolone rozwiązania. Kryterium porównuje rozwiązania, które już są poprawne.

### Dlaczego kryteria są leksykograficzne?

> Ponieważ wymagania mają hierarchię. Na przykład zachowanie istniejących pakietów jest ważniejsze niż wybór najnowszej wersji zależności.

### Co zmienia próg 6?

> Pojawia się stan początkowy. Musimy wykrywać usunięcia, zmiany wersji i nowe pakiety, a także optymalizować liczbę modyfikacji.

### Dlaczego jest osobny weryfikator?

> Żeby niezależnie sprawdzić wynik solvera bez używania tego samego kodowania logicznego.

### Co dzieje się, gdy nie ma rozwiązania?

> Zwykła instalacja zwraca brak rozwiązania. Polecenie `explain` może dodatkowo wskazać minimalny zestaw żądań i aksjomatów powodujący sprzeczność.

---

# Krótka mapa wszystkich plików

| Plik | Odpowiedzialność | Osoba |
|---|---|---|
| `models.py` | Modele repozytorium, wymagań i stanu | 1 |
| `versions.py` | Porównywanie wersji | 1 |
| `requirements_parser.py` | Parsowanie i normalizacja wymagań | 1 |
| `json_reader.py` | Bezpieczne czytanie JSON-a | 1 |
| `loaders.py` | Wczytywanie i walidacja danych | 1 |
| `knowledge_base.py` | Zmienne logiczne i aksjomaty A1–A3 | 1 |
| `installer.py` | Instalacja do pustego środowiska | 1 |
| `verification.py` | Niezależna weryfikacja stanu | 1 |
| `experiments.py` | Pomiary dla różnych rozmiarów repozytorium | 1 |
| `solving.py` | Wspólny szkielet kodowania i optymalizacji | 2 |
| `operations.py` | Instalacja do stanu, usuwanie, autoremove | 2 |
| `plan.py` | Różnice między stanami i zapis stanu | 2 |
| `explanations.py` | Minimalny sprzeczny podzbiór | 2 |
| `scenario.py` | Powtarzalny scenariusz operacji | 2 |
| `__main__.py` | Interfejs wiersza poleceń | 2 |
| `__init__.py` | Definicja pakietu Pythona | 2 |

# Kolejność pokazania kodu na prezentacji

1. `models.py` — jakie dane przyjmujemy.
2. `requirements_parser.py` i `versions.py` — jak interpretujemy wymagania.
3. `knowledge_base.py` — jak powstają zmienne i aksjomaty.
4. `installer.py` — instalacja do pustego stanu.
5. `verification.py` — niezależna kontrola.
6. `solving.py` — przejście do pracy ze stanem początkowym.
7. `operations.py` — instalacja i usuwanie.
8. `plan.py` — opis zmian dla użytkownika.
9. `explanations.py` — wyjaśnienie sprzeczności.
10. `experiments.py`, `scenario.py`, `__main__.py` — pomiary, scenariusz i interfejs.
