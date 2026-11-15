const $ = (id) => document.getElementById(id);
let moves = [],
  state = null,
  busy = false,
  generation = 0;
for (let c = 0; c < 7; c++) {
  const button = document.createElement("button");
  button.textContent = "↓";
  button.disabled = true;
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
  const computer = state.mode === "computer";
  const playerName = (player) =>
    computer
      ? player === state.human_player
        ? "You"
        : "Computer"
      : `Player ${player + 1}`;
  $("first-label").textContent = `${playerName(0)} · Red`;
  $("second-label").textContent = `${playerName(1)} · Yellow`;
  $("status").textContent = state.terminal
    ? state.winner === null
      ? "Draw"
      : computer && state.winner === state.human_player
        ? "You win!"
        : `${playerName(state.winner)} wins!`
    : computer && state.turn === state.human_player
      ? "Your turn"
      : `${playerName(state.turn)} to move`;
  $("counter").textContent = state.terminal
    ? `${moves.length} moves`
    : `Move ${moves.length + 1}`;
  Array.from($("columns").children).forEach(
    (b, c) =>
      (b.disabled =
        busy ||
        !state.legal.includes(c) ||
        (computer && state.turn !== state.human_player)),
  );
}
async function update(next, reset = false) {
  if (busy && !reset) return;
  const token = ++generation;
  busy = true;
  $("error").textContent = "";
  if (state) render();
  $("status").textContent =
    $("mode").value === "computer" ? "Computer is thinking…" : "Loading…";
  try {
    const response = await fetch("/api/game", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        moves: next,
        mode: $("mode").value,
        difficulty: $("difficulty").value,
        human_player: Number($("seat").value),
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
  $("seat-field").hidden = $("mode").value === "human";
  update([], true);
};
$("difficulty").onchange = () => update([], true);
$("seat").onchange = () => update([], true);
update([]);
