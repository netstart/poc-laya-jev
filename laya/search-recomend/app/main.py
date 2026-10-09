from contextlib import asynccontextmanager
import logging
import time
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings
from app.schemas import BuscarRequest, BuscarResponse, Producto
from app.search_engine import SearchEngine, keyword_search
from app.laya_engine import LayaEngine
from app.cache import get_cache
import json

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _laya, _productos, _search
    _laya = LayaEngine(checkpoint=settings.MODEL_CHECKPOINT, device=settings.MODEL_DEVICE)
    _productos = load_catalogo()
    _search = SearchEngine(_productos, _laya)
    logger.info("=" * 49)
    logger.info(" BUSCA QUE ENTENDE")
    logger.info("=" * 49)
    logger.info(f"Engine: LAYA")
    logger.info(f"Checkpoint: {settings.MODEL_CHECKPOINT}")
    logger.info(f"Device: {settings.MODEL_DEVICE}")
    logger.info(f"Catalogo: {len(_productos)} produtos")
    logger.info(f"Porta: {settings.PORT}")
    logger.info(f"Modo: LOCAL / OFFLINE")
    logger.info("=" * 49)
    yield


app = FastAPI(title="Busca que Entende", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:4111", "http://localhost:4111"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_laya: Optional[LayaEngine] = None
_productos: list[Producto] = []
_search: Optional[SearchEngine] = None


def load_catalogo() -> list[Producto]:
    path = Path(settings.CATALOGO_PATH)
    if not path.exists():
        raise FileNotFoundError(f"Catalogo not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Producto(**p) for p in data]


@app.get("/healthz")
async def healthz():
    return {
        "ok": True,
        "app": settings.APP_NAME,
        "engine": "laya",
        "model": settings.MODEL_CHECKPOINT,
        "device": settings.MODEL_DEVICE,
        "loaded": _laya is not None,
    }


@app.get("/api/catalogo")
async def get_catalogo():
    return [p.model_dump() for p in _productos]


@app.get("/api/exemplos")
async def get_exemplos():
    return [
        {"texto": "presente pra minha mãe que ama jardinagem até 150 reais", "emoji": "🌱"},
        {"texto": "acampar com criança no frio", "emoji": "🏕️"},
        {"texto": "meu cachorro destrói todos os brinquedos", "emoji": "🐶"},
        {"texto": "tenho insônia e acordo com qualquer barulho", "emoji": "😴"},
        {"texto": "amigo secreto da firma até 50 reais", "emoji": "🤫"},
        {"texto": "presente pra criança de 5 anos que ama dinossauro", "emoji": "🦖"},
        {"texto": "o carregador do meu celular quebrou", "emoji": "🔌"},
        {"texto": "gift for a coffee lover", "emoji": "☕"},
    ]


@app.get("/api/stats")
async def get_stats():
    cache = get_cache()
    return {"cache": cache.stats(), "productos": len(_productos)}


@app.post("/api/buscar", response_model=BuscarResponse)
async def buscar(req: BuscarRequest):
    if not req.q or len(req.q.strip()) < 2:
        raise HTTPException(status_code=400, detail={"codigo": "vazio", "mensagem": "Digite o que você procura (pelo menos 2 letras)."})
    if len(req.q) > 300:
        raise HTTPException(status_code=400, detail={"codigo": "longo", "mensagem": "Busca longa demais: use até 300 caracteres."})
    resultado = _search.buscar(req.q.strip(), fresh=req.fresh)
    return BuscarResponse(**resultado)


public_dir = Path(__file__).resolve().parent.parent / "public"
if public_dir.exists():
    app.mount("/", StaticFiles(directory=str(public_dir), html=True), name="public")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT, log_level="info")
