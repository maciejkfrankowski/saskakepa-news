(() => {
  const root = document.body.dataset.root || "";

  // Data w nagłówku
  const today = document.getElementById("today");
  if (today) {
    const locale = { pl: "pl-PL", de: "de-DE" }[document.documentElement.lang] || "pl-PL";
    const text = new Date().toLocaleDateString(locale, { weekday: "long", day: "numeric", month: "long", year: "numeric" });
    today.textContent = text.charAt(0).toUpperCase() + text.slice(1);
  }

  // Pogoda (Open-Meteo, bez klucza); przy błędzie element zostaje ukryty
  const weather = document.getElementById("weather");
  const { lat, lon } = document.body.dataset;
  if (weather && lat && lon) {
    fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((data) => {
        weather.textContent = `${Math.round(data.current.temperature_2m)}°C`;
        weather.hidden = false;
      })
      .catch(() => {});
  }

  // Wyszukiwarka po search.json (ładowany przy pierwszym użyciu)
  const input = document.getElementById("q");
  const box = document.getElementById("results");
  let index = null;
  const norm = (s) => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/ł/g, "l");

  const show = () => {
    const query = norm(input.value.trim());
    box.replaceChildren();
    if (query.length < 2 || !index) { box.hidden = true; return; }
    const hits = index.filter((e) => norm(`${e.t} ${e.l}`).includes(query)).slice(0, 8);
    if (!hits.length) {
      const empty = document.createElement("p");
      empty.textContent = document.body.dataset.noResults || "—";
      box.append(empty);
    }
    for (const hit of hits) {
      const link = document.createElement("a");
      link.href = hit.x ? hit.u : root + hit.u;
      if (hit.x) { link.target = "_blank"; link.rel = "noopener"; }
      const title = document.createElement("strong");
      title.textContent = hit.t;
      const meta = document.createElement("small");
      meta.textContent = `${hit.d} · ${hit.s}`;
      link.append(title, meta);
      box.append(link);
    }
    box.hidden = false;
  };

  if (input && box) {
    input.addEventListener("input", () => {
      if (index) return show();
      fetch(`${root}search.json`).then((r) => r.json()).then((data) => { index = data; show(); }).catch(() => {});
    });
    document.addEventListener("click", (event) => {
      if (!event.target.closest(".tools")) box.hidden = true;
    });
  }
})();
