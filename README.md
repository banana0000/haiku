---
title: Haunted Haiku
emoji: 👻
colorFrom: purple
colorTo: pink
sdk: docker
app_port: 7860
---

# Haiku

Type a word or a mood and a local model (Gemma 3 via Ollama) writes a haiku. The same model picks two colours and a few emoji, and the app paints the poem as a gradient card. You can also choose the colours yourself, and translate the haiku into Hungarian, Spanish, German, French, Italian, Portuguese or Japanese.

Built for the Hacktoberfest Open-Source AI Challenge: Week 4 (Ghost in the Machine). Everything runs locally; the only network call goes to your own Ollama server.

## Run

```
ollama pull gemma3:4b
pip install -r requirements.txt
python app.py
```

Open http://localhost:8063.

## Settings (environment variables)

| Variable | Default | Meaning |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434` | where Ollama runs |
| `HAIKU_MODEL` | `gemma3:4b` | any Ollama model |
| `HOST` / `PORT` | `127.0.0.1` / `8063` | where the app listens |

## Deploying (Render)

`render.yaml` deploys the `Dockerfile` (Ollama and `gemma3:4b` baked in) as a Docker web service. It needs the Standard plan (4 GB RAM); set `ELEVENLABS_API_KEY` in the Render dashboard.

## Deploying (Hugging Face Spaces)

Create a Docker Space and push this repo. The `Dockerfile` installs Ollama and bakes in `gemma3:4b`, so the whole app (model included) runs inside the Space. Add `ELEVENLABS_API_KEY` under Settings → Secrets for voice and music.
