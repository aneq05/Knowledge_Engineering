# Step-by-step DFS visualization

Open `dfs-krok-po-kroku.html` in a browser. The visualization runs offline
directly from disk. To move it, copy both the HTML file and the adjacent
`dfs-krok-po-kroku/` directory.

## Files

| File | Purpose |
| --- | --- |
| `dfs-krok-po-kroku.html` | Page structure, buttons, and panels. |
| `dfs-krok-po-kroku/styles.css` | Styles, animations, mobile layout, and dark theme. |
| `dfs-krok-po-kroku/sources.js` | Copies of the Python code displayed in the source panel. |
| `dfs-krok-po-kroku/trace.js` | Example state and generation of DFS trace snapshots. |
| `dfs-krok-po-kroku/view.js` | Block rendering, code highlighting, and panel updates. |
| `dfs-krok-po-kroku/app.js` | Step controls, playback, event handling, and playback position storage. |

The scripts load in the order specified in the HTML and share
`window.BlocksWorldDFS`. Classic scripts with `defer` support direct opening
via `file://` and avoid the browser restrictions that affect modules and
`fetch` on local files.

## Editing the example code

`sources.js` contains static copies of the Python code. The line numbers in
`trace.js` refer to those copies. Update the corresponding trace line
numbers whenever you edit the displayed code.
