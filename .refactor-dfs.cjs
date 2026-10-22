const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const parser = require('@babel/parser');
const generate = require('@babel/generator').default;
const postcss = require('postcss');

const directory = path.resolve('blocks_world_basic/other_resources/visualizations');
const filename = path.join(directory, 'dfs-krok-po-kroku.html');
const original = fs.readFileSync(filename, 'utf8');
const backup = path.join(os.tmpdir(), 'dfs-before-refactor.html');
fs.writeFileSync(backup, original);
const assets = path.join(directory, 'dfs-krok-po-kroku');
fs.mkdirSync(assets, { recursive: true });
const sources = JSON.parse(original.match(/<script type="application\/json" id="bw-dfs-source">([\s\S]*?)<\/script>/)[1]);
const script = original.match(/<script>([\s\S]*?)<\/script>/)[1];
const css = original.match(/<style>([\s\S]*?)<\/style>/)[1];

function writeScript(name, content) {
  const ast = parser.parse(content);
  fs.writeFileSync(path.join(assets, name), generate(ast, { comments: true }).code + '\n');
}

// Keep the Python snapshots readable, with exactly the original line numbering.
const snapshots = Object.entries(sources).map(([name, source]) => {
  assert(!source.includes('`') && !source.includes('${'));
  return `  ${JSON.stringify(name)}: String.raw\`${source}\``;
}).join(',\n\n');
fs.writeFileSync(path.join(assets, 'sources.js'), `// Kod wyświetlany w panelu. Numery linii w trace.js odnoszą się do tych kopii.\n// String.raw zachowuje sekwencje takie jak \\n w kodzie Pythona.\nwindow.BlocksWorldDFS = {\n  sources: {\n${snapshots}\n  }\n};\n`);

const helpers = script.slice(script.indexOf('  const start='), script.indexOf('  // Snapshots'));
const traceFunction = script.slice(script.indexOf('  // Snapshots'), script.indexOf('  const trace=makeTrace()'));
writeScript('trace.js', `(() => {\n'use strict';\nconst { sources } = window.BlocksWorldDFS;\n// Stan przykładu i funkcje wspólne dla przebiegu oraz widoku.\n${helpers.replace(/  const escape=.*\n/, '')}\n${traceFunction.replace('// Snapshots mirror the Python search order and its visited-at-push rule.', '// Migawki zachowują kolejność wyszukiwania Pythona i dodawanie do visited przy odkryciu.')}\nObject.assign(window.BlocksWorldDFS, { start, goal, key, tuple, makeTrace });\n})();`);

const escapeHelper = helpers.match(/  const escape=.*\n/)[0];
const drawing = script.slice(script.indexOf('  const blockColor='), script.indexOf('  const currentPositions='));
const render = script.slice(script.indexOf('  function render()'), script.indexOf('  function save()'))
  .replace('function render() {', 'function render(item, { step, traceLength, positions, mode, manual }) {')
  .replace('const item=trace[step],world=item.state??start,positions=currentPositions(),position=', 'const world=item.state??start,position=')
  .replaceAll('trace.length', 'traceLength')
  .replace('renderCode(item);', 'renderCode(item, manual);');
writeScript('view.js', `(() => {\n'use strict';\nconst { sources, start, key, tuple } = window.BlocksWorldDFS;\n${escapeHelper}\n// Widok otrzymuje migawkę; nie zmienia pozycji odtwarzania ani przebiegu DFS.\nfunction createView(root) {\nconst query = selector => root.querySelector(selector);\nlet displayedFile = null;\n// Rysowanie klocków i podgląd kodu Pythona.\n${drawing.replace('function renderCode(item) {', 'function renderCode(item, manual = null) {')}\n// Aktualizacja paneli dla wybranej migawki.\n${render}\nfunction resize(item, manual) {\ndrawWorld(query('[data-world]'), item.state ?? start);\nif (item.candidate) drawWorld(query('[data-preview]'), item.nextState, true);\nrenderCode(item, manual);\n}\nreturn { render, renderCode, resize };\n}\nwindow.BlocksWorldDFS.createView = createView;\n})();`);

let controller = script.slice(script.indexOf('  const trace=makeTrace()'), script.indexOf('  const blockColor='));
controller = controller.replace('displayedFile=null,', '');
controller += `\nfunction currentPositions() { return mode === 'iteration' ? checkpoints : trace.map((_, index) => index); }\nfunction render() { view.render(trace[step], { step, traceLength: trace.length, positions: currentPositions(), mode, manual }); }\n`;
controller += script.slice(script.indexOf('  function save()'), script.lastIndexOf('})();'));
controller = controller.replaceAll('renderCode(trace[step])', 'view.renderCode(trace[step], manual)');
controller = controller.replace(/new ResizeObserver\(\(\)=>\{const item=trace\[step\];.*?\}\)\.observe/, 'new ResizeObserver(() => view.resize(trace[step], manual)).observe');
writeScript('app.js', `(() => {\n'use strict';\nconst { makeTrace, createView } = window.BlocksWorldDFS;\nconst root = document.getElementById('bw-dfs-explainer');\nconst query = selector => root.querySelector(selector);\nconst view = createView(root);\n// Stan odtwarzacza i przywracanie zapisanej pozycji.\n${controller}\n})();`);

// Format CSS through its syntax tree, without changing selectors or declarations.
const stylesheet = postcss.parse(css);
function formatCss(nodes, depth = 0) {
  const indent = '  '.repeat(depth);
  return nodes.map(node => {
    if (node.type === 'decl') return `${indent}${node.prop}: ${node.value}${node.important ? ' !important' : ''};`;
    if (node.type === 'comment') return `${indent}/* ${node.text} */`;
    const header = node.type === 'rule' ? node.selector : `@${node.name}${node.params ? ' ' + node.params : ''}`;
    return `${indent}${header} {\n${formatCss(node.nodes, depth + 1)}\n${indent}}`;
  }).join(depth === 0 ? '\n\n' : '\n');
}
let formattedCss = formatCss(stylesheet.nodes);
for (const [selector, label] of [
  ['#bw-dfs-explainer {', 'Motyw i ustawienia bazowe'],
  ['#bw-dfs-explainer .bw-header {', 'Nagłówek i sterowanie'],
  ['#bw-dfs-explainer .bw-workspace {', 'Układ strony i świat klocków'],
  ['#bw-dfs-explainer .bw-location {', 'Panel kodu Pythona'],
  ['#bw-dfs-explainer .bw-inspectors {', 'Zmienne i stosy'],
  ['#bw-dfs-explainer .bw-plan-section {', 'Plan i stopka'],
  ['@keyframes bw-block-arrive {', 'Animacje'],
  ['@media (max-width:1000px) {', 'Układ responsywny i preferencje użytkownika']
]) {
  formattedCss = formattedCss.replace(selector, `/* ${label} */\n${selector}`);
}
fs.writeFileSync(path.join(assets, 'styles.css'), formattedCss + '\n');

// Split block elements onto their own lines, preserving inline text and elements.
const body = original.slice(original.indexOf('<div id="bw-dfs-explainer"'), original.indexOf('<style>')).trim();
const blockTags = new Set(['div', 'header', 'nav', 'section', 'footer', 'h1', 'h2', 'p', 'svg', 'ol', 'dl', 'details']);
const voidTags = new Set(['meta', 'link', 'input', 'br']);
let depth = 2;
let line = '';
const htmlLines = [];
function flush() { if (line.trim()) htmlLines.push('  '.repeat(depth) + line.trim()); line = ''; }
for (const token of body.match(/<[^>]+>|[^<]+/g)) {
  const tag = token.match(/^<(\/)?([\w-]+)/);
  if (!tag) { line += token.trim() ? token.replace(/\s+/g, ' ') : ''; continue; }
  const [, closing, name] = tag;
  if (blockTags.has(name)) {
    flush();
    if (closing) depth--;
    htmlLines.push('  '.repeat(depth) + token);
    if (!closing && !voidTags.has(name)) depth++;
  } else {
    line += token;
    if (['button', 'label', 'span', 'summary'].includes(name) && closing && !['span'].includes(name)) flush();
  }
}
flush();
const html = `<!doctype html>\n<html lang="pl">\n  <head>\n    <meta charset="utf-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1">\n    <title>DFS krok po kroku — Świat klocków</title>\n    <link rel="stylesheet" href="dfs-krok-po-kroku/styles.css">\n    <!-- Kolejność: kod Pythona, przebieg DFS, widok, sterowanie. -->\n    <script defer src="dfs-krok-po-kroku/sources.js"></script>\n    <script defer src="dfs-krok-po-kroku/trace.js"></script>\n    <script defer src="dfs-krok-po-kroku/view.js"></script>\n    <script defer src="dfs-krok-po-kroku/app.js"></script>\n  </head>\n  <body>\n${htmlLines.join('\n')}\n  </body>\n</html>\n`;
fs.writeFileSync(filename, html);

// Compare every generated snapshot against the original implementation.
const oldContext = vm.createContext({ window: {}, document: { getElementById: id => id === 'bw-dfs-source' ? { textContent: JSON.stringify(sources) } : {} } });
vm.runInContext(script.slice(0, script.indexOf('  const trace=makeTrace()')) + 'window.trace = makeTrace();})();', oldContext);
const newContext = vm.createContext({ window: {} });
for (const file of ['sources.js', 'trace.js']) vm.runInContext(fs.readFileSync(path.join(assets, file), 'utf8'), newContext);
assert.equal(JSON.stringify(newContext.window.BlocksWorldDFS.sources), JSON.stringify(sources));
assert.equal(JSON.stringify(newContext.window.BlocksWorldDFS.makeTrace()), JSON.stringify(oldContext.window.trace));
console.log(`Zgodne wszystkie ${oldContext.window.trace.length} migawki DFS i kopie kodu Python. Oryginał do porównania: ${backup}`);
