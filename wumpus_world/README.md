# Wumpus World — gra i wizualizacja

Interaktywna plansza korzysta bezpośrednio z `World.execute()` w `world.py`,
agenta z `agent.py` oraz rzeczywistego wnioskowania Clingo z `inference.py`
i `wumpus_kb.lp`. Przeglądarka rysuje stan przekazany przez lokalny serwer Pythona.

## Uruchomienie

W terminalu w głównym katalogu projektu:

```powershell
py -3 -m venv wumpus_world/.venv
wumpus_world/.venv/Scripts/python.exe -m pip install -r wumpus_world/requirements.txt
wumpus_world/.venv/Scripts/python.exe wumpus_world/visualizer.py
```

Jeśli środowisko jest już przygotowane, wystarczy ostatnie polecenie.
Gra otworzy się w przeglądarce pod `http://127.0.0.1:8765`.
Serwer zatrzymasz przez **Ctrl+C** w terminalu. Nie otwieraj samego `index.html`:
potrzebuje połączenia z Pythonem. Serwer jest dostępny tylko na tym komputerze;
otwarte karty współdzielą jedną wyprawę.

Opcje: `--no-browser` wyłącza automatyczne otwarcie przeglądarki,
`--port 8766` zmienia port, `--port 0` wybiera wolny port.

## Co można zrobić

- Grać ręcznie: **↑** krok naprzód, **← / →** obrót, **G** podnieś,
  **F** strzel, **E** wyjdź. **Spacja** uruchamia i zatrzymuje pokaz agenta.
- Wykonywać pojedyncze akcje agenta lub obserwować animowaną rozgrywkę.
- Przełączać **wiedzę agenta** i **pełną mapę**. Podgląd nie zmienia wiedzy agenta.
- Kliknąć pole, aby zobaczyć opis; kliknięcie nie przemieszcza postaci.
- Czytać percepcje, wnioski, aktualny cel, pozostały plan i fakty ASP.
- Cofać akcje wraz z wiedzą, strzałami, złotem i planem. Cofnięcie jest pomocą
  edukacyjną i przywraca stan sprzed akcji, nie jest akcją w regułach Wumpusa.
- Wybrać planszę AIMA, przykład porównania ryzyka albo losową jaskinię z ziarnem.
- Porównywać strategie ostrożną, heurystycznego ryzykanta i zliczanie modeli.
  Ustawienia planszy i strategii stosuje przycisk **Nowa wyprawa**.

## Jak czytać grę

Wejście `(1, 1)` jest w lewym dolnym rogu. Agent zaczyna zwrócony na wschód.
Powiew oznacza jamę na co najmniej jednym polu sąsiadującym krawędzią,
smród — Wumpusa na sąsiednim polu, a blask — złoto na bieżącym polu.
Martwy Wumpus nadal śmierdzi, zgodnie z implementacją projektu.

Pola bezpieczne są bezpieczne we wszystkich modelach zgodnych z obserwacjami.
„Możliwa jama / Wumpus” oznacza, że zagrożenie występuje w przynajmniej jednym
takim modelu; nie jest to potwierdzenie jego obecności. Dalej od odwiedzonego
obszaru położenie jam pozostaje nieznane.

Każda akcja kosztuje 1 punkt, oddana strzała dodatkowo 10. Śmierć kosztuje 1000,
a każda sztuka złota daje 1000 dopiero po wyjściu z jaskini na `(1, 1)`.
Strzała leci w kierunku patrzenia do ściany i zatrzymuje się na pierwszym żywym
Wumpusie. Wyjście bez złota też kończy grę. Losowa plansza nie musi być wygrywalna.

Proponowana nauka: wykonaj kilka kroków agenta na planszy AIMA, porównaj
percepcje z bezpiecznymi polami, włącz pełną mapę, a potem dokończ wyprawę.
Na planszy porównania ryzyka uruchom osobno obie strategie ryzykowne:
zliczanie modeli uwzględnia różne prawdopodobieństwa jam.

## Testy

```powershell
wumpus_world/.venv/Scripts/python.exe -m unittest discover -s wumpus_world -p "test_visualizer.py" -v
```

Dotychczasowa symulacja terminalowa pozostaje dostępna:

```powershell
wumpus_world/.venv/Scripts/python.exe wumpus_world/simulate.py --aima
```
