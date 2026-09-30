# Modelo LAYA

## Checkpoint

```
laya-multilingual
```

## Instalação

```bash
pip install laya
python scripts/setup_model.py
```

## Dispositivo

O modelo roda em:

- CPU (fallback obrigatório)
- NVIDIA CUDA (se disponível)
- Apple Silicon (se suportado pelo runtime)

## Uso

O modelo é carregado uma única vez na inicialização e reutilizado por todas as requisições.

## Offline

Depois do download inicial, o modelo funciona sem internet.

## Trocando o modelo

Edite `app/config.py`:

```python
MODEL_CHECKPOINT: str = "outro-checkpoint"
```
