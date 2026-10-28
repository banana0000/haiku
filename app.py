"""Haiku: type a word or a mood and Gemma 3 (via Ollama) writes a haiku and picks the colours and
emoji for its picture. Everything runs locally."""
import json
import os

import dash_mantine_components as dmc
import requests
from dash import Dash, Input, Output, State, dcc, html

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("HAIKU_MODEL", "gemma3:4b")
COLORS = ["red", "orange", "yellow", "lime", "green", "teal", "cyan", "blue", "indigo",
          "violet", "grape", "pink"]
CHOICES = [{"value": "auto", "label": "✨ Auto (AI picks)"}] + [{"value": c, "label": c.capitalize()} for c in COLORS]
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
    c1 = d.get("from") if d.get("from") in COLORS else "grape"
    c2 = d.get("to") if d.get("to") in COLORS and d.get("to") != c1 else ("pink" if c1 != "pink" else "indigo")
    emoji = d.get("emoji") or "🌸"
    if isinstance(emoji, list):  # a modell néha listát ad
        emoji = "".join(str(e) for e in emoji[:3])
    return {"lines": [str(l).strip() for l in d["lines"]][:3], "emoji": str(emoji)[:12],
            "from": c1, "to": c2}


def picture(h):
    """The haiku as a picture: a two-colour gradient, a big faint emoji scene and the poem on top."""
    return dmc.Paper(
        radius="lg", p="xl", mih=340, style={
            "position": "relative", "overflow": "hidden", "display": "flex", "alignItems": "center",
            "justifyContent": "center", "textAlign": "center",
            "background": f"linear-gradient(135deg, var(--mantine-color-{h['from']}-8) 0%, "
                          f"var(--mantine-color-{h['to']}-5) 100%)",
            "boxShadow": f"0 12px 40px var(--mantine-color-{h['from']}-9)"},
        children=[
            html.Div(h["emoji"], style={"position": "absolute", "right": -10, "bottom": -30,
                                        "fontSize": 190, "opacity": .22, "lineHeight": 1}),
            html.Div(h["emoji"], style={"position": "absolute", "left": 14, "top": 8,
                                        "fontSize": 54, "opacity": .45}),
            dmc.Stack(gap="xs", style={"position": "relative"}, children=[
                dmc.Text(l, size="xl", fs="italic", c="white", ff="Georgia, serif", fw=500,
                         style={"textShadow": "0 2px 12px rgba(0,0,0,.45)"}) for l in h["lines"]])])


app = Dash(__name__, title="Haiku")
server = app.server  # gunicorn (e.g. Render) uses this
app.layout = dmc.MantineProvider(forceColorScheme="dark", theme={"primaryColor": "grape"},
    children=dmc.Container(size="xs", py="xl", children=dmc.Stack(gap="md", children=[
        dmc.Title("🌸 Haiku", order=1, ta="center", c="grape.3"),
        dmc.TextInput(id="topic", placeholder="A word or a mood, e.g. autumn rain", n_submit=0, size="md"),
        dmc.Group(grow=True, children=[
            dmc.Select(id="c1", label="Colour 1", data=CHOICES, value="auto", allowDeselect=False),
            dmc.Select(id="c2", label="Colour 2", data=CHOICES, value="auto", allowDeselect=False)]),
        dmc.Button("✨ Write a haiku", id="go", n_clicks=0, size="md", fullWidth=True,
                   variant="gradient", gradient={"from": "grape", "to": "pink", "deg": 45}),
        dcc.Loading(html.Div(id="out", style={"minHeight": 40}),
                    custom_spinner=dmc.Loader(type="dots", color="pink")),
    ])))


@app.callback(Output("out", "children"), Input("go", "n_clicks"), Input("topic", "n_submit"),
              State("topic", "value"), State("c1", "value"), State("c2", "value"),
              prevent_initial_call=True)
def write(_n, _s, topic, c1, c2):
    if not topic:
        return dmc.Alert("Type a word first.", color="orange")
    try:
        h = haiku(topic)
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return dmc.Alert("Could not make the haiku. Is Ollama running? (ollama serve)", color="red")
    # a választott szín felülírja a modell választását; "auto" = marad, amit a modell adott
    if c1 != "auto":
        h["from"] = c1
    if c2 != "auto":
        h["to"] = c2
    return picture(h)


if __name__ == "__main__":
    app.run(debug=False, host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8063)))
