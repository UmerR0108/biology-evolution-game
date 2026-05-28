# Railway deployment image for the pygbag/WebAssembly build.
# Build static browser assets during the image build, then serve only build/web at runtime.

FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
COPY main.py pygbag.ini ./
COPY src ./src
COPY assets ./assets

RUN mkdir -p build/web build/web-cache \
    && uv run pygbag --build --ume_block 0 .

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /app/build/web ./build/web

EXPOSE 8000

CMD ["sh", "-c", "python -m http.server ${PORT:-8000} --bind 0.0.0.0 --directory build/web"]
