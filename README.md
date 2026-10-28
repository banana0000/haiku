# Haiku

Type a word or a mood and a local model (Gemma 3 via Ollama) writes a haiku. The same model picks two colours and a few emoji, and the app paints the poem as a gradient card. You can also choose the colours yourself.

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

`render.yaml` and `gunicorn app:server` are included. The app itself is light, but Render's free instance is far too small to run Ollama, so `OLLAMA_URL` has to point to an Ollama server the service can reach.
