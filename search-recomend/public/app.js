const API = "http://127.0.0.1:4111";
let ks = null;
let catalogo = [];
let debounceTimer = null;
let currentQuery = "";
let currentLayaResult = null;

async function init() {
  const [catRes, exRes] = await Promise.all([
    fetch(`${API}/api/catalogo`),
    fetch(`${API}/api/exemplos`),
  ]);
  catalogo = await catRes.json();
  const exemplos = await exRes.json();
  const list = document.getElementById("exemplosList");
  exemplos.forEach(ex => {
    const btn = document.createElement("div");
    btn.className = "exemplo-chip";
    btn.innerHTML = `<span>${ex.emoji}</span><span>${ex.texto}</span>`;
    btn.onclick = () => {
      document.getElementById("q").value = ex.texto;
      doSearch(ex.texto);
    };
    list.appendChild(btn);
  });
  ks = new KeywordSearch(catalogo);
}

function debounce(fn, ms) {
  return (...args) => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => fn(...args), ms);
  };
}

const debouncedSearch = debounce(q => doSearch(q), 550);

document.getElementById("searchForm").addEventListener("submit", e => {
  e.preventDefault();
  const q = document.getElementById("q").value.trim();
  if (q.length >= 2) doSearch(q);
});

document.getElementById("q").addEventListener("input", e => {
  const q = e.target.value.trim();
  if (q.length >= 3) debouncedSearch(q);
});

async function doSearch(q) {
  currentQuery = q;
  const resultados = document.getElementById("resultados");
  resultados.style.display = "block";
  resultados.scrollIntoView({ behavior: "smooth", block: "start" });
  const grid = document.getElementById("grid");
  grid.innerHTML = "";
  document.getElementById("footer").innerHTML = "";

  const tiles = catalogo.map(p => {
    const div = document.createElement("div");
    div.className = "tile lv0";
    div.id = `tile-${p.id}`;
    div.innerHTML = `<div class="tile-id">${p.id}</div><div class="tile-nome">${p.nombre}</div><div class="tile-preco">R$ ${p.precio.toFixed(2)}</div>`;
    grid.appendChild(div);
    return div;
  });

  try {
    const res = await fetch(`${API}/api/buscar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ q, fresh: false }),
    });
    const data = await res.json();
    if (!data.ok) {
      document.getElementById("footer").innerHTML = `<div class="nada-serve">${JSON.stringify(data)}</div>`;
      return;
    }
    currentLayaResult = data;
    renderLaya(data);
    renderKeyword(q);
    renderInspector(data);
  } catch (e) {
    document.getElementById("footer").innerHTML = `<div class="nada-serve">Erro na busca: ${e.message}</div>`;
  }
}

function renderKeyword(q) {
  const ids = ks.search(q, 20);
  const balcao1 = document.getElementById("balcao1Num");
  if (ids.length === 0) {
    balcao1.textContent = "0 resultados";
  } else {
    balcao1.textContent = `${ids.length} resultados`;
  }
  ids.forEach((id, idx) => {
    const tile = document.getElementById(`tile-${id}`);
    if (tile) {
      tile.classList.add("hot");
      const badge = document.createElement("div");
      badge.className = "tile-badge";
      badge.textContent = idx + 1;
      tile.appendChild(badge);
    }
  });
}

function renderLaya(data) {
  const scores = data.scores || {};
  const ordem = data.ordem || [];
  const entendimento = data.entendimiento || {};
  const orcamentoMax = entendimento.orcamento_max;

  const within = ordem.filter(id => {
    const p = catalogo.find(x => x.id === id);
    return p && (orcamentoMax == null || p.precio <= orcamentoMax);
  });
  const top = within.slice(0, 8);
  const good = within.filter(id => (scores[id] ? scores[id][0] : 0) >= 2);
  document.getElementById("balcao2Num").textContent = `${Math.max(0, good.length)} boas opções`;

  top.forEach((id, idx) => {
    const tile = document.getElementById(`tile-${id}`);
    if (!tile) return;
    const s = scores[id] ? scores[id][0] : 0;
    const lv = Math.max(0, Math.min(3, Math.round(s)));
    tile.className = `tile lv${lv}`;
    if (idx < 5) {
      const badge = document.createElement("div");
      badge.className = "tile-badge";
      badge.textContent = idx + 1;
      tile.appendChild(badge);
    }
    if (orcamentoMax != null && catalogo.find(x => x.id === id)?.precio > orcamentoMax) {
      tile.classList.add("over");
    }
  });

  const over = ordem.filter(id => {
    const p = catalogo.find(x => x.id === id);
    return p && orcamentoMax != null && p.precio > orcamentoMax && (scores[id] ? scores[id][0] : 0) >= 1.5;
  }).slice(0, 3);

  let footer = document.getElementById("footer");
  if (over.length > 0 && orcamentoMax != null) {
    footer.innerHTML = `<div class="over-budget"><div class="over-budget-titulo">Também combinam, mas passam de R$ ${orcamentoMax.toFixed(2)}:</div>` +
      over.map(id => {
        const p = catalogo.find(x => x.id === id);
        return p ? `<div class="over-budget-item"><span>${p.nombre}</span><span>R$ ${p.precio.toFixed(2)}</span></div>` : "";
      }).join("") + `</div>`;
  }

  if (within.length > 0 && good.length === 0) {
    footer.innerHTML = `<div class="nada-serve">Nada no catálogo atende bem a este pedido. O LAYA prefere dizer isso a empurrar qualquer coisa — abaixo, o que chega mais perto.</div>`;
  }
}

function renderInspector(data) {
  const body = document.getElementById("inspectorBody");
  body.innerHTML = `
    <div class="inspector-section"><h4>Estado</h4><pre>${JSON.stringify({ pedido_do_cliente: data.q }, null, 2)}</pre></div>
    <div class="inspector-section"><h4>Entendimento</h4><pre>${JSON.stringify(data.entendimiento, null, 2)}</pre></div>
    <div class="inspector-section"><h4>Métricas</h4><pre>latency: ${data.latency_ms}ms\nchamadas: ${data.n_chamadas}\nperguntas: ${data.n_perguntas}</pre></div>
  `;
}

document.getElementById("inspectorBtn").addEventListener("click", () => {
  const el = document.getElementById("inspector");
  el.style.display = el.style.display === "none" ? "block" : "none";
});

document.getElementById("inspectorClose").addEventListener("click", () => {
  document.getElementById("inspector").style.display = "none";
});

init();
