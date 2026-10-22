// Elementy interfejsu, słowniki i stan wizualizacji.
const $ = (id) => document.getElementById(id);
const canvas = $('board'),
  ctx = canvas.getContext('2d');
const names = {
  left: 'Obrót w lewo',
  right: 'Obrót w prawo',
  forward: 'Naprzód',
  grab: 'Podnieś złoto',
  shoot: 'Strzał',
  climb: 'Wyjście',
};
const directions = { n: 'północ', e: 'wschód', s: 'południe', w: 'zachód' };
const angles = { n: -Math.PI / 2, e: 0, s: Math.PI / 2, w: Math.PI };
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
let state,
  previous,
  playing = false,
  busy = false,
  truth = false,
  selected = null,
  timer = null;
let animationStart = 0,
  animationDuration = 0,
  geometry = {},
  cssWidth = 0,
  cssHeight = 0;
let paintTime = 0;

// Komunikacja z Pythonem i sterowanie przebiegiem wyprawy.
async function api(path, payload) {
  const response = await fetch(
    '/api/' + path,
    payload === undefined
      ? {}
      : {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        },
  );
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Nie udało się wykonać operacji.');
  return data;
}

function stop() {
  playing = false;
  clearTimeout(timer);
  updateButtons();
}

function updateButtons() {
  $('play').textContent = playing ? 'Ⅱ Zatrzymaj pokaz' : '▶ Obserwuj agenta';
  $('play').disabled = (!playing && busy) || !state || state.done;
  $('stepAgent').disabled = busy || !state || state.done;
  document
    .querySelectorAll('[data-action]')
    .forEach((b) => (b.disabled = busy || !state || state.done));
  $('undo').disabled = busy || !state?.canUndo;
  $('outcomeUndo').disabled = busy || !state?.canUndo;
  $('newGame').disabled = busy;
}

async function command(path, payload = {}) {
  if (busy) return;
  busy = true;
  updateButtons();
  try {
    const next = await api(path, payload);
    previous = state;
    state = next;
    if (path === 'new') {
      previous = null;
      selected = null;
      $('cellInfo').textContent = 'Kliknij pole, aby sprawdzić jego status.';
    }
    animationStart = performance.now();
    animationDuration = reduced || path !== 'action' ? 0 : state.effect?.fired ? 580 : 310;
    render();
    await new Promise((resolve) => setTimeout(resolve, animationDuration));
    if (state.done) stop();
  } catch (error) {
    stop();
    $('message').textContent = error.message;
  } finally {
    busy = false;
    updateButtons();
  }
}

async function autoTick() {
  if (!playing) return;
  await command('action', { action: 'agent' });
  if (playing && !state.done) timer = setTimeout(autoTick, Number($('speed').value));
}

// Aktualizacja paneli: statystyki, percepcje, wnioski i historia akcji.
function render() {
  $('steps').textContent = String(state.steps).padStart(2, '0');
  $('gold').textContent = `${state.gold} / ${state.totalGold}`;
  $('arrows').textContent = state.arrows;
  $('score').textContent = state.score;
  $('position').textContent =
    `Pole (${state.pos.join(', ')}) · patrzysz na ${directions[state.direction]}`;
  const perceptions = [
    ['breeze', '≈', 'Powiew'],
    ['stench', '♨', 'Smród'],
    ['glitter', '◇', 'Blask'],
    ['bump', '⊥', 'Ściana'],
    ['scream', '!', 'Krzyk'],
  ];
  $('percepts').replaceChildren(
    ...perceptions.map(([key, icon, label]) => {
      const el = document.createElement('span');
      el.className = 'percept' + (state.percept[key] ? ' on' : '');
      const symbol = document.createElement('b');
      symbol.textContent = icon;
      el.append(symbol, document.createTextNode(label));
      el.title = state.percept[key] ? `${label}: tak` : `${label}: nie`;
      return el;
    }),
  );
  const notes = [];
  if (state.percept.breeze) notes.push('Powiew: na przynajmniej jednym sąsiednim polu jest jama.');
  if (state.percept.stench) notes.push('Smród: obok jest żywy lub martwy Wumpus.');
  if (state.percept.glitter) notes.push('Blask: możesz podnieść złoto na swoim polu.');
  if (state.percept.scream) notes.push('Krzyk potwierdza zabicie Wumpusa.');
  if (state.percept.bump) notes.push('Uderzenie w ścianę nie zmieniło pozycji.');
  $('perceptHelp').textContent =
    notes.join(' ') ||
    'Cisza. Brak powiewu i smrodu pozwala wykluczyć zagrożenia na sąsiednich polach.';
  const safe = state.cells.filter((c) => c.safe),
    uncertain = state.cells.filter((c) => c.frontier && !c.safe);
  let reason;
  if (!state.alive)
    reason =
      'Wyprawa zakończyła się śmiercią. To pole nie zostało dopisane do wiedzy jako bezpieczne. Cofnij ruch i porównaj dostępne wcześniej informacje.';
  else if (state.climbed)
    reason = 'Agent opuścił jaskinię. Punkty za złoto naliczane są dopiero po wyjściu.';
  else if (safe.length)
    reason = `Bezpieczne pola na granicy poznanego obszaru: ${safe.map((c) => `(${c.x}, ${c.y})`).join(', ')}. Ich bezpieczeństwo wynika ze wszystkich modeli zgodnych z obserwacjami.`;
  else
    reason =
      'Brak nowych pól, których bezpieczeństwo jest dowiedzione. Agent może zabezpieczyć pole strzałą, zaryzykować (zależnie od strategii) albo wrócić do wejścia.';
  if (uncertain.length && !state.done)
    reason += ` Niepewnych pól przy poznanym obszarze: ${uncertain.length}. Możliwość zagrożenia nie oznacza jego pewności.`;
  $('reason').textContent = reason;
  $('goal').textContent = state.goal;
  $('plan').textContent = state.plan.length
    ? 'Pozostały plan: ' + state.plan.map((a) => names[a]).join(' → ')
    : 'Nowy plan zostanie wybrany przy kolejnej decyzji.';
  $('facts').textContent = state.facts;
  $('message').textContent = state.message;
  $('journal').replaceChildren(
    ...[...state.events].reverse().map((event) => {
      const li = document.createElement('li'),
        number = document.createElement('span'),
        pos = document.createElement('small');
      number.textContent = String(event.step).padStart(2, '0');
      pos.textContent = `(${event.pos.join(', ')})`;
      li.append(number, document.createTextNode(names[event.action]), pos);
      li.title = event.message;
      return li;
    }),
  );
  $('outcome').hidden = !state.done;
  if (state.done) {
    $('outcomeLabel').textContent = state.alive ? 'WYPRAWA ZAKOŃCZONA' : 'KONIEC WYPRAWY';
    $('outcomeTitle').textContent = !state.alive
      ? 'Jaskinia wygrała.'
      : state.gold
        ? 'Złoto jest twoje.'
        : 'Bezpieczny powrót.';
    $('outcomeDetail').textContent =
      `Złoto: ${state.gold} / ${state.totalGold} · Akcje: ${state.steps} · Wynik: ${state.score}`;
  }
  if (selected) describeCell();
  updateButtons();
}

// Opis pola wybranego na planszy, zależny od aktywnego widoku.
function describeCell() {
  const cell = state.cells.find((c) => c.x === selected[0] && c.y === selected[1]);
  if (!cell) return;
  const parts = [];
  if (truth) {
    if (cell.pit) parts.push('jama');
    if (cell.wumpus) parts.push(cell.alive ? 'żywy Wumpus' : 'martwy Wumpus');
    if (cell.gold) parts.push('złoto');
    if (!parts.length) parts.push('brak zagrożeń i złota');
  } else {
    if (cell.visited) parts.push('odwiedzone');
    else if (cell.safe) parts.push('na pewno bezpieczne');
    else parts.push('nieodwiedzone');
    if (cell.pit_certain) parts.push('pewna jama');
    else if (cell.frontier && cell.pit_possible) parts.push('możliwa jama');
    if (cell.alive_certain) parts.push('pewny żywy Wumpus');
    else if (cell.alive_possible) parts.push('możliwy żywy Wumpus');
    if (cell.dead_certain) parts.push('pewny martwy Wumpus');
    if (cell.visited && cell.breeze) parts.push('zaobserwowano powiew');
    if (cell.visited && cell.stench) parts.push('zaobserwowano smród');
  }
  $('cellInfo').textContent = `(${cell.x}, ${cell.y}) · ${parts.join(' · ')}`;
}

// Rozmiar płótna i pomocnicze operacje rysowania.
function resize() {
  const rect = canvas.getBoundingClientRect(),
    dpr = window.devicePixelRatio || 1;
  cssWidth = rect.width;
  cssHeight = rect.height;
  canvas.width = Math.round(rect.width * dpr);
  canvas.height = Math.round(rect.height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function roundRect(x, y, w, h, r, fill, stroke) {
  ctx.beginPath();
  ctx.roundRect(x, y, w, h, r);
  if (fill) {
    ctx.fillStyle = fill;
    ctx.fill();
  }
  if (stroke) {
    ctx.strokeStyle = stroke;
    ctx.stroke();
  }
}

function text(str, x, y, size, color, align = 'center') {
  ctx.fillStyle = color;
  ctx.font = `${size}px "Segoe UI",sans-serif`;
  ctx.textAlign = align;
  ctx.textBaseline = 'middle';
  ctx.fillText(str, x, y);
}

function center(x, y) {
  const { left, top, size } = geometry;
  return [left + (x - 0.5) * size, top + (state.height - y + 0.5) * size];
}

// Symbole obiektów świata i postaci agenta.
function monster(x, y, r, alive = true) {
  ctx.save();
  ctx.translate(x, y);
  ctx.strokeStyle = alive ? '#d6b09c' : '#77918a';
  ctx.fillStyle = alive ? '#735a4f' : '#344c46';
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(-r * 0.8, -r * 0.15);
  ctx.lineTo(-r, -r * 0.95);
  ctx.lineTo(-r * 0.35, -r * 0.65);
  ctx.quadraticCurveTo(0, -r * 0.85, r * 0.35, -r * 0.65);
  ctx.lineTo(r, -r * 0.95);
  ctx.lineTo(r * 0.8, -r * 0.1);
  ctx.bezierCurveTo(r * 1.3, r * 1.2, -r * 1.3, r * 1.2, -r * 0.8, -r * 0.15);
  ctx.fill();
  ctx.stroke();
  if (alive) {
    for (const ex of [-0.35, 0.35]) {
      ctx.fillStyle = '#f5e6c7';
      ctx.beginPath();
      ctx.ellipse(ex * r, -r * 0.05, r * 0.15, r * 0.18, 0, 0, 7);
      ctx.fill();
      ctx.fillStyle = '#192627';
      ctx.beginPath();
      ctx.arc(ex * r, -r * 0.03, r * 0.065, 0, 7);
      ctx.fill();
    }
    ctx.beginPath();
    ctx.moveTo(-r * 0.35, r * 0.4);
    ctx.quadraticCurveTo(0, r * 0.57, r * 0.35, r * 0.4);
    ctx.stroke();
  } else {
    text('× ×', 0, 0, r * 0.65, '#abc0b3');
  }
  ctx.restore();
}

function gold(x, y, r) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(Math.PI / 4);
  roundRect(-r / 2, -r / 2, r, r, 2, '#ddc375', '#fff0af');
  ctx.restore();
  ctx.strokeStyle = '#b39e64';
  ctx.beginPath();
  ctx.moveTo(x + r, y - r);
  ctx.lineTo(x + r + 4, y - r);
  ctx.moveTo(x + r + 2, y - r - 2);
  ctx.lineTo(x + r + 2, y - r + 2);
  ctx.stroke();
}

function pit(x, y, r) {
  ctx.fillStyle = '#091212';
  ctx.strokeStyle = '#ad8d71';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.ellipse(x, y, r, r * 0.56, -0.12, 0, 7);
  ctx.fill();
  ctx.stroke();
  ctx.strokeStyle = '#4c5b54';
  ctx.beginPath();
  ctx.ellipse(x, y + 1, r * 0.65, r * 0.27, -0.12, 0, Math.PI);
  ctx.stroke();
}

function explorer(x, y, angle, r, alive) {
  ctx.save();
  ctx.translate(x, y);
  ctx.shadowColor = '#d7f58455';
  ctx.shadowBlur = alive ? 18 : 0;
  ctx.fillStyle = alive ? '#d7f584' : '#b89581';
  ctx.beginPath();
  ctx.arc(0, 0, r * 0.78, 0, 7);
  ctx.fill();
  ctx.shadowBlur = 0;
  ctx.strokeStyle = '#28392c';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(0, -r * 0.09, r * 0.36, 0, 7);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(-r * 0.48, r * 0.48);
  ctx.quadraticCurveTo(0, r * 0.04, r * 0.48, r * 0.48);
  ctx.stroke();
  ctx.rotate(angle);
  ctx.fillStyle = alive ? '#e7ffb2' : '#b89581';
  ctx.beginPath();
  ctx.moveTo(r * 1.5, 0);
  ctx.lineTo(r * 0.95, -r * 0.26);
  ctx.lineTo(r * 0.95, r * 0.26);
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

// Główna pętla rysowania planszy i animacji.
function draw(now) {
  requestAnimationFrame(draw);
  if (!state) return;
  if (now - paintTime < 30 && !animationDuration) return;
  paintTime = now;
  ctx.clearRect(0, 0, cssWidth, cssHeight);
  const size = Math.min((cssWidth - 72) / state.width, (cssHeight - 86) / state.height);
  const left = (cssWidth - size * state.width) / 2,
    top = (cssHeight - size * state.height) / 2 + 8;
  geometry = { left, top, size };
  const t = animationDuration ? Math.min(1, (now - animationStart) / animationDuration) : 1,
    eased = t * t * (3 - 2 * t);
  for (const cell of state.cells) {
    const [cx, cy] = center(cell.x, cell.y),
      x = cx - size / 2,
      y = cy - size / 2;
    const reveal = truth || cell.visited,
      certain = cell.pit_certain || cell.alive_certain;
    const fill = reveal ? '#253a35' : cell.safe ? '#293d32' : cell.frontier ? '#2a302c' : '#182729';
    roundRect(
      x + 3,
      y + 3,
      size - 6,
      size - 6,
      7,
      fill,
      reveal ? '#40574b' : cell.safe ? '#728c54' : certain ? '#a97c5c' : '#2b3d3c',
    );
    if (!reveal && !cell.safe && !cell.frontier) {
      text('·', cx, cy, size * 0.25, '#52655e');
    }
    text(`${cell.x},${cell.y}`, x + 12, y + size - 14, 9, '#82988c', 'left');
    if (cell.x === 1 && cell.y === 1) {
      text('WEJŚCIE', cx, y + 16, 8, '#b5ce9a');
      ctx.strokeStyle = '#84996a';
      ctx.lineWidth = 1.5;
      ctx.strokeRect(cx - size * 0.2, cy - size * 0.2, size * 0.4, size * 0.4);
    }
    if (reveal) {
      if (cell.pit) pit(cx, cy + size * 0.05, size * 0.24);
      if (cell.wumpus) monster(cx, cy - size * 0.03, size * 0.19, cell.alive);
      if (cell.gold)
        gold(
          cx + size * 0.2,
          cy - size * 0.21,
          size * 0.17 * (reduced ? 1 : 1 + Math.sin(now / 650) * 0.07),
        );
      if (cell.visited && (cell.breeze || cell.stench))
        text(
          `${cell.breeze ? '≈ ' : ''}${cell.stench ? '♨' : ''}`,
          x + size - 13,
          y + size - 15,
          13,
          '#b6be99',
          'right',
        );
    } else {
      if (cell.safe) {
        text('✓', cx, cy, 20, '#c6e399');
        text('BEZPIECZNE', cx, cy + 21, size < 78 ? 6 : 8, '#abc18c');
      } else if (cell.pit_certain) {
        pit(cx, cy, size * 0.2);
        text('PEWNA JAMA', cx, cy + size * 0.3, 7, '#d7b196');
      } else if (cell.alive_certain) {
        monster(cx, cy, size * 0.17);
        text('PEWNY WUMPUS', cx, cy + size * 0.3, 7, '#d7b196');
      } else if (cell.frontier) {
        text('?', cx, cy - 6, 25, '#c5aa8d');
        text(
          [cell.pit_possible ? 'JAMA?' : '', cell.alive_possible ? 'WUMPUS?' : '']
            .filter(Boolean)
            .join(' / '),
          cx,
          cy + size * 0.2,
          size < 90 ? 6 : 8,
          '#af9e87',
        );
      }
      if (cell.dead_certain) text('× W', cx, cy, 16, '#94b0a1');
    }
    if (selected && cell.x === selected[0] && cell.y === selected[1]) {
      ctx.lineWidth = 2;
      roundRect(x + 3, y + 3, size - 6, size - 6, 7, null, '#e6edcc');
      ctx.lineWidth = 1;
    }
  }
  // Ślad pochodzi wyłącznie z wykonanych ruchów, bez ujawniania mapy.
  if ($('showTrail').checked) {
    ctx.strokeStyle = '#b4cf8b55';
    ctx.lineWidth = 2;
    ctx.setLineDash([3, 5]);
    ctx.beginPath();
    const start = center(1, 1);
    ctx.moveTo(...start);
    for (const pos of state.trail) ctx.lineTo(...center(...pos));
    ctx.stroke();
    ctx.setLineDash([]);
  }
  for (let x = 1; x <= state.width; x++)
    text(String(x), center(x, 1)[0], top + size * state.height + 18, 10, '#81938d');
  for (let y = 1; y <= state.height; y++)
    text(String(y), left - 18, center(1, y)[1], 10, '#81938d');
  let px = state.pos[0],
    py = state.pos[1],
    angle = angles[state.direction];
  if (previous && t < 1) {
    px = previous.pos[0] + (px - previous.pos[0]) * eased;
    py = previous.pos[1] + (py - previous.pos[1]) * eased;
    let delta = angle - angles[previous.direction];
    if (delta > Math.PI) delta -= Math.PI * 2;
    if (delta < -Math.PI) delta += Math.PI * 2;
    angle = angles[previous.direction] + delta * eased;
  }
  const [ax, ay] = center(px, py);
  explorer(ax, ay, angle, size * 0.18, state.alive);
  if (t < 1 && state.effect?.fired) {
    const path = state.effect.path;
    if (path.length) {
      const [sx, sy] = center(...state.effect.origin),
        [ex, ey] = center(...path[path.length - 1]);
      const q = Math.min(1, t * 1.4),
        bx = sx + (ex - sx) * q,
        by = sy + (ey - sy) * q;
      ctx.strokeStyle = '#f3df9c';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(sx, sy);
      ctx.lineTo(bx, by);
      ctx.stroke();
      text('✦', bx, by, 20, '#fff0bf');
    }
  }
  if (t < 1 && state.percept.bump) {
    ctx.strokeStyle = `rgba(221,164,123,${1 - t})`;
    ctx.lineWidth = 3;
    roundRect(
      left - 3,
      top - 3,
      size * state.width + 6,
      size * state.height + 6,
      10,
      null,
      ctx.strokeStyle,
    );
  }
  if (t >= 1) animationDuration = 0;
}

// Obsługa przycisków, wyboru pola i skrótów klawiaturowych.
$('play').onclick = () => {
  if (playing) stop();
  else {
    playing = true;
    updateButtons();
    autoTick();
  }
};
$('stepAgent').onclick = () => {
  stop();
  command('action', { action: 'agent' });
};
document.querySelectorAll('[data-action]').forEach(
  (button) =>
    (button.onclick = () => {
      stop();
      command('action', { action: button.dataset.action });
    }),
);
$('undo').onclick = $('outcomeUndo').onclick = () => {
  stop();
  command('undo');
};
$('newGame').onclick = () => {
  stop();
  command('new', {
    scenario: $('scenario').value,
    strategy: $('strategy').value,
    seed: $('seed').value || 7,
  });
};
function setView(full) {
  truth = full;
  $('truthView').classList.toggle('active', truth);
  $('knowledgeView').classList.toggle('active', !truth);
  $('truthView').setAttribute('aria-pressed', truth);
  $('knowledgeView').setAttribute('aria-pressed', !truth);
  $('boardMode').textContent = truth
    ? 'PRAWDZIWY ŚWIAT · AGENT NIE WIDZI TEJ MAPY'
    : 'TYLKO TO, CO WIADOMO';
  if (selected) describeCell();
}
$('knowledgeView').onclick = () => setView(false);
$('truthView').onclick = () => setView(true);
$('helpButton').onclick = () => {
  $('help').showModal();
  stop();
};
$('closeHelp').onclick = () => $('help').close();
canvas.onclick = (event) => {
  if (!state) return;
  const rect = canvas.getBoundingClientRect();
  const x = Math.floor((event.clientX - rect.left - geometry.left) / geometry.size) + 1,
    y = state.height - Math.floor((event.clientY - rect.top - geometry.top) / geometry.size);
  if (x >= 1 && x <= state.width && y >= 1 && y <= state.height) {
    selected = [x, y];
    describeCell();
  }
};
window.addEventListener('keydown', (event) => {
  if (
    ['INPUT', 'SELECT', 'TEXTAREA'].includes(event.target.tagName) ||
    $('help').open ||
    event.ctrlKey ||
    event.metaKey ||
    event.altKey ||
    event.repeat
  )
    return;
  const action = {
    ArrowLeft: 'left',
    ArrowRight: 'right',
    ArrowUp: 'forward',
    g: 'grab',
    f: 'shoot',
    e: 'climb',
  }[event.key.length === 1 ? event.key.toLowerCase() : event.key];
  if (action) {
    event.preventDefault();
    if (!busy && state && !state.done) {
      stop();
      command('action', { action });
    }
  }
  if (event.code === 'Space' && !['BUTTON', 'SUMMARY'].includes(event.target.tagName)) {
    event.preventDefault();
    if (!$('play').disabled) $('play').click();
  }
});
// Inicjalizacja płótna i pobranie bieżącego stanu gry.
new ResizeObserver(resize).observe(canvas);
resize();
requestAnimationFrame(draw);
api('state')
  .then((data) => {
    state = data;
    render();
  })
  .catch((error) => {
    $('message').textContent = 'Nie można połączyć się z serwerem: ' + error.message;
  });
