const $ = (id) => document.getElementById(id);
let moves = [],
  state = null,
  busy = false,
  generation = 0;
for (let c = 0; c < 7; c++) {
  const button = document.createElement("button");
  button.textContent = "↓";
  button.setAttribute("aria-label", `Drop disc in column ${c + 1}`);
  button.addEventListener("click", () => update([...moves, c]));
  $("columns").append(button);
}
function render() {
  $("board").replaceChildren();
  for (const [r, row] of state.board.entries())
    for (const [c, value] of row.entries()) {
      const cell = document.createElement("div");
      cell.className = `cell p${value}`;
      cell.setAttribute(
        "aria-label",
        `Row ${r + 1}, column ${c + 1}: ${value ? "player " + value : "empty"}`,
      );
      $("board").append(cell);
    }
  $("status").textContent = state.terminal
    ? state.winner === null
      ? "A draw. Well played!"
      : `Player ${state.winner + 1} wins!`
    : `Player ${state.turn + 1} to move`;
  $("counter").textContent =
    `MOVE ${String(moves.length + 1).padStart(2, "0")}`;
  Array.from($("columns").children).forEach(
    (b, c) => (b.disabled = busy || !state.legal.includes(c)),
  );
}
async function update(next, reset = false) {
  if (busy && !reset) return;
  const token = ++generation;
  busy = true;
  $("error").textContent = "";
  if (state) render();
  $("status").textContent = "Thinking…";
  try {
    const response = await fetch("/api/game", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        moves: next,
        mode: $("mode").value,
        difficulty: $("difficulty").value,
      }),
    });
    const data = await response.json();
    if (token !== generation) return;
    if (!response.ok) throw new Error(data.error || "Unable to update game.");
    state = data;
    moves = data.moves;
  } catch (error) {
    if (token === generation) $("error").textContent = error.message;
  } finally {
    if (token === generation) {
      busy = false;
      if (state) render();
    }
  }
}
$("reset").onclick = () => update([], true);
$("mode").onchange = () => {
  $("difficulty").disabled = $("mode").value === "human";
  update([], true);
};
$("difficulty").onchange = () => update([], true);
update([]);
