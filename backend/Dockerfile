ARG PYTHON_IMAGE=python:3.10-slim
FROM ${PYTHON_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies before copying application code so Docker can reuse the
# layer when only source files change. The backend requirements include the
# runtime API stack, LLM/RAG clients, and Phase 6 quality tools used by CI.
COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY app ./app

EXPOSE 8000

# The FastAPI app is created in app.main:create_app and exported as `app`.
# Binding to 0.0.0.0 makes the service reachable from docker-compose and the
# host machine through the published container port.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
