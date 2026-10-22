(() => {
  'use strict';

  const {
    makeTrace,
    createView
  } = window.BlocksWorldDFS;
  const root = document.getElementById('bw-dfs-explainer');
  const query = selector => root.querySelector(selector);
  const view = createView(root);
  // Stan odtwarzacza i przywracanie zapisanej pozycji.
  const trace = makeTrace(),
    checkpoints = trace.map((item, index) => item.checkpoint ? index : -1).filter(index => index >= 0);
  let step = 0,
    manual = null,
    timer = null,
    mode = 'iteration';
  try {
    const saved = window.openai?.widgetState?.privateContent;
    if (Number.isInteger(saved?.step)) step = saved.version === 2 ? Math.max(0, Math.min(trace.length - 1, saved.step)) : checkpoints[Math.max(0, Math.min(checkpoints.length - 1, saved.step))] ?? 0;
    if (saved?.mode === 'operation') mode = 'operation';
  } catch {}
  query('[data-mode]').value = mode;

  // Wybór kroków i aktualizacja widoku.
  function currentPositions() {
    return mode === 'iteration' ? checkpoints : trace.map((_, index) => index);
  }
  function render() {
    view.render(trace[step], {
      step,
      traceLength: trace.length,
      positions: currentPositions(),
      mode,
      manual
    });
  }

  // Integracja z zapisem stanu widżetu (opcjonalna przy otwarciu lokalnym).
  function save() {
    try {
      window.openai?.setWidgetState?.({
        modelContent: {
          problem: 'Blocks World: DFS',
          step,
          state: trace[step].state,
          expanded: trace[step].expanded
        },
        privateContent: {
          step,
          mode,
          version: 2
        }
      })?.catch?.(() => {});
    } catch {}
  }

  // Nawigacja i odtwarzanie.
  function stop() {
    clearInterval(timer);
    timer = null;
    query('[data-play]').textContent = '▶ Odtwarzaj';
    query('[data-play]').setAttribute('aria-pressed', 'false');
  }
  function go(index) {
    step = Math.max(0, Math.min(trace.length - 1, index));
    manual = null;
    render();
    save();
    if (step === trace.length - 1) stop();
  }
  function advance(direction) {
    const positions = currentPositions(),
      target = direction > 0 ? positions.find(index => index > step) : positions.findLast(index => index < step);
    go(target ?? (direction > 0 ? trace.length - 1 : 0));
  }

  // Przyciski, suwak i tryb krokowania.
  query('[data-prev]').addEventListener('click', () => {
    stop();
    advance(-1);
  });
  query('[data-next]').addEventListener('click', () => {
    stop();
    advance(1);
  });
  query('[data-reset]').addEventListener('click', () => {
    stop();
    go(0);
  });
  query('[data-end]').addEventListener('click', () => {
    stop();
    go(trace.length - 1);
  });
  query('[data-progress]').addEventListener('input', event => {
    stop();
    go(currentPositions()[Number(event.target.value)]);
  });
  query('[data-mode]').addEventListener('change', event => {
    stop();
    mode = event.target.value;
    manual = null;
    render();
    save();
  });
  query('[data-play]').addEventListener('click', () => {
    if (timer) {
      stop();
      return;
    }
    if (step === trace.length - 1) go(0);
    query('[data-play]').textContent = 'Ⅱ Pauza';
    query('[data-play]').setAttribute('aria-pressed', 'true');
    timer = setInterval(() => advance(1), mode === 'iteration' ? 1600 : 1200);
  });

  // Ręczny podgląd pliku lub ramki stosu wywołań.
  root.addEventListener('click', event => {
    const file = event.target.closest('[data-file]'),
      selectedFrame = event.target.closest('[data-frame]');
    if (file) {
      stop();
      manual = {
        file: file.dataset.file,
        lines: [],
        name: 'Podgląd pliku · następny krok wraca do kodu'
      };
      view.renderCode(trace[step], manual);
    }
    if (selectedFrame) {
      stop();
      const call = trace[step].calls[Number(selectedFrame.dataset.frame)];
      manual = {
        file: call.file,
        lines: [call.line],
        name: call.name
      };
      view.renderCode(trace[step], manual);
    }
  });
  query('[data-follow]').addEventListener('click', () => {
    manual = null;
    view.renderCode(trace[step], manual);
  });

  // Klawiatura i zdarzenia otoczenia strony.
  root.addEventListener('keydown', event => {
    if (event.ctrlKey || event.altKey || event.metaKey || /^(INPUT|SELECT|TEXTAREA)$/.test(event.target.tagName)) return;
    if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
      event.preventDefault();
      stop();
      advance(event.key === 'ArrowRight' ? 1 : -1);
    }
  });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) stop();
  });
  window.addEventListener('openai:set_globals', event => {
    const saved = event.detail?.globals?.widgetState?.privateContent;
    if (Number.isInteger(saved?.step)) {
      stop();
      if (saved.mode === 'operation' || saved.mode === 'iteration') {
        mode = saved.mode;
        query('[data-mode]').value = mode;
      }
      step = Math.max(0, Math.min(trace.length - 1, saved.step));
      manual = null;
      render();
    }
  });
  new ResizeObserver(() => view.resize(trace[step], manual)).observe(query('[data-world]'));
  render();
})();
