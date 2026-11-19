# DevSecOps Pipeline — API FastAPI com esteira de segurança

Projeto da **Atividade 07 – Pipeline CI/CD de Segurança** (Segurança em Desenvolvimento de Sistemas).
A API é propositalmente simples; o foco é a esteira em `.github/workflows/devsecops.yml`.

## Etapas da esteira

| # | Job | Ferramenta | O que bloqueia (Security Gate) |
|---|-----|-----------|--------------------------------|
| 1 | Secret Scanning | Gitleaks | qualquer senha/token/chave no código |
| 2 | SAST | Semgrep | achados de severidade ERROR (SQLi, `eval`, CORS `*`...) |
| 3 | SCA + SBOM | Trivy | CVE HIGH/CRITICAL em dependências; gera SBOM CycloneDX |
| 4 | Docker + IaC | Hadolint + Checkov | `USER root`, pod privilegiado, más práticas no Dockerfile/K8s |
| 5 | Testes | pytest | teste falhando |
| 6 | Build + scan da imagem | Trivy image | CVE HIGH/CRITICAL na imagem final; processo rodando como root |
| 7 | DAST | `scripts/dast_check.py` + OWASP ZAP | cabeçalhos ausentes, validação fraca, CORS aberto |
| 8 | Deploy | GHCR | só roda na `main`, depois de todos os gates |

Os jobs 1–5 rodam em paralelo; 6 → 7 → 8 só começam se os anteriores passarem.
Gatilhos: `push`, `pull_request` e execução manual.

## Estrutura

```
app/                  código da API (FastAPI)
tests/                testes unitários
Dockerfile            multi-stage, usuário não-root, HEALTHCHECK
k8s/deployment.yaml   IaC: Deployment endurecido, Service, NetworkPolicy
.semgrep/rules.yml    regras SAST do projeto
.gitleaks.toml        regras de secret scanning
scripts/dast_check.py DAST: requisições HTTP contra a API em execução
scripts/demo.sh       injeta/remove falhas controladas para a demonstração
.github/workflows/    pipeline
```

## Rodar localmente

```bash
pip install -r requirements-dev.txt
python -m pytest -q
uvicorn app.main:app --port 8000
python scripts/dast_check.py http://localhost:8000
```

## Demonstração do Security Gate

```bash
./scripts/demo.sh break secret   # ou: sast | sca | docker | iac
git add -A && git commit -m "demo: falha" && git push   # esteira reprova
./scripts/demo.sh fix
git add -A && git commit -m "fix: corrige falhas" && git push   # esteira aprova
```

O SBOM (`sbom-cyclonedx`) e o relatório do ZAP (`zap-report`) ficam como artefatos da execução.
