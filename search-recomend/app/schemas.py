from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class Producto(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    nombre: str
    precio: float
    categoria: str
    publico: str
    departamento: str
    descripcion: str
    tags: list[str] = []
    imagen: Optional[str] = None


class Entendimiento(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    intencion: str = "no_informado"
    categoria: str = "no_informado"
    destinatario: str = "no_informado"
    ocasion: str = "nenhuma"
    orcamento_max: Optional[float] = None
    orcamento_fonte: str = "no_detectado"
    confianca: float = 0.0
    bruto: dict = {}


class ScoreProducto(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    producto_id: str
    score: float
    probabilities: dict[str, float]
    confidence: float


class BuscarRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    q: str = Field(...)
    fresh: bool = False


class BuscarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    ok: bool
    q: str
    cached: bool
    entendimiento: Entendimiento
    scores: dict[str, list[float]]
    ordem: list[str]
    lotes: list[list[str]]
    latency_ms: int
    laya_ms: int
    n_produtos: int
    n_chamadas: int
    n_perguntas: int
    parcial: Optional[dict] = None
    _laya: list[dict] = []
