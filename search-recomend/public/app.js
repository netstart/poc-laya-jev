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
  renderSidebarCatalog();
  document.body.classList.add("catalog-open");
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

function createTile(producto, source, rank, level = 0) {
  const div = document.createElement("div");
  div.className = `tile lv${level} ${source}`;
  div.id = `tile-${source}-${producto.id}`;
  const sourceLabels = {
    "source-both": "Encontrado em ambos",
    "source-keyword": "Encontrado apenas na busca tradicional",
    "source-laya": "Encontrado apenas na busca com LAYA"
  };
  div.title = sourceLabels[source] || "";
  let html = `<div class="tile-id">${producto.id}</div>`;
  html += `<div class="tile-nome">${producto.nombre}</div>`;
  html += `<div class="tile-preco">R$ ${producto.precio.toFixed(2)}</div>`;
  if (rank) {
    html += `<div class="tile-badge">${rank}</div>`;
  }
  div.innerHTML = html;
  return div;
}

function createNeutralTile(producto) {
  const div = document.createElement("div");
  div.className = "tile";
  div.title = "";
  div.id = `tile-sidebar-${producto.id}`;
  let html = `<div class="tile-id">${producto.id}</div>`;
  html += `<div class="tile-nome">${producto.nombre}</div>`;
  html += `<div class="tile-preco">R$ ${producto.precio.toFixed(2)}</div>`;
  div.innerHTML = html;
  return div;
}

function renderSidebarCatalog() {
  const content = document.getElementById("catalogSidebarContent");
  const sub = document.getElementById("catalogSidebarSub");
  if (!content) return;
  if (sub) sub.textContent = `${catalogo.length} artigos`;
  content.innerHTML = "";
  const categories = {};
  catalogo.forEach(p => {
    if (!categories[p.categoria]) categories[p.categoria] = [];
    categories[p.categoria].push(p);
  });
  Object.keys(categories).sort().forEach(cat => {
    const group = document.createElement("div");
    group.className = "categoria-group";
    const title = document.createElement("div");
    title.className = "categoria-title";
    title.textContent = cat;
    group.appendChild(title);
    const grid = document.createElement("div");
    grid.className = "grid";
    categories[cat].forEach(p => {
      grid.appendChild(createNeutralTile(p));
    });
    group.appendChild(grid);
    content.appendChild(group);
  });
}

async function doSearch(q) {
  currentQuery = q;
  const resultados = document.getElementById("resultados");
  resultados.style.display = "block";
  resultados.scrollIntoView({ behavior: "smooth", block: "start" });

  const gridKeyword = document.getElementById("grid-keyword");
  const gridLaya = document.getElementById("grid-laya");
  gridKeyword.innerHTML = "";
  gridLaya.innerHTML = "";
  document.getElementById("footer").innerHTML = "";

  const keywordIds = ks.search(q, 20);
  const balcao1 = document.getElementById("balcao1Num");
  balcao1.textContent = keywordIds.length > 0 ? `${keywordIds.length} resultados` : "0 resultados";

  const keywordProducts = keywordIds.map(id => catalogo.find(p => p.id === id)).filter(Boolean);
  const keywordIdSet = new Set(keywordIds);

  keywordProducts.forEach((p, idx) => {
    const tile = createTile(p, "source-keyword", idx + 1, 0);
    gridKeyword.appendChild(tile);
  });

  try {
    const res = await fetch(`${API}/api/buscar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ q, fresh: false }),
    });
    const data = await res.json();
    if (data.q !== currentQuery) return;
    if (!data.ok) {
      document.getElementById("footer").innerHTML = `<div class="nada-serve">${JSON.stringify(data)}</div>`;
      return;
    }
    currentLayaResult = data;

    const scores = data.scores || {};
    const ordem = data.ordem || [];
    const entendimento = data.entendimiento || {};
    const orcamentoMax = entendimento.orcamento_max;

    const within = ordem.filter(id => {
      const p = catalogo.find(x => x.id === id);
      return p && (orcamentoMax == null || p.precio <= orcamentoMax);
    });
    const good = within.filter(id => (scores[id] ? scores[id][0] : 0) >= 2);
    document.getElementById("balcao2Num").textContent = `${Math.max(0, good.length)} boas opções`;

    const bothIds = new Set(ordem.filter(id => keywordIdSet.has(id)));

    bothIds.forEach(id => {
      const tile = document.getElementById(`tile-source-keyword-${id}`);
      if (tile) {
        tile.classList.add("source-both");
        tile.classList.remove("source-keyword");
      }
    });

    const top = within.slice(0, 8);
    top.forEach((id, idx) => {
      const p = catalogo.find(x => x.id === id);
      if (!p) return;
      const s = scores[id] ? scores[id][0] : 0;
      const lv = Math.max(0, Math.min(3, Math.round(s)));
      const source = bothIds.has(id) ? "source-both" : "source-laya";
      const tile = createTile(p, source, idx < 5 ? idx + 1 : null, lv);
      gridLaya.appendChild(tile);
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

    renderInspector(data, keywordIds);
  } catch (e) {
    document.getElementById("footer").innerHTML = `<div class="nada-serve">Erro na busca: ${e.message}</div>`;
  }
}

function renderInspector(data, keywordIds) {
  const body = document.getElementById("inspectorBody");
  body.innerHTML = `
    <div class="inspector-section"><h4>Estado</h4><pre>${JSON.stringify({ pedido_do_cliente: data.q }, null, 2)}</pre></div>
    <div class="inspector-section"><h4>Busca Tradicional</h4><pre>resultados: ${keywordIds.length}\nids: [${keywordIds.slice(0, 10).join(", ")}${keywordIds.length > 10 ? "..." : ""}]</pre></div>
    <div class="inspector-section"><h4>Entendimento LAYA</h4><pre>${JSON.stringify(data.entendimiento, null, 2)}</pre></div>
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
