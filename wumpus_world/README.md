# Wumpus World game and visualizer

The interactive board uses `World.execute()` from `world.py`, the agent
from `agent.py`, and Clingo inference from `inference.py` and
`wumpus_kb.lp`. The browser renders the state supplied by a local Python
server.

## Running the game

Run the following commands from the repository root.

```powershell
py -3 -m venv wumpus_world/.venv
wumpus_world/.venv/Scripts/python.exe -m pip install -r wumpus_world/requirements.txt
wumpus_world/.venv/Scripts/python.exe wumpus_world/visualizer.py
```

Once the environment is set up, run the final command to start the game.
It opens at `http://127.0.0.1:8765`. Press **Ctrl+C** in the terminal to stop
the server. Open the game through the Python server so the page can access
the game state. The server is available only on your computer, and open
tabs share one game session.

Use `--no-browser` to suppress automatic browser launch, `--port 8766` to
choose a port, or `--port 0` to let the system choose an available port.

## Controls and features

- Play manually using **↑** to move forward, **← / →** to turn, **G** to
  grab, **F** to shoot, and **E** to exit. **Space** starts or pauses agent
  playback.
- Execute one agent action at a time or watch an animated run.
- Switch between **Wiedza agenta** (agent knowledge) and **Pełna mapa**
  (full map). The choice affects only the player's view.
- Click a cell to read its description. Movement uses the game controls.
- Inspect percepts, inferences, the current goal, the remaining plan, and ASP
  facts.
- Undo an action to restore the prior state, including the agent's
  knowledge, arrows, gold, and plan.
- Choose the AIMA board, the risk-comparison board, or a seeded random cave.
- Compare the cautious, risk-taking heuristic, and model-counting strategies.
  Select **Nowa wyprawa** (new expedition) to apply the board and strategy
  settings.

## Reading the board

The entrance `(1, 1)` is in the lower-left corner. The agent starts facing
east. A breeze indicates a pit in at least one orthogonally adjacent cell,
a stench indicates a Wumpus in an adjacent cell, and glitter indicates gold
in the current cell. A dead Wumpus continues to produce a stench in this
implementation.

A safe cell is safe in every model consistent with the observations. A
possible pit or Wumpus appears in at least one such model. The locations
of pits farther from the explored area remain unknown.

Each action costs 1 point, firing an arrow costs an additional 10, and death
costs 1,000. Each piece of gold earns 1,000 points once the agent exits the
cave at `(1, 1)`. An arrow travels in the facing direction until it reaches
a wall or hits the first living Wumpus. Exiting without gold also ends the
game. Some random boards have no winning route.

To learn the game, step through a few actions on the AIMA board, compare the
percepts with the marked safe cells, reveal the full map, and finish the
expedition. Then try each risk-taking strategy separately on the
risk-comparison board. Model counting accounts for differences in pit
probabilities.

## Tests and terminal simulation

```powershell
wumpus_world/.venv/Scripts/python.exe -m unittest discover -s wumpus_world -p "test_visualizer.py" -v
```

Run the AIMA simulation in the terminal with the following command.

```powershell
wumpus_world/.venv/Scripts/python.exe wumpus_world/simulate.py --aima
```
