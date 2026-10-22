(() => {
  'use strict';

  const {
    sources
  } = window.BlocksWorldDFS;
  // Stan przykładu i funkcje wspólne dla przebiegu oraz widoku.
  const start = [0, 1, 0, 2, 3],
    goal = [2, 3, 4, 5, 0];
  const key = state => state.join(' ');
  const tuple = value => value ? `(${value.join(', ')})` : '—';
  const same = (a, b) => key(a) === key(b);
  const range = (first, last = first) => Array.from({
    length: last - first + 1
  }, (_, i) => first + i);
  const frame = (name, file, line) => ({
    name,
    file,
    line
  });
  const mainLine = sources['main.py'].split(/\r?\n/).findIndex(line => line.includes('result = solve_dfs(')) + 1;
  const mainFrame = frame('main()', 'main.py', mainLine);

  // Migawki zachowują kolejność wyszukiwania Pythona i dodawanie do visited przy odkryciu.
  function makeTrace() {
    let stack = [start.slice()],
      visited = new Set([key(start)]),
      parent = new Map(),
      expanded = 0;
    let state = null,
      moves = null,
      move = null,
      nextState = null,
      iteration = 0,
      plan = [],
      planState = null,
      planMove = null;
    const trace = [];
    const solverFrame = line => frame('solve_dfs()', 'dfs.py', line);
    function emit(action, detail, file, lines, options = {}) {
      trace.push({
        action,
        detail,
        file,
        lines,
        iteration,
        expanded,
        state: state?.slice() ?? null,
        stack: stack.map(s => s.slice()),
        visited: [...visited],
        parent: [...parent].map(([child, value]) => [child, {
          state: value.state.slice(),
          move: value.move.slice()
        }]),
        moves: moves?.map(m => m.slice()) ?? null,
        move: move?.slice() ?? null,
        nextState: nextState?.slice() ?? null,
        plan: plan.map(m => m.slice()),
        planState: planState?.slice() ?? null,
        planMove: planMove?.slice() ?? null,
        calls: options.calls ?? [mainFrame, solverFrame(lines[0])],
        scope: options.scope ?? 'solve_dfs()',
        locals: options.locals ?? [],
        candidate: options.candidate ?? false,
        candidateStatus: options.candidateStatus ?? '',
        changed: options.changed ?? [],
        checkpoint: options.checkpoint ?? false,
        building: options.building ?? false,
        done: options.done ?? false,
        movedBlock: options.movedBlock ?? null
      });
    }
    emit('Inicjalizacja', 'Stan startowy trafia na stack i do visited. parent jest pusty, expanded = 0.', 'dfs.py', range(25, 29), {
      changed: ['stack', 'visited', 'parent', 'expanded'],
      checkpoint: true
    });
    while (stack.length) {
      iteration++;
      emit('Początek iteracji', 'Stos nie jest pusty. Program sprawdza limit czasu i limit węzłów; dla tego przykładu oba pozwalają kontynuować.', 'dfs.py', [31, 32, 33, 35]);
      state = stack.pop();
      emit('Zdjęcie stanu ze stosu', `state = stack.pop() → ${key(state)}. Stos ma teraz ${stack.length} elementów.`, 'dfs.py', [38], {
        changed: ['state', 'stack'],
        movedBlock: parent.get(key(state))?.move[0]
      });
      const isGoal = same(state, goal);
      emit('Sprawdzenie celu', isGoal ? 'state == goal → True. Cel został zdjęty ze stosu; nie zwiększamy expanded.' : 'state == goal → False. Teraz rozwiną się następniki tego stanu.', 'dfs.py', [39]);
      if (isGoal) {
        const buildCalls = line => [mainFrame, solverFrame(41), frame('_build_plan()', 'dfs.py', line)];
        plan = [];
        planState = goal.slice();
        emit('Odtwarzanie planu', 'Wywołanie _build_plan(start, goal, parent). Cofamy się od celu po zapisanych poprzednikach.', 'dfs.py', [57, 58], {
          calls: buildCalls(58),
          scope: '_build_plan()',
          building: true
        });
        while (!same(planState, start)) {
          const child = key(planState),
            link = parent.get(child);
          planState = link.state.slice();
          planMove = link.move.slice();
          emit('Odczyt poprzednika', `parent[${child}] prowadzi do ${key(planState)} z ruchem ${tuple(planMove)}.`, 'dfs.py', [59, 60], {
            calls: buildCalls(60),
            scope: '_build_plan()',
            building: true
          });
          plan.push(planMove.slice());
          emit('Zapis ruchu od końca', `Dopisujemy ${tuple(planMove)} do lokalnego moves. Lista powstaje od celu do startu.`, 'dfs.py', [61], {
            calls: buildCalls(61),
            scope: '_build_plan()',
            building: true
          });
        }
        plan.reverse();
        emit('Odwrócenie planu', 'tuple(reversed(moves)) zwraca ruchy w kolejności wykonania: od startu do celu.', 'dfs.py', [62], {
          calls: buildCalls(62),
          scope: '_build_plan()',
          building: true
        });
        emit('Zwrócenie wyniku', `SearchResult: solved, ${plan.length} ruchów, ${expanded} rozwiniętych węzłów. Niewykorzystane stany pozostają na stosie.`, 'dfs.py', range(40, 42), {
          building: true
        });
        emit('Cel znaleziony', `main() odbiera result: ${plan.length} ruchów, expanded_nodes = ${expanded}. Wyszukiwanie jest zakończone.`, 'main.py', [mainLine], {
          calls: [mainFrame],
          scope: 'main()',
          locals: [['result.status', 'solved'], ['liczba ruchów', plan.length], ['expanded_nodes', expanded]],
          done: true,
          building: true,
          checkpoint: true
        });
        return trace;
      }
      expanded++;
      emit('Rozwinięcie węzła', `expanded += 1 → ${expanded}. Licznik rośnie tylko dla stanu, który nie jest celem.`, 'dfs.py', [43], {
        changed: ['expanded']
      });
      const settled = new Set();
      let changed = true;
      while (changed) {
        changed = false;
        state.forEach((support, index) => {
          const block = index + 1;
          if (!settled.has(block) && support === goal[index] && (support === 0 || settled.has(support))) {
            settled.add(block);
            changed = true;
          }
        });
      }
      const orderedCalls = line => [mainFrame, solverFrame(45), frame('_ordered_moves()', 'dfs.py', line)];
      const settledText = settled.size ? `{${[...settled].join(', ')}}` : 'set()';
      emit('Ustalenie poprawnie ułożonych klocków', `settled = ${settledText}. Klocek musi leżeć na docelowym, również ustalonym podłożu.`, 'dfs.py', range(67, 79), {
        calls: orderedCalls(69),
        scope: '_ordered_moves()',
        locals: [['settled', settledText], ['changed', 'False']]
      });
      const clear = state.map((_, i) => i + 1).filter(block => !state.includes(block)),
        legal = [];
      const legalCalls = line => [...orderedCalls(93), frame('legal_moves()', 'state.py', line)];
      emit('Znalezienie wolnych klocków', `clear_blocks() → {${clear.join(', ')}}. Na tych klockach nic nie stoi.`, 'state.py', [24, 25], {
        calls: [...legalCalls(28), frame('clear_blocks()', 'state.py', 25)],
        scope: 'clear_blocks()',
        locals: [['wolne klocki', `{${clear.join(', ')}}`]]
      });
      clear.forEach(block => {
        if (state[block - 1] !== 0) legal.push([block, 0]);else clear.filter(target => target !== block).forEach(target => legal.push([block, target]));
      });
      emit('Wygenerowanie legalnych ruchów', `${legal.length} ruchów. Z wieży zdejmujemy wolny klocek na stół; ze stołu można położyć go na innym wolnym klocku.`, 'state.py', range(28, 35), {
        calls: legalCalls(35),
        scope: 'legal_moves()',
        locals: [['clear', `[${clear.join(', ')}]`], ['moves', legal.map(tuple).join(', ')]]
      });
      const ranked = legal.map(candidate => {
        const [block, target] = candidate,
          reachesGoal = target === goal[block - 1],
          targetReady = target === 0 || settled.has(target);
        const rank = reachesGoal && targetReady && !settled.has(block) ? 0 : target === 0 && !settled.has(block) ? 1 : !settled.has(block) ? 2 : 3;
        const returnLine = [86, 88, 90, 91][rank];
        emit('Ocena priorytetu ruchu', `priority(${tuple(candidate)}) → (${rank}, ${block}, ${target}). Mniejszy priorytet oznacza wcześniejsze rozpatrzenie.`, 'dfs.py', [82, 83, 84, 85, ...(rank > 0 ? [87] : []), ...(rank > 1 ? [89] : []), returnLine], {
          calls: [...orderedCalls(93), frame('priority()', 'dfs.py', returnLine)],
          scope: 'priority()',
          locals: [['move', tuple(candidate)], ['reaches_goal', reachesGoal ? 'True' : 'False'], ['target_ready', targetReady ? 'True' : 'False'], ['priorytet', `(${rank}, ${block}, ${target})`]]
        });
        return {
          move: candidate,
          rank
        };
      });
      ranked.sort((a, b) => a.rank - b.rank || a.move[0] - b.move[0] || a.move[1] - b.move[1]);
      const ordered = ranked.map(item => item.move);
      emit('Posortowanie ruchów', `sorted(..., key=priority) → ${ordered.map(tuple).join(', ')}.`, 'dfs.py', [93], {
        calls: orderedCalls(93),
        scope: '_ordered_moves()',
        locals: [['wynik', ordered.map(tuple).join(', ')]]
      });
      moves = ordered;
      emit('Powrót do solve_dfs', 'moves otrzymuje posortowaną listę. reversed(moves) sprawi, że najlepszy następnik trafi na wierzchołek stosu.', 'dfs.py', [45], {
        changed: ['moves']
      });
      for (const candidate of moves.slice().reverse()) {
        move = candidate.slice();
        emit('Kolejny ruch w odwróconej kolejności', `move = ${tuple(move)}. Słabsze ruchy dodajemy najpierw, ponieważ stos działa według LIFO.`, 'dfs.py', [46], {
          changed: ['move']
        });
        const applyCalls = line => [mainFrame, solverFrame(47), frame('apply()', 'state.py', line)];
        emit('Zastosowanie ruchu', `apply(${tuple(move)}) sprawdza poprawność ruchu. Oryginalny state pozostaje bez zmian.`, 'state.py', [38, 39, 41, 43, 45, 48, ...(move[1] === 0 ? [49] : [52, 56])], {
          calls: applyCalls(38),
          scope: 'apply()',
          locals: [['block', move[0]], ['target', move[1]], ['current_support', state[move[0] - 1]]]
        });
        const successor = state.slice();
        successor[move[0] - 1] = move[1];
        emit('Utworzenie nowego układu', `Kopia supports otrzymuje supports[${move[0] - 1}] = ${move[1]}. apply() zwraca nowy BlockWorldState.`, 'state.py', [59, 60, 61], {
          calls: applyCalls(61),
          scope: 'apply()',
          locals: [['supports', `[${successor.join(', ')}]`]]
        });
        nextState = successor;
        emit('Powrót z apply', `next_state = ${key(nextState)}. To kandydat; state nadal wynosi ${key(state)}.`, 'dfs.py', [47], {
          candidate: true,
          changed: ['next_state']
        });
        const isNew = !visited.has(key(nextState));
        emit('Sprawdzenie visited', isNew ? 'next_state not in visited → True. Ten stan nie został jeszcze odkryty.' : 'next_state not in visited → False. Pomijamy już odkryty stan; nie trafi ponownie na stos.', 'dfs.py', [48], {
          candidate: true,
          candidateStatus: isNew ? 'Nowy stan' : 'Już w visited · pomijamy'
        });
        if (isNew) {
          visited.add(key(nextState));
          emit('Oznaczenie stanu jako odkrytego', `visited.add(next_state). len(visited) = ${visited.size}; stan oznaczamy już przed jego rozwinięciem.`, 'dfs.py', [49], {
            candidate: true,
            changed: ['visited']
          });
          parent.set(key(nextState), {
            state: state.slice(),
            move: move.slice()
          });
          emit('Zapis poprzednika', `parent[${key(nextState)}] = (${key(state)}, ${tuple(move)}). Ta relacja posłuży do odtworzenia planu.`, 'dfs.py', [50], {
            candidate: true,
            changed: ['parent']
          });
          stack.push(nextState.slice());
          emit('Dodanie na stos DFS', `${key(nextState)} trafia na wierzchołek. stack ma ${stack.length} elementów.`, 'dfs.py', [51], {
            candidate: true,
            candidateStatus: 'Dodany na stos',
            changed: ['stack']
          });
        }
      }
      emit('Koniec iteracji ' + iteration, `Rozwinięto stan ${key(state)}. expanded = ${expanded}, len(visited) = ${visited.size}, len(stack) = ${stack.length}. Następne pop() wybierze wierzchołek stosu.`, 'dfs.py', [46], {
        checkpoint: true
      });
      if (iteration > 1000) throw new Error('Przekroczono limit wizualizacji.');
    }
    throw new Error('Przykład nie dotarł do celu.');
  }
  Object.assign(window.BlocksWorldDFS, {
    start,
    goal,
    key,
    tuple,
    makeTrace
  });
})();
