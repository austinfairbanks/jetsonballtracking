FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app
COPY proxy.py .
ENV PYTHONUNBUFFERED=1
CMD ["python", "proxy.py"]
