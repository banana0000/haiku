---
title: "A haiku that paints its own picture: a tiny local Gemma 3 app (Ghost in the Machine)"
published: false
description: "Type a word, get a haiku and a picture. Gemma 3 runs through Ollama on your own machine and also picks the colours and emoji for the card."
tags: hf26challenge, python, ollama, ai
---

*This is my submission for the [Hacktoberfest Open-Source AI Challenge: Week 4](https://dev.to/challenges/hf26) (theme: Ghost in the Machine).*

## What I built

A very small app: you type a word or a mood ("autumn rain", "sunset on the sea"), and a local model writes a haiku for it. The same model also decides what the poem should *look like*: it picks two colours and a few emoji, and the app paints the poem as a card with a two-colour gradient and a big, faint emoji scene behind the text.

My reading of the theme: the "ghost in the machine" is the voice that whispers a poem back at you from inside your own laptop. It is not a cloud service. It is an open-weight model, Gemma 3, running through Ollama on `localhost`.

<!-- TODO: add a screenshot or GIF of the app with a generated card -->

## Why open, and why local

- **It works with the Wi-Fi off.** The only network call goes to `localhost:11434`.
- **Nothing you type leaves the machine.** A haiku prompt is not sensitive, but the same code works for things that are.
- **The model is a one-line swap.** `HAIKU_MODEL=gemma3:12b` (or any other Ollama model) changes the poet without touching the code.

## How it works

One Python file, [Dash](https://dash.plotly.com/) with Dash Mantine Components for the UI, and plain `requests` for the model call. No SDK.

The interesting part is that a single request returns both the poem and the art direction, as JSON:

```python
PROMPT = (
    "Write an English haiku (3 lines, 5-7-5 syllables) about: {topic}. Also design a picture for it. "
    "Reply with JSON only: {{\"lines\": [3 strings], \"emoji\": \"1 to 3 emoji that show the scene\", "
    "\"from\": a colour, \"to\": a different colour}}. Colours must come from: " + ", ".join(COLORS) + ". "
    "Pick colours that match the mood (e.g. cold blues for rain, warm orange and pink for sunset).")

def haiku(topic):
    r = requests.post(f"{OLLAMA_URL}/api/chat", timeout=120, json={
        "model": MODEL, "stream": False, "format": "json", "options": {"temperature": 0.9},
        "messages": [{"role": "user", "content": PROMPT.format(topic=topic)}]})
    r.raise_for_status()
    d = json.loads(r.json()["message"]["content"])
    ...
```

Setting `"format": "json"` makes Ollama constrain the output to valid JSON. The colours are limited to Mantine's palette names, so the picture is just CSS variables:

```python
"background": f"linear-gradient(135deg, var(--mantine-color-{h['from']}-8) 0%, "
              f"var(--mantine-color-{h['to']}-5) 100%)"
```

There is no image model involved. The "picture" is a gradient, a large translucent emoji and the poem, all drawn with Dash Mantine Components. You can also override either colour from two dropdowns, or leave them on "Auto" and let the model choose.

## Things that went wrong (and what I did about them)

- **The model does not always follow the schema.** I asked for `"emoji": "1 to 3 emoji"` as a string. Sometimes it returns a *list* instead. My first version printed `"['🌧️', '🍂', "` into the picture. The fix is three lines: if it is a list, join it.
- **Colours need validating.** The model can answer with a colour that is not in the palette, or the same colour twice. I check both and fall back to a default pair.
- **5-7-5 is a hint, not a guarantee.** Gemma does not count syllables reliably. Most English haiku come out close, but not all are exactly 5-7-5.

## Run it

Code: [banana0000/haiku](https://github.com/banana0000/haiku)

```bash
git clone https://github.com/banana0000/haiku
cd haiku
ollama pull gemma3:4b
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:8063`. There is no login. Type a word, press **Write a haiku** (or Enter), and optionally pick the two colours.

## Related reading

For the JSON side of this, [Clean JSON Extraction with Ollama and Python](https://dev.to/nearshi/-clean-json-extraction-with-ollama-and-python-21f3) by nearshi is on the same problem: getting dependable structured output from a local model.

## Prize categories

- **Best Use of Gemma:** Gemma 3 (`gemma3:4b`) is the only model in the app. It writes the poem and chooses its colours and emoji.

## Reflection

The pleasant surprise was how far a small model goes when you ask it for *structure* instead of just text. One request, one JSON object, and the model is both the poet and the art director. The unpleasant surprise was how often a small model almost follows a schema. Validating its output is not optional.
