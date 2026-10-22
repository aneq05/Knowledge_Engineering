(() => {
  'use strict';

  const {
    sources,
    start,
    key,
    tuple
  } = window.BlocksWorldDFS;
  const escape = value => String(value).replace(/[&<>"']/g, char => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  })[char]);

  // Widok otrzymuje migawkę; nie zmienia pozycji odtwarzania ani przebiegu DFS.
  function createView(root) {
    const query = selector => root.querySelector(selector);
    let displayedFile = null;
    // Rysowanie klocków i podgląd kodu Pythona.
    const blockColor = block => `var(--bw-block-${block})`;
    query('[data-legend]').innerHTML = start.map((_, i) => `<span><i class="bw-swatch" style="background:${blockColor(i + 1)}" aria-hidden="true"></i>Klocek ${i + 1}</span>`).join('');
    function drawWorld(svg, current, preview = false, movedBlock = null) {
      const width = Math.max(120, svg.getBoundingClientRect().width),
        height = preview ? 150 : parseFloat(getComputedStyle(svg).height);
      svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
      const towers = [];
      current.forEach((support, index) => {
        if (support !== 0) return;
        const tower = [index + 1];
        let upper;
        while (upper = current.indexOf(tower[tower.length - 1]) + 1) tower.push(upper);
        towers.push(tower);
      });
      const slot = (width - 16) / towers.length,
        blockWidth = Math.min(preview ? 39 : 70, slot - 9),
        blockHeight = preview ? 20 : 36,
        pitch = preview ? 23 : 40,
        baseline = height - 27;
      let markup = `<title>${preview ? 'Kandydat' : 'Rozpatrywany układ'}: ${key(current)}</title><desc>${current.map((support, i) => `Klocek ${i + 1} ${support === 0 ? 'na stole' : `na klocku ${support}`}`).join('. ')}.</desc><line x1="5" y1="${baseline}" x2="${width - 5}" y2="${baseline}" stroke="var(--bw-line)" stroke-width="2"/>`;
      towers.forEach((tower, towerIndex) => {
        const x = 8 + slot * (towerIndex + .5);
        tower.forEach((block, level) => {
          const y = baseline - 5 - blockHeight - level * pitch;
          markup += `<g${block === movedBlock ? ' class="bw-moved"' : ''}><rect class="bw-block-rect" x="${x - blockWidth / 2}" y="${y}" width="${blockWidth}" height="${blockHeight}" rx="5" fill="${blockColor(block)}"/><text class="bw-block-label" x="${x}" y="${y + blockHeight / 2}" dy=".35em" text-anchor="middle" font-size="${preview ? 12 : 17}">${block}</text></g>`;
        });
      });
      svg.innerHTML = markup + `<text x="${width - 6}" y="${height - 7}" text-anchor="end" font-size="11">stół · 0</text>`;
    }
    function highlight(line) {
      return line.split(/("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|#.*$|\b(?:def|class|return|if|else|for|in|not|and|or|while|from|import|True|False|None|try|except|raise)\b)/g).map(token => {
        const css = /^#/.test(token) ? 'bw-comment' : /^['"]/.test(token) ? 'bw-string' : /^(def|class|return|if|else|for|in|not|and|or|while|from|import|True|False|None|try|except|raise)$/.test(token) ? 'bw-keyword' : '';
        return css ? `<span class="${css}">${escape(token)}</span>` : escape(token);
      }).join('');
    }
    function renderCode(item, manual = null) {
      const view = manual ?? {
        file: item.file,
        lines: item.lines,
        name: item.scope
      };
      if (displayedFile !== view.file) {
        query('[data-code]').innerHTML = sources[view.file].split(/\r?\n/).map((line, i) => `<span class="bw-code-line" data-line="${i + 1}"><span class="bw-line-number" aria-hidden="true">${i + 1}</span><span class="bw-line-content">${highlight(line) || ' '}</span></span>`).join('');
        displayedFile = view.file;
      }
      root.querySelectorAll('.bw-code-line.is-active').forEach(line => line.classList.remove('is-active'));
      view.lines.forEach(number => query(`[data-line="${number}"]`)?.classList.add('is-active'));
      root.querySelectorAll('[data-file]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.file === view.file)));
      query('[data-location]').textContent = view.file + (view.lines.length ? ':' + view.lines[0] + (view.lines.length > 1 ? '–' + view.lines.at(-1) : '') : '');
      query('[data-function]').textContent = view.name;
      query('[data-follow]').hidden = manual === null;
      const scroller = query('[data-code-scroll]'),
        first = view.lines.length ? query(`[data-line="${view.lines[0]}"]`) : null;
      if (first) {
        const offset = first.getBoundingClientRect().top - scroller.getBoundingClientRect().top + scroller.scrollTop;
        scroller.scrollTop = Math.max(0, offset - scroller.clientHeight * .26);
      }
    }
    const variableRows = (rows, changed = []) => rows.map(([name, value]) => `<div class="bw-var${changed.includes(name) ? ' is-changed' : ''}"><dt><code>${escape(name)}</code></dt><dd><code>${escape(value)}</code></dd></div>`).join('');

    // Aktualizacja paneli dla wybranej migawki.
    function render(item, {
      step,
      traceLength,
      positions,
      mode,
      manual
    }) {
      const world = item.state ?? start,
        position = Math.max(0, positions.findLastIndex(index => index <= step));
      query('[data-progress]').max = positions.length - 1;
      query('[data-progress]').value = position;
      query('[data-step]').textContent = mode === 'iteration' ? `Etap ${position + 1} / ${positions.length}` : `Operacja ${step + 1} / ${traceLength}`;
      query('[data-iteration]').textContent = `Iteracja ${item.iteration}`;
      query('[data-action]').textContent = item.action;
      query('[data-detail]').textContent = item.detail;
      query('[data-status]').textContent = item.done ? '✓ Cel znaleziony' : item.building ? 'Odtwarzanie planu' : step === 0 ? 'Gotowe do przejścia' : 'Wyszukiwanie';
      query('[data-state]').textContent = key(world);
      query('[data-world-label]').textContent = item.state ? 'state · aktualnie przetwarzany' : 'start · przed pierwszym pop()';
      const from = item.state ? item.parent.find(([child]) => child === key(item.state))?.[1] : null;
      query('[data-move-label]').textContent = from ? `Ruch wejściowy ${tuple(from.move)}` : '';
      drawWorld(query('[data-world]'), world, false, item.movedBlock);
      query('[data-supports]').innerHTML = world.map((support, i) => `<div class="bw-support"><strong style="background:${blockColor(i + 1)}">${i + 1}</strong><span>${support === 0 ? 'stół (0)' : 'klocek ' + support}</span></div>`).join('');
      query('[data-candidate]').hidden = !item.candidate;
      if (item.candidate) {
        query('[data-next-state]').textContent = key(item.nextState);
        query('[data-candidate-status]').textContent = item.candidateStatus || `ruch ${tuple(item.move)}`;
        drawWorld(query('[data-preview]'), item.nextState, true, item.move?.[0]);
      }
      query('[data-vars-scope]').textContent = item.done ? 'solve_dfs · zapis końcowy' : 'solve_dfs';
      query('[data-vars]').innerHTML = variableRows([['state', tuple(item.state)], ['move', tuple(item.move)], ['next_state', tuple(item.nextState)], ['expanded', item.expanded], ['visited', `${item.visited.length} stanów`], ['parent', `${item.parent.length} powiązań`], ['stack', `${item.stack.length} stanów`], ['moves', item.moves ? item.moves.map(tuple).join(', ') : '—']], item.changed);
      let locals = item.locals;
      if (item.scope === '_build_plan()') {
        const collected = item.lines.includes(62) ? item.plan.slice().reverse() : item.plan;
        locals = [['state', tuple(item.planState)], ['move', tuple(item.planMove)], ['moves', collected.length ? collected.map(tuple).join(', ') : '[]']];
      }
      query('[data-locals]').innerHTML = locals.length ? `<h3 class="bw-locals-heading">Lokalne w ${escape(item.scope)}</h3><dl class="bw-variables">${variableRows(locals)}</dl>` : '';
      query('[data-collections]').innerHTML = `<div class="bw-collection"><h3>visited · ${item.visited.length}</h3>${item.visited.map(s => `<div><code>${escape(s)}</code></div>`).join('')}<h3>parent · ${item.parent.length}</h3>${item.parent.length ? item.parent.map(([child, value]) => `<div class="bw-parent-row"><code>${escape(child)} ← ${escape(key(value.state))}<br>ruch ${escape(tuple(value.move))}</code></div>`).join('') : 'Brak powiązań.'}</div>`;
      query('[data-stack-count]').textContent = `len(stack) = ${item.stack.length}`;
      query('[data-stack-note]').textContent = item.done ? 'Wyszukiwanie zakończone. Pozostałe stany nie będą już odwiedzane. Wierzchołek jest u góry.' : 'Stany oczekujące na odwiedzenie. Wierzchołek u góry; pop() zdejmie pierwszy wiersz.';
      query('[data-stack]').innerHTML = item.stack.slice().reverse().map((s, index) => `<li><code>${key(s)}</code><span class="bw-stack-tag">${index === 0 ? item.done ? '← wierzchołek' : '← następny' : `[${item.stack.length - index - 1}]`}</span></li>`).join('');
      query('[data-stack-empty]').hidden = item.stack.length !== 0;
      query('[data-call-count]').textContent = `Liczba ramek: ${item.calls.length}`;
      query('[data-calls]').innerHTML = item.calls.slice().reverse().map((call, index) => `<li><button type="button" class="bw-frame" data-frame="${item.calls.length - index - 1}"><code>${escape(call.name)}</code><span>${escape(call.file)}:${call.line}${index === 0 ? ' · aktywna' : ''}</span></button></li>`).join('');
      query('[data-plan-section]').hidden = !item.building;
      query('[data-plan-direction]').textContent = item.done || item.lines.includes(62) || item.action === 'Zwrócenie wyniku' ? 'Od startu do celu' : 'Od celu do startu · przed reversed()';
      query('[data-plan]').innerHTML = item.plan.map(([block, target]) => `<li><i class="bw-swatch" style="background:${blockColor(block)}" aria-hidden="true"></i><code>(${block}, ${target})</code><span>${target === 0 ? 'na stół' : 'na klocek ' + target}</span></li>`).join('') || '<li>Plan jest jeszcze pusty.</li>';
      query('[data-prev]').disabled = step === 0;
      query('[data-reset]').disabled = step === 0;
      query('[data-next]').disabled = step === traceLength - 1;
      renderCode(item, manual);
      root.dataset.traceStep = step;
      root.dataset.traceLength = traceLength;
    }
    function resize(item, manual) {
      drawWorld(query('[data-world]'), item.state ?? start);
      if (item.candidate) drawWorld(query('[data-preview]'), item.nextState, true);
      renderCode(item, manual);
    }
    return {
      render,
      renderCode,
      resize
    };
  }
  window.BlocksWorldDFS.createView = createView;
})();
