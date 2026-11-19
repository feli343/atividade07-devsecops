#!/usr/bin/env python3
"""DAST leve: dispara requisições HTTP contra a API em execução.

Verifica cabeçalhos de segurança, comportamento de erro e CORS.
Sai com código 1 se qualquer verificação falhar (Security Gate).
Uso: python scripts/dast_check.py http://localhost:8000
"""
import json
import sys
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")

REQUIRED_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "content-security-policy": None,
    "strict-transport-security": None,
    "referrer-policy": None,
}

failures: list[str] = []


def call(method, path, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, {k.lower(): v for k, v in resp.headers.items()}, resp.read()
    except urllib.error.HTTPError as err:
        return err.code, {k.lower(): v for k, v in err.headers.items()}, err.read()


def check(ok: bool, label: str):
    print(("[ OK ] " if ok else "[FAIL] ") + label)
    if not ok:
        failures.append(label)


# 1. Cabeçalhos de segurança em endpoints diferentes (inclusive 404)
for path in ("/health", "/items", "/rota-inexistente"):
    _, headers, _ = call("GET", path)
    for name, expected in REQUIRED_HEADERS.items():
        value = headers.get(name)
        good = value is not None and (expected is None or value == expected)
        check(good, f"{path}: cabeçalho {name}")

# 2. Não vazar informação de servidor/stack trace
status, headers, body = call("GET", "/items/abc")
check(status == 422, "ID inválido retorna 422 (validação) e não 500")
check(b"Traceback" not in body, "resposta de erro sem stack trace")

# 3. Entrada maliciosa é rejeitada
status, _, _ = call("POST", "/items", {"name": "<script>" * 50, "price": 1})
check(status == 422, "payload com nome gigante rejeitado (422)")
status, _, _ = call("POST", "/items", {"name": "x", "price": -5})
check(status == 422, "preço negativo rejeitado (422)")

# 4. Swagger/Docs não expostos em produção
status, _, _ = call("GET", "/docs")
check(status == 404, "/docs desativado")

# 5. CORS não pode refletir origem arbitrária
_, headers, _ = call("GET", "/health", headers={"Origin": "https://evil.example"})
check(headers.get("access-control-allow-origin") not in ("*", "https://evil.example"),
      "CORS não libera origem arbitrária")

# 6. Fluxo feliz continua funcionando
status, _, _ = call("POST", "/items", {"name": "ok", "price": 9.9})
check(status == 201, "POST /items válido retorna 201")

print()
if failures:
    print(f"DAST FALHOU: {len(failures)} verificação(ões) reprovada(s).")
    sys.exit(1)
print("DAST OK: todas as verificações passaram.")
