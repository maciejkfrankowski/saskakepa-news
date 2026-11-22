(() => {
  const dataEl = document.getElementById("sudoku-data");
  const board = document.getElementById("su-board");
  if (!dataEl || !board) return;

  const data = JSON.parse(dataEl.textContent);
  const msg = document.getElementById("su-msg");
  const text = document.getElementById("sudoku").dataset;
  const fill = (template, values) => template.replace(/\{(\w+)\}/g, (_, key) => values[key]);
  const tabs = [...document.querySelectorAll(".su-levels button")];
  let level = data.levels[0];
  let values = [];
  let selected = -1;

  const key = () => `sudoku:${data.date}:${level.slug}`;
  const load = () => {
    try {
      const saved = localStorage.getItem(key());
      if (saved && saved.length === 81) return saved.split("").map(Number);
    } catch (error) { /* brak dostępu do pamięci przeglądarki */ }
    return level.puzzle.split("").map(Number);
  };
  const save = () => {
    try { localStorage.setItem(key(), values.join("")); } catch (error) { /* jw. */ }
  };
  const given = (i) => level.puzzle[i] !== "0";

  const cells = [];
  for (let i = 0; i < 81; i += 1) {
    const cell = document.createElement("button");
    cell.type = "button";
    cell.className = "su-cell";
    cell.setAttribute("role", "gridcell");
    cell.addEventListener("click", () => select(i));
    board.append(cell);
    cells.push(cell);
  }

  function render() {
    const picked = selected >= 0 ? values[selected] : 0;
    cells.forEach((cell, i) => {
      const row = Math.floor(i / 9), col = i % 9;
      const sameUnit = selected >= 0 && (row === Math.floor(selected / 9) || col === selected % 9
        || (Math.floor(row / 3) === Math.floor(selected / 27) && Math.floor(col / 3) === Math.floor((selected % 9) / 3)));
      cell.textContent = values[i] || "";
      cell.classList.toggle("given", given(i));
      cell.classList.toggle("sel", i === selected);
      cell.classList.toggle("peer", sameUnit && i !== selected);
      cell.classList.toggle("same", picked > 0 && values[i] === picked && i !== selected);
      cell.setAttribute("aria-label", fill(text.cell, { r: row + 1, c: col + 1, v: values[i] || text.empty }));
    });
  }

  function clearMarks() {
    cells.forEach((cell) => cell.classList.remove("bad"));
    msg.textContent = "";
    msg.className = "su-msg";
  }

  function select(i) { selected = i; render(); }

  function put(n) {
    if (selected < 0 || given(selected)) return;
    values[selected] = n;
    clearMarks();
    save();
    render();
    if (values.join("") === level.solution) {
      msg.textContent = text.solved;
      msg.classList.add("ok");
    }
  }

  function setLevel(slug) {
    level = data.levels.find((item) => item.slug === slug) || data.levels[0];
    tabs.forEach((tab) => tab.setAttribute("aria-selected", String(tab.dataset.level === level.slug)));
    values = load();
    selected = -1;
    clearMarks();
    render();
  }

  tabs.forEach((tab) => tab.addEventListener("click", () => setLevel(tab.dataset.level)));
  document.getElementById("su-pad").addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (button) put(Number(button.dataset.n));
  });
  document.getElementById("su-check").addEventListener("click", () => {
    clearMarks();
    let wrong = 0, empty = 0;
    values.forEach((value, i) => {
      if (!value) { empty += 1; return; }
      if (String(value) !== level.solution[i]) { wrong += 1; cells[i].classList.add("bad"); }
    });
    if (wrong) { msg.textContent = fill(text.wrong, { n: wrong }); msg.classList.add("err"); }
    else if (empty) msg.textContent = fill(text.left, { n: empty });
    else { msg.textContent = text.solved; msg.classList.add("ok"); }
  });
  document.getElementById("su-reset").addEventListener("click", () => {
    values = level.puzzle.split("").map(Number);
    save();
    clearMarks();
    render();
  });
  document.addEventListener("keydown", (event) => {
    if (selected < 0 || event.target.closest("input, textarea")) return;
    if (/^[1-9]$/.test(event.key)) put(Number(event.key));
    else if (["Backspace", "Delete", "0"].includes(event.key)) put(0);
    else {
      const step = { ArrowUp: -9, ArrowDown: 9, ArrowLeft: -1, ArrowRight: 1 }[event.key];
      if (!step) return;
      const next = selected + step;
      if (next < 0 || next > 80 || (Math.abs(step) === 1 && Math.floor(next / 9) !== Math.floor(selected / 9))) return;
      select(next);
      cells[next].focus();
    }
    event.preventDefault();
  });

  setLevel(level.slug);
})();
