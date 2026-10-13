# ==========================================
# Stage 1: Build & Dependencies
# ==========================================
FROM python:3.14-slim AS builder

WORKDIR /app

# Variables para optimizar instalación de Python y pip
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Crear virtualenv aislado para empaquetar dependencias
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar e instalar dependencias (aprovechando cache de layers)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt


# ==========================================
# Stage 2: Runtime Image (Minimal & Secure)
# ==========================================
FROM python:3.14-slim AS runner

WORKDIR /app

# Variables de entorno para ejecución
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=5000

# 1. Crear usuario y grupo sin privilegios (Principio de menor privilegio)
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -s /sbin/nologin -d /app appuser

# 2. Copiar únicamente el runtime virtualenv desde el builder
COPY --from=builder --chown=appuser:appgroup /opt/venv /opt/venv

# 3. Copiar el código fuente con permisos del usuario no-root
COPY --chown=appuser:appgroup . .

# 4. Cambiar al usuario sin privilegios ANTES de ejecutar cualquier proceso
USER appuser

# 5. Puerto expuesto
EXPOSE 5000

# 6. Healthcheck nativo con Python (evita instalar curl/wget en la imagen slim)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# 7. Ejecución con WSGI Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "2", "--timeout", "60", "app:app"]
