# DFS krok po kroku

Otwórz `dfs-krok-po-kroku.html` w przeglądarce. Nie potrzeba serwera,
instalacji pakietów ani połączenia z internetem. Przy przenoszeniu wizualizacji
skopiuj zarówno plik HTML, jak i sąsiadujący folder `dfs-krok-po-kroku/`.

## Podział plików

| Plik | Odpowiedzialność |
| --- | --- |
| `dfs-krok-po-kroku.html` | Struktura strony, przyciski i panele. |
| `dfs-krok-po-kroku/styles.css` | Style, animacje, układ mobilny i ciemny motyw. |
| `dfs-krok-po-kroku/sources.js` | Czytelne kopie kodu Pythona wyświetlanego w panelu. |
| `dfs-krok-po-kroku/trace.js` | Stan przykładu i generowanie migawek przebiegu DFS. |
| `dfs-krok-po-kroku/view.js` | Rysowanie klocków, podświetlanie kodu i aktualizacja paneli. |
| `dfs-krok-po-kroku/app.js` | Krokowanie, odtwarzanie, zdarzenia i zapis pozycji. |

Skrypty są ładowane w kolejności zapisanej w HTML i współdzielą obiekt
`window.BlocksWorldDFS`. Zwykłe skrypty z `defer` pozwalają otwierać stronę
bezpośrednio z dysku, bez ograniczeń dotyczących modułów i pobierania plików
przez `fetch` dla adresów `file://`.

## Edycja kodu przykładu

`sources.js` przechowuje statyczne kopie Pythona, a nie odczytuje plików z `src/`.
Numery linii użyte w `trace.js` wskazują na te kopie. Przy zmianie ich treści
zaktualizuj również odpowiadające im numery linii w przebiegu.
