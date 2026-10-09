const STOPWORDS = new Set(["de","a","o","que","e","do","da","em","um","para","com","nao","uma","os","no","se","na","por","mais","as","dos","como","mas","ao","ele","das","do","seu","sua","ou","quando","muito","nos","ja","eu","tambem","so","pelo","pela","ate","isso","ela","entre","sem","mesmo","seu","sua","onde","quem","voc","tem","mae","pra","para"]);

const SYNONYMS = {
  "presente": ["presente","presentear","presentinho","gift"],
  "quebrou": ["quebrou","quebrado","quebrada","falhou"],
  "destroi": ["destroi","destruidor","destrutivel","indestrutivel"],
  "insonia": ["insonia","insone","barulho","ruido","acordo"],
  "jardim": ["jardim","jardinagem","planta","flor","vaso","terra","regar"],
  "cafe": ["cafe","cafeteira","cafezinho","café"],
  "carregador": ["carregador","carregar","energia","bateria"],
  "frio": ["frio","inverno","casaco","aquentar","faca"],
  "crianca": ["crianca","criancas","filho","filha","kids"],
  "pet": ["pet","cachorro","cao","gato","animal"],
  "dinossauro": ["dinossauro","dino","jurassico"],
};

function normalize(text) {
  return text.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^\w\s]/g, " ").replace(/\s+/g, " ").trim();
}

function tokenize(text) {
  const norm = normalize(text);
  return norm.split(" ").filter(t => t.length > 1 && !STOPWORDS.has(t));
}

function expandSynonyms(tokens) {
  const expanded = new Set(tokens);
  for (const token of tokens) {
    for (const [key, syns] of Object.entries(SYNONYMS)) {
      if (syns.includes(token) || token === key) {
        syns.forEach(s => expanded.add(s));
        expanded.add(key);
      }
    }
  }
  return Array.from(expanded);
}

function simpleStem(word) {
  const suffixes = ["ando","endo","indo","acao","oes","mente","inho","inha","ao","oes"];
  for (const s of suffixes) {
    if (word.endsWith(s) && word.length > s.length + 2) {
      return word.slice(0, -s.length);
    }
  }
  return word;
}

function KeywordSearch(catalogo) {
  this.docs = catalogo.map(p => ({
    id: p.id,
    text: normalize([p.nombre, p.descripcion, p.tags.join(" "), p.categoria, p.departamento, p.publico].join(" ")),
    tokens: tokenize([p.nombre, p.descripcion, p.tags.join(" "), p.categoria, p.departamento, p.publico].join(" ")).map(simpleStem),
    precio: p.precio,
  }));
  this.idf = {};
  this.computeIdf();
}

KeywordSearch.prototype.computeIdf = function() {
  const N = this.docs.length;
  const df = {};
  for (const doc of this.docs) {
    const seen = new Set(doc.tokens);
    for (const t of seen) {
      df[t] = (df[t] || 0) + 1;
    }
  }
  for (const t in df) {
    this.idf[t] = Math.log((N + 1) / (df[t] + 1)) + 1;
  }
};

KeywordSearch.prototype.highlight = function(text, queryTokens) {
  let result = text;
  const norm = normalize(text);
  for (const tok of queryTokens) {
    const regex = new RegExp("(" + tok.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "gi");
    result = result.replace(regex, '<mark>$1</mark>');
  }
  return result;
};

KeywordSearch.prototype.search = function(query, topK = 20) {
  const tokens = expandSynonyms(tokenize(query)).map(simpleStem);
  if (tokens.length === 0) return [];
  const scored = this.docs.map(doc => {
    let score = 0;
    const terms = new Set(tokens);
    for (const t of terms) {
      const tf = doc.tokens.filter(x => x === t).length;
      const idf = this.idf[t] || 1;
      score += tf * idf;
    }
    return { id: doc.id, score, precio: doc.precio };
  });
  scored.sort((a, b) => b.score - a.score || a.precio - b.precio);
  return scored.filter(s => s.score > 0).slice(0, topK).map(s => s.id);
};

if (typeof module !== "undefined") {
  module.exports = { KeywordSearch, tokenize, expandSynonyms, simpleStem, normalize };
}
