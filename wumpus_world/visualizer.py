"""Lokalna gra edukacyjna. Uruchom: python visualizer.py (lub dodaj --no-browser)."""

from __future__ import annotations

import argparse
import copy
import json
import random
import threading
import webbrowser
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from agent import Agent
from world import AIMA_WORLD, COUNTING_WORLD, START, Action, World, generate_world, ray

STATIC = Path(__file__).with_name("visualizer")
ACTION_NAMES = {
    "left": "Obrót w lewo", "right": "Obrót w prawo", "forward": "Krok naprzód",
    "grab": "Podniesienie złota", "shoot": "Strzał", "climb": "Wyjście z jaskini",
}


class Game:
    """Łączy prawdziwe środowisko, agenta i historię; interfejs nie ustala reguł."""

    def __init__(self, scenario: str = "aima", strategy: str = "safe", seed: int = 7):
        if scenario not in {"aima", "counting", "random"}:
            raise ValueError("Nieznana plansza.")
        if strategy not in {"safe", "risky", "counting"}:
            raise ValueError("Nieznana strategia.")
        self.scenario, self.strategy, self.seed = scenario, strategy, seed
        config = {"aima": AIMA_WORLD, "counting": COUNTING_WORLD}.get(scenario)
        self.world = World(config or generate_world(rng=random.Random(seed)))
        self.agent = Agent(self.world.width, self.world.height, n_wumpus=len(self.world.config.wumpuses),
                           n_gold=len(self.world.config.gold), n_arrows=self.world.arrows,
                           risky=strategy == "risky", counting=strategy == "counting")
        self.percept = self.world.percept()
        self.history: list[tuple] = []
        self.events: list[dict] = []
        self.effect = None
        self.message = "Wejście do jaskini. Zbierz złoto i wróć na (1, 1), aby je wynieść."
        self._observe()

    def _observe(self):
        # Śmiertelnego pola nie wolno dopisać jako odwiedzonego i bezpiecznego.
        if self.world.alive:
            self.agent.kb.tell_percept(self.world.pos, self.percept.breeze, self.percept.stench)
            self.agent.last_inference = self.agent.kb.infer()
        # Ręczne puste GRAB/SHOOT również muszą zgadzać się z World.execute.
        self.agent.pos, self.agent.direction = self.world.pos, self.world.direction
        self.agent.arrows = self.world.arrows
        self.agent.gold_carried = self.world.gold_carried
        self.agent.last_action = None  # strzał zapisujemy raz, bezpośrednio po wykonaniu

    def act(self, action: str):
        if self.world.done:
            raise ValueError("Gra jest zakończona. Cofnij ruch lub rozpocznij nową grę.")
        if self.world.actions_taken >= 500:
            raise ValueError("Limit 500 akcji. Cofnij ruch lub rozpocznij nową grę.")
        if action != "agent":
            try:
                chosen = Action(action)
            except ValueError:
                raise ValueError("Nieznana akcja.") from None
        self.history.append(copy.deepcopy((self.world, self.agent, self.percept,
                                           self.events, self.effect, self.message)))
        if action == "agent":
            chosen = self.agent.act(self.percept)
        else:
            self.agent.plan.clear()
            self.agent.goal = "Sterowanie ręczne"
        origin, direction = self.world.pos, self.world.direction
        arrows_before, gold_before = self.world.arrows, self.world.gold_carried
        path = ray(origin, direction, self.world.width, self.world.height)
        if chosen is Action.SHOOT:
            for i, cell in enumerate(path):
                if cell in self.world.live_wumpuses:
                    path = path[:i + 1]
                    break
        self.percept = self.world.execute(chosen)
        fired = self.world.arrows < arrows_before
        if fired:
            self.agent.kb.tell_shot(origin, direction, self.percept.scream)
            self.agent.plan.clear()
        self._observe()
        self.effect = {"action": chosen.value, "origin": origin, "direction": direction.value,
                       "path": path if fired else [], "fired": fired}
        message = ACTION_NAMES[chosen.value] + ". "
        if not self.world.alive:
            message += "Koniec wyprawy: " + ("wpadłeś do jamy." if self.world.pos in self.world.config.pits else "spotkałeś żywego Wumpusa.")
        elif self.world.climbed:
            message += f"Wyprawa zakończona. Wyniesione złoto: {self.world.gold_carried}."
        elif self.percept.bump:
            message += "Ściana! Pozycja pozostaje bez zmian."
        elif chosen is Action.SHOOT:
            message += "Krzyk! Wumpus został zabity." if self.percept.scream else ("Brak krzyku: na torze strzały nie było żywego Wumpusa." if fired else "Nie masz już strzał.")
        elif chosen is Action.GRAB:
            message += "Masz złoto! Teraz wróć do wejścia." if self.world.gold_carried > gold_before else "Na tym polu nie ma złota."
        elif chosen is Action.CLIMB:
            message += "Wyjście jest dostępne tylko na polu (1, 1)."
        else:
            message += f"Pozycja ({self.world.pos[0]}, {self.world.pos[1]}). "
            message += "Poczuj otoczenie i sprawdź, co wynika z obserwacji."
        self.message = message
        self.events.append({"step": self.world.actions_taken, "action": chosen.value,
                            "message": message, "pos": self.world.pos})
        return self.state()

    def undo(self):
        if self.history:
            (self.world, self.agent, self.percept, self.events,
             self.effect, self.message) = self.history.pop()
            self.effect = None
        return self.state()

    def state(self):
        w, kb, inf = self.world, self.agent.kb, self.agent.last_inference
        cells = []
        for y in range(w.height, 0, -1):
            for x in range(1, w.width + 1):
                c = (x, y)
                cells.append({"x": x, "y": y, "visited": c in kb.visited,
                              "pit": c in w.config.pits, "wumpus": c in w.config.wumpuses,
                              "alive": c in w.live_wumpuses, "gold": c in w.gold_left,
                              "breeze": kb.breeze.get(c), "stench": kb.stench.get(c),
                              **{name: c in getattr(inf, name) for name in (
                                  "safe", "frontier", "pit_certain", "pit_possible",
                                  "alive_certain", "alive_possible", "dead_certain")}})
        goal = self.agent.goal
        for prefix, label in (("explore ", "Eksploracja bezpiecznego pola "),
                              ("shoot ", "Zabezpieczenie pola strzałą "),
                              ("risk counting ", "Ryzyko wg zliczania modeli "),
                              ("risk ", "Ryzykowny krok ")):
            if goal.startswith(prefix):
                goal = label + goal[len(prefix):]
                break
        goal = {"start": "Poznaj otoczenie wejścia", "bring the gold home": "Powrót ze złotem do wejścia",
                "nothing safe left, leave the cave": "Brak bezpiecznej drogi — powrót do wejścia"}.get(goal, goal)
        return {"cells": cells, "width": w.width, "height": w.height, "pos": w.pos,
                "direction": w.direction.value, "alive": w.alive, "done": w.done,
                "climbed": w.climbed, "gold": w.gold_carried, "totalGold": len(w.config.gold),
                "arrows": w.arrows, "steps": w.actions_taken, "score": w.score(),
                "percept": asdict(self.percept), "goal": goal, "message": self.message,
                "plan": [a.value for a in self.agent.plan], "facts": kb.facts(),
                "events": self.events[-60:], "effect": self.effect,
                "trail": [START] + [e["pos"] for e in self.events if e["action"] == "forward"],
                "canUndo": bool(self.history), "scenario": self.scenario,
                "strategy": self.strategy, "seed": self.seed}


class Server(ThreadingHTTPServer):
    def __init__(self, address):
        super().__init__(address, Handler)
        self.game = Game()
        self.lock = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def reply(self, value, status=200):
        data = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/api/state":
            with self.server.lock:
                self.reply(self.server.game.state())
            return
        files = {"/": ("index.html", "text/html"), "/style.css": ("style.css", "text/css"),
                 "/app.js": ("app.js", "text/javascript")}
        if self.path not in files:
            self.send_error(404)
            return
        name, mime = files[self.path]
        data = (STATIC / name).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        # JSON + kontrola Origin chronią lokalny serwer przed żądaniami z innych stron.
        origin = self.headers.get("Origin")
        expected = f"http://127.0.0.1:{self.server.server_port}"
        if (origin and origin != expected) or self.headers.get_content_type() != "application/json":
            self.reply({"error": "Niedozwolone źródło żądania."}, 403)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4096:
                raise ValueError("Niepoprawny rozmiar żądania.")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("Oczekiwano obiektu JSON.")
            with self.server.lock:
                if self.path == "/api/new":
                    seed = int(payload.get("seed", 7))
                    self.server.game = Game(payload.get("scenario", "aima"), payload.get("strategy", "safe"), seed)
                    result = self.server.game.state()
                elif self.path == "/api/action":
                    result = self.server.game.act(payload.get("action", ""))
                elif self.path == "/api/undo":
                    result = self.server.game.undo()
                else:
                    self.reply({"error": "Nieznany adres."}, 404)
                    return
            self.reply(result)
        except (ValueError, TypeError) as exc:
            self.reply({"error": str(exc)}, 400)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765, help="0 wybiera wolny port")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    with Server(("127.0.0.1", args.port)) as server:
        url = f"http://127.0.0.1:{server.server_port}"
        print(f"Wumpus World: {url}\nZatrzymanie serwera: Ctrl+C", flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
