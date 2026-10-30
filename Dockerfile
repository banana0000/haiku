FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates zstd \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL https://ollama.com/install.sh | sh

# Hugging Face Spaces runs the container as uid 1000
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH \
    OLLAMA_MODELS=/home/user/.ollama/models HAIKU_MODEL=gemma3:4b
WORKDIR /home/user/app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# bake the model into the image so start-up is fast
RUN (ollama serve >/dev/null 2>&1 &) && sleep 5 && ollama pull $HAIKU_MODEL

COPY --chown=user . .
EXPOSE 7860
CMD ["bash", "start.sh"]
