"""API de exemplo usada para exercitar a esteira DevSecOps."""
from itertools import count

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="DevSecOps Demo API",
    version="1.0.0",
    docs_url=None,  # Swagger UI desligado (menos superfície de ataque)
    redoc_url=None,
)

# CORS restrito: nada de allow_origins=["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.exemplo.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; frame-ancestors 'none'"
    )
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Cache-Control"] = "no-store"
    return response


class ItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    price: float = Field(gt=0, le=1_000_000)


class Item(ItemIn):
    id: int


_items: dict[int, Item] = {}
_ids = count(1)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/items")
def list_items() -> list[Item]:
    return list(_items.values())


@app.post("/items", status_code=201)
def create_item(payload: ItemIn) -> Item:
    item = Item(id=next(_ids), **payload.model_dump())
    _items[item.id] = item
    return item


@app.get("/items/{item_id}")
def get_item(item_id: int) -> Item:
    item = _items.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return item
