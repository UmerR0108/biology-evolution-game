# Railway deployment image for the pygbag/WebAssembly build.
# Build static browser assets during the image build, then serve only build/web at runtime.

FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
COPY main.py pygbag.ini serve.py patch_pygbag_loader.py ./
COPY src ./src
COPY assets ./assets

RUN mkdir -p build/web build/web-cache \
    && uv run pygbag --build --ume_block 0 . \
    && python patch_pygbag_loader.py build/web/index.html

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /app/build/web ./build/web
COPY serve.py ./serve.py

EXPOSE 8000

CMD ["python", "serve.py"]
