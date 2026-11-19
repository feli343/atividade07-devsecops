# ---- build: instala dependências em um venv isolado ----
FROM python:3.13-slim-bookworm AS build
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip==24.3.1 setuptools==78.1.1 wheel==0.46.2 \
    && /opt/venv/bin/pip install -r requirements.txt \
    && /opt/venv/bin/pip install urllib3==2.8.0 msgpack==1.2.3 jaraco.context==6.1.0

# ---- runtime: imagem final enxuta, sem root e sem ferramentas de build ----
FROM python:3.13-slim-bookworm
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin app \
    && /usr/local/bin/python -m pip uninstall -y pip setuptools wheel
WORKDIR /srv
COPY --from=build /opt/venv /opt/venv
COPY app ./app
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
