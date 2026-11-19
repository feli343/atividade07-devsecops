#!/usr/bin/env bash
# Injeta (ou remove) falhas de segurança controladas para a demonstração ao vivo.
#
#   ./scripts/demo.sh break secret   -> senha/token hardcoded      (reprova: 1 Secret Scanning)
#   ./scripts/demo.sh break sast     -> eval() + SQL injection     (reprova: 2 SAST)
#   ./scripts/demo.sh break sca      -> biblioteca vulnerável      (reprova: 3 SCA)
#   ./scripts/demo.sh break docker   -> Dockerfile com USER root   (reprova: 4 Docker/IaC)
#   ./scripts/demo.sh break iac      -> pod privilegiado no K8s    (reprova: 4 Docker/IaC)
#   ./scripts/demo.sh fix            -> desfaz TODAS as falhas acima
#
# O script só altera arquivos. O git add/commit/push é feito à mão, ao vivo.
set -euo pipefail
cd "$(dirname "$0")/.."

VULN_LINE="PyYAML==5.3.1"   # CVE-2020-14343 (CRITICAL) - execução arbitrária de código

break_secret() {
  cat > app/config.py <<'EOF'
# ATENÇÃO: arquivo criado de propósito para a demo (credencial hardcoded)
DB_PASSWORD = "Sup3rS3cretPassw0rd2026"
INTERNAL_API_TOKEN = "demo7f3a9c1e5b2d8046aa91"
EOF
}

break_sast() {
  cat > app/legacy.py <<'EOF'
# ATENÇÃO: arquivo criado de propósito para a demo (SAST)
import sqlite3


def buscar_usuario(nome: str):
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM usuarios WHERE nome = '{nome}'")  # SQL injection
    return cur.fetchall()


def calcular(expressao: str):
    return eval(expressao)  # execução arbitrária de código
EOF
}

break_sca() {
  grep -qx "$VULN_LINE" requirements.txt || echo "$VULN_LINE" >> requirements.txt
}

break_docker() {
  sed -i 's/^USER 10001:10001/USER root/' Dockerfile
}

break_iac() {
  sed -i 's/^\( *\)privileged: false/\1privileged: true/' k8s/deployment.yaml
}

fix_all() {
  rm -f app/config.py app/legacy.py
  sed -i "\|^${VULN_LINE}\$|d" requirements.txt
  sed -i 's/^USER root/USER 10001:10001/' Dockerfile
  sed -i 's/^\( *\)privileged: true/\1privileged: false/' k8s/deployment.yaml
}

case "${1:-}" in
  break)
    case "${2:-}" in
      secret) break_secret ;;
      sast)   break_sast ;;
      sca)    break_sca ;;
      docker) break_docker ;;
      iac)    break_iac ;;
      *) echo "Uso: $0 break {secret|sast|sca|docker|iac}"; exit 2 ;;
    esac
    echo "Falha '${2}' injetada. Agora rode:"
    echo "  git add -A && git commit -m \"demo: falha ${2}\" && git push"
    ;;
  fix)
    fix_all
    echo "Falhas removidas. Agora rode:"
    echo "  git add -A && git commit -m \"fix: corrige falhas de seguranca\" && git push"
    ;;
  *)
    echo "Uso: $0 {break <tipo>|fix}"; exit 2 ;;
esac
