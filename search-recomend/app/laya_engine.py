import logging
import time
import unicodedata
from typing import Optional
from app.schemas import Producto, Entendimiento, ScoreProducto
from app.orcamento import parse_budget, bucket_budget

logger = logging.getLogger(__name__)


def _norm(text: str) -> str:
    return unicodedata.normalize("NFD", text.lower()).encode("ascii", "ignore").decode("ascii")


SYNONYM_MAP = {
    "gift": ["presente", "presentear", "presentinho", "present", "presente"],
    "present": ["presente", "presentear", "presentinho", "gift"],
    "coffee": ["cafe", "cafeteira", "cafezinho", "café", "cafe"],
    "cafe": ["coffee", "cafeteira", "cafezinho", "café"],
    "lover": ["amante", "fan", "apaixonado", "adorador"],
    "dog": ["cachorro", "cao", "pet", "canino"],
    "destroyer": ["destroi", "destrutivel", "resistente", "duro"],
    "toy": ["brinquedo", "brinquedos", "joguete"],
    "insomnia": ["insonia", "insone", "sono", "dormir"],
    "noise": ["barulho", "ruido", "som", "ruidoso"],
    "camping": ["camping", "acampar", "barraca", "fogueira"],
    "cold": ["frio", "inverno", "casaco", "aquentar"],
    "child": ["crianca", "filho", "filha", "kids", "kid"],
    "dinosaur": ["dinossauro", "dino", "jurassico"],
    "charger": ["carregador", "carregar", "energia", "bateria"],
    "broken": ["quebrou", "quebrado", "quebrada", "falhou"],
    "destroy": ["destroi", "destruir", "destrutivel", "indestrutivel"],
    "resistant": ["resistente", "duro", "resistencia", "indestrutivel"],
    "plant": ["planta", "plantas", "jardim", "jardinagem"],
    "garden": ["jardim", "jardinagem", "planta", "flor"],
    "kitchen": ["cozinha", "panela", "talheres", "cozinhar"],
    "pet": ["cachorro", "gato", "cao", "animal", "pet"],
    "cachorro": ["dog", "cao", "pet", "canino"],
    "gato": ["cat", "pet", "felino"],
    "book": ["livro", "leitura", "ler", "livros"],
    "music": ["musica", "som", "fone", "audio"],
    "study": ["estudo", "estudar", "escola", "aprender"],
    "travel": ["viagem", "viajar", "turismo", "passeio"],
    "sleep": ["sono", "dormir", "insonia", "descansar"],
    "massage": ["massagem", "massageador", "relaxar", "massagear"],
    "gift": ["presente", "presentear", "presentinho"],
}


def _expand_synonyms(tokens: set[str]) -> set[str]:
    expanded = set(tokens)
    for token in list(tokens):
        for key, syns in SYNONYM_MAP.items():
            if token == key or token in syns:
                expanded.add(key)
                expanded.update(syns)
    return expanded


def _simple_stem(word: str) -> str:
    suffixes = [
        "ando", "endo", "indo", "acao", "acoes", "mente",
        "inho", "inha", "ao", "oes", "mente", "mente",
        "mente", "ar", "er", "ir", "ado", "ido",
    ]
    for s in suffixes:
        if word.endswith(s) and len(word) > len(s) + 2:
            return word[: -len(s)]
    return word


def _tokenize(text: str) -> list[str]:
    norm = _norm(text)
    tokens = norm.split()
    stopwords = {
        "de", "a", "o", "que", "e", "do", "da", "em", "um", "para",
        "com", "nao", "uma", "os", "no", "se", "na", "por", "mais",
        "as", "dos", "como", "mas", "ao", "ele", "das", "seu", "sua",
        "ou", "quando", "muito", "nos", "ja", "eu", "tambem", "so",
        "pelo", "pela", "ate", "isso", "ela", "entre", "sem", "mesmo",
        "onde", "quem", "voc", "tem", "pra", "para", "the",
        "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "must", "shall", "can",
        "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after",
        "above", "below", "between", "out", "off", "over", "under",
        "again", "further", "then", "once", "here", "there", "when",
        "where", "why", "how", "all", "each", "every", "both",
        "few", "more", "most", "other", "some", "such", "no", "nor",
        "not", "only", "own", "same", "so", "than", "too", "very",
        "just", "because", "but", "and", "or", "if", "while", "about",
        "up", "it", "its", "this", "that", "these", "those", "i",
        "me", "my", "we", "our", "you", "your", "he", "him", "she",
        "her", "they", "them", "what", "which", "who", "whom",
    }
    return [t for t in tokens if t not in stopwords and len(t) > 1]


INTENT_KEYWORDS = {
    "presente": [
        "presente", "presentear", "presentinho", "gift", "present",
        "presentar", "presentear", "presenteando", "presentes",
    ],
    "reposicao": [
        "repor", "rep", "quebrou", "quebrado", "perdi", "broken",
        "quebrada", "falhou", "preciso substituir", "preciso repor",
        "novo", "substituir",
    ],
    "pesquisa": [
        "pesquisar", "comparar", "ver opcoes", "procurando",
        "research", "compare", "procurar", "buscar", "encontrar",
    ],
}


CAT_KEYWORDS = {
    "jardim": [
        "jardim", "jardinagem", "planta", "flor", "vaso", "terra",
        "regar", "garden", "plants", "jardinar", "suculenta",
    ],
    "casa": [
        "casa", "moveis", "decoracao", "quadro", "almofada",
        "cortina", "home", "decor", "moveis", "luminaria",
    ],
    "cozinha": [
        "cozinha", "panela", "fogao", "talheres", "prato", "copo",
        "caf", "kitchen", "coffee", "cafe", "cafeteira", "cozinhar",
    ],
    "eletronicos": [
        "eletronico", "celular", "carregador", "fone", "tablet",
        "notebook", "computador", "eletronicos", "tech", "gadget",
    ],
    "esporte": [
        "esporte", "futebol", "bike", "bicicleta", "academia",
        "corrida", "sports", "esportivo", "trilha", "caminhada",
    ],
    "camping": [
        "camping", "acampar", "barraca", "cobra", "fogueira",
        "mochila", "acampamento", "outdoor",
    ],
    "moda": [
        "roupa", "calcado", "sapato", "camisa", "vestido", "moda",
        "fashion", "calcados", "vestuario",
    ],
    "beleza": [
        "beleza", "perfume", "maquiagem", "creme", "rosto",
        "skincare", "beauty", "cosmetico",
    ],
    "pet": [
        "cachorro", "gato", "pet", "cao", "brinquedo para cachorro",
        "racao", "dog", "cat", "animal", "animais",
    ],
    "brinquedos": [
        "brinquedo", "crianca", "infantil", "boneca", "carrinho",
        "dinossauro", "toy", "brincar", "kids",
    ],
    "livros": [
        "livro", "leitura", "romance", "historia", "book",
        "ler", "leitor", "e-reader",
    ],
    "papelaria": [
        "caneta", "caderno", "papel", "escrita", "stationery",
        "escritorio", "pincel",
    ],
    "bem_estar": [
        "massagem", "relaxar", "insonia", "sono", "bem estar",
        "saude", "wellness", "meditacao", "relaxamento",
    ],
}


DEST_KEYWORDS = {
    "mae": ["mae", "mamae", "minha mae", "mother", "mom", "mama"],
    "pai": ["pai", "papai", "father", "dad", "papa"],
    "avos": ["avo", "avoh", "vov", "grandparent", "grandma", "grandpa"],
    "parceiro": [
        "namorado", "namorada", "esposo", "esposa", "parceiro",
        "marido", "mulher", "partner", "boyfriend", "girlfriend",
        "husband", "wife",
    ],
    "crianca": [
        "crianca", "filho", "filha", "sobrinho", "sobrinha",
        "menino", "menina", "child", "kid", "children",
    ],
    "bebe": ["bebe", "bebezinho", "nenem", "baby", "infant"],
    "adolescente": [
        "adolescente", "jovem", "teen", "teenager", "jovens",
    ],
    "amigo": [
        "amigo", "amiga", "colega", "amigo secreto", "friend",
        "amiga secreta",
    ],
    "pet": [
        "cachorro", "gato", "pet", "cao", "dog", "cat", "animal",
    ],
    "eu_mesmo": [
        "eu", "minha", "meu", "minhas", "meus", "myself", "my",
    ],
    "familia": [
        "familia", "irmao", "irma", "primo", "prima", "family",
        "irmaos", "irmao",
    ],
}


OCASION_KEYWORDS = {
    "aniversario": ["aniversario", "birthday", "anniversario"],
    "dia_das_maes": ["dia das maes", "maes", "mothers day", "mae"],
    "dia_dos_pais": ["dia dos pais", "pais", "fathers day", "pai"],
    "natal": ["natal", "natalino", "christmas", "xmas"],
    "amigo_secreto": ["amigo secreto", "amigo oculto", "secret santa"],
    "dia_dos_namorados": [
        "dia dos namorados", "namorados", "valentines", "valentine",
    ],
    "dia_das_criancas": ["dia das criancas", "criancas", "childrens day"],
    "viagem": ["viagem", "acampar", "trip", "travel", "viajar"],
}


class LayaEngine:
    def __init__(self, checkpoint: str = "laya-multilingual", device: str = "cpu"):
        self.checkpoint = checkpoint
        self.device = device
        self._model = None
        self._load_model()

    def _load_model(self) -> None:
        try:
            import laya
            self._model = laya.load(self.checkpoint, device=self.device)
            logger.info("LAYA loaded from package")
        except Exception as e:
            logger.warning(f"LAYA package not available, using local simulation: {e}")
            self._model = None

    def understand_query(self, query: str) -> Entendimiento:
        if self._model is not None:
            return self._understand_query_real(query)
        return self._understand_query_sim(query)

    def _understand_query_sim(self, query: str) -> Entendimiento:
        q = _norm(query)
        q_tokens = set(_tokenize(query))
        q_syns = _expand_synonyms(q_tokens)
        q_all = q_tokens | q_syns
        q_text = " ".join(sorted(q_all))
        q_wordset = set(q_all)

        intencao = "uso_proprio"
        for intent, keywords in INTENT_KEYWORDS.items():
            if any(w in q_wordset for w in keywords):
                intencao = intent
                break

        categoria = "varias"
        for cat, keywords in CAT_KEYWORDS.items():
            if any(w in q_wordset for w in keywords):
                categoria = cat
                break

        destinatario = "no_informado"
        for dest, keywords in DEST_KEYWORDS.items():
            if any(w in q_wordset for w in keywords):
                destinatario = dest
                break

        ocasion = "nenhuma"
        for occ, keywords in OCASION_KEYWORDS.items():
            if any(w in q_wordset for w in keywords):
                ocasion = occ
                break

        orcamento_max, orcamento_fonte = parse_budget(query)

        return Entendimiento(
            intencion=intencao,
            categoria=categoria,
            destinatario=destinatario,
            ocasion=ocasion,
            orcamento_max=orcamento_max,
            orcamento_fonte=orcamento_fonte,
            confianca=0.8,
            bruto={"method": "sim", "query": query, "tokens": sorted(q_tokens)},
        )

    def score_products(self, query: str, productos: list[Producto]) -> list[ScoreProducto]:
        if self._model is not None:
            return self._score_products_real(query, productos)
        return self._score_products_sim(query, productos)

    def _score_products_sim(self, query: str, productos: list[Producto]) -> list[ScoreProducto]:
        q_tokens = set(_tokenize(query))
        q_syns = _expand_synonyms(q_tokens)
        q_all = q_tokens | q_syns
        q_stems = {_simple_stem(t) for t in q_all}
        q_wordset = set(q_all)

        cat_matches = set()
        recip_matches = set()
        for cat, keywords in CAT_KEYWORDS.items():
            if any(w in q_wordset for w in keywords):
                cat_matches.add(cat)
        for dest, keywords in DEST_KEYWORDS.items():
            if any(w in q_wordset for w in keywords):
                recip_matches.add(dest)

        results = []
        for p in productos:
            p_text = _norm(f"{p.nombre} {p.descripcion} {' '.join(p.tags)}")
            p_tokens = set(_tokenize(p_text))
            p_syns = _expand_synonyms(p_tokens)
            p_all = p_tokens | p_syns
            p_stems = {_simple_stem(t) for t in p_all}
            p_tagset = {_norm(t) for t in p.tags}

            score = 0.0
            word_match = len(q_tokens & p_tokens)
            score += word_match * 0.5

            syn_match = len(q_syns & p_all)
            score += syn_match * 0.4

            stem_match = len(q_stems & p_stems)
            score += stem_match * 0.3

            if p.categoria in cat_matches or p.departamento in cat_matches:
                score += 1.0

            if p.publico in recip_matches:
                score += 0.5

            tag_match = len(q_wordset & p_tagset)
            score += tag_match * 0.5

            score = min(3.0, max(0.0, score))

            if score < 1.0 and (word_match > 0 or syn_match > 0 or p.categoria in cat_matches):
                score = 1.0

            if score == 0.0 and p.categoria in cat_matches:
                score = 0.5

            probs = {"0": max(0.0, 1.0 - score / 3.0), "1": max(0.0, score * 0.3), "2": max(0.0, score * 0.3), "3": max(0.0, score * 0.4)}
            total = sum(probs.values())
            if total > 0:
                probs = {k: round(v / total, 2) for k, v in probs.items()}

            confidence = round(min(score / 3.0, 1.0), 2)
            results.append(ScoreProducto(producto_id=p.id, score=round(score, 2), probabilities=probs, confidence=confidence))
        return results

    def _understand_query_real(self, query: str) -> Entendimiento:
        try:
            state = {"query": query}
            questions = [
                {"type": "choice", "id": "intencion", "options": ["presente", "uso_proprio", "reposicao", "pesquisa"]},
                {"type": "choice", "id": "categoria", "options": ["casa", "jardim", "cozinha", "eletronicos", "esporte", "camping", "moda", "beleza", "pet", "brinquedos", "livros", "papelaria", "bem_estar", "varias"]},
                {"type": "choice", "id": "destinatario", "options": ["mae", "pai", "avos", "parceiro", "crianca", "bebe", "adolescente", "amigo", "pet", "eu_mesmo", "familia", "no_informado"]},
                {"type": "choice", "id": "ocasion", "options": ["aniversario", "dia_das_maes", "dia_dos_pais", "natal", "amigo_secreto", "dia_dos_namorados", "dia_das_criancas", "viagem", "nenhuma"]},
                {"type": "choice", "id": "orcamento", "options": ["sem_limite", "barato", "ate_50", "ate_100", "ate_150", "ate_200", "ate_300", "ate_500", "ate_1000", "premium"]},
            ]
            decisions = self._model.decide(state, questions)
            intencion = decisions.get("intencion", {}).get("choice", "uso_proprio")
            categoria = decisions.get("categoria", {}).get("choice", "varias")
            destinatario = decisions.get("destinatario", {}).get("choice", "no_informado")
            ocasion = decisions.get("ocasion", {}).get("choice", "nenhuma")
            orcamento_max, orcamento_fonte = parse_budget(query)
            return Entendimiento(intencion=intencion, categoria=categoria, destinatario=destinatario, ocasion=ocasion, orcamento_max=orcamento_max, orcamento_fonte=orcamento_fonte, confianca=0.9, bruto=decisions)
        except Exception as e:
            logger.error(f"LAYA real query failed: {e}")
            return self._understand_query_sim(query)

    def _score_products_real(self, query: str, productos: list[Producto]) -> list[ScoreProducto]:
        try:
            batch = []
            for p in productos:
                batch.append({"type": "score", "state": {"query": query, "producto": p.nombre, "descripcion": p.descripcion}, "question": f"Quao bem o produto {p.nombre} atende ao pedido do cliente?"})
            answers = self._model.decide_batch(batch)
            results = []
            for i, p in enumerate(productos):
                ans = answers[i] if i < len(answers) else {}
                score = float(ans.get("score", 0.0))
                results.append(ScoreProducto(producto_id=p.id, score=round(score, 2), probabilities=ans.get("probabilities", {}), confidence=round(ans.get("confidence", 0.0), 2)))
            return results
        except Exception as e:
            logger.error(f"LAYA real scoring failed: {e}")
            return self._score_products_sim(query, productos)
