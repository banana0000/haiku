"""Haiku: type a word or a mood and Gemma 3 (via Ollama) writes a haiku and picks the colours and
emoji for its picture. Everything runs locally."""
import base64
import json
import os

import dash_mantine_components as dmc
import requests
from dotenv import load_dotenv
from elevenlabs import ElevenLabs
from dash import Dash, Input, ctx, no_update, Output, State, dcc, html

load_dotenv(".env")  # ELEVENLABS_API_KEY
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("HAIKU_MODEL", "gemma3:4b")
ELEVEN_VOICE = os.getenv("ELEVENLABS_VOICE", "JBFqnCBsd6RMkjVDRZzb")  # tetszőleges ElevenLabs voice id
HEX = {"red": "#fa5252", "orange": "#fd7e14", "yellow": "#fab005", "lime": "#82c91e", "green": "#40c057",
       "teal": "#12b886", "cyan": "#15aabf", "blue": "#228be6", "indigo": "#4c6ef5", "violet": "#7950f2",
       "grape": "#be4bdb", "pink": "#e64980"}
COLORS = list(HEX)
PROMPT = (
    "Write an eerie, haunted English {form} about: {topic}. Make it spooky: ghosts, whispers, candlelight, fog, the thin line between the living and the dead (Halloween and Dia de los Muertos spirit). Also design a picture for it. "
    "Reply with JSON only: {{\"lines\": [{n} strings], \"emoji\": \"1 to 3 spooky emoji that show the scene\", "
    "\"from\": a colour, \"to\": a different colour}}. Colours must come from: " + ", ".join(COLORS) + ". "
    "Pick dark, haunting colours that match the mood (e.g. midnight indigo, deep violet, candle orange).")


def haiku(topic, n=3):
    form = "haiku (3 lines, 5-7-5 syllables)" if n == 3 else f"short haiku-style poem of exactly {n} lines"
    r = requests.post(f"{OLLAMA_URL}/api/chat", timeout=120, json={
        "model": MODEL, "stream": False, "format": "json", "options": {"temperature": 0.9},
        "messages": [{"role": "user", "content": PROMPT.format(topic=topic, form=form, n=n)}]})
    r.raise_for_status()
    d = json.loads(r.json()["message"]["content"])
    c1 = d.get("from") if d.get("from") in COLORS else "grape"
    c2 = d.get("to") if d.get("to") in COLORS and d.get("to") != c1 else ("pink" if c1 != "pink" else "indigo")
    c1, c2 = HEX[c1], HEX[c2]  # a kép hexet használ, mert a színválasztó is azt ad
    emoji = d.get("emoji") or "👻"
    if isinstance(emoji, list):  # a modell néha listát ad
        emoji = "".join(str(e) for e in emoji[:3])
    return {"lines": [str(l).strip() for l in d["lines"]][:n], "emoji": str(emoji)[:12],
            "from": c1, "to": c2}


MAX_LINES = 10
# lágy fényfoltok (bokeh) a kép hátterében
BOKEH = ", ".join(f"radial-gradient(circle at {x}% {y}%, rgba(255,255,255,{o}) 0, rgba(255,255,255,0) {r}px)"
                  for x, y, r, o in [(12, 70, 38, .22), (30, 25, 24, .18), (55, 80, 46, .16), (72, 18, 30, .24),
                                     (90, 55, 40, .18), (45, 45, 18, .14), (8, 20, 20, .16), (66, 62, 22, .14)])


def mix(hexc, other, pct):
    """pct % of hexc over other (both #rrggbb), as #rrggbb."""
    a, b = (tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in (hexc, other))
    return "#" + "".join(f"{round(x * pct / 100 + y * (100 - pct) / 100):02x}" for x, y in zip(a, b))


def speak(text):
    """ElevenLabs text-to-speech via the SDK (reads ELEVENLABS_API_KEY); returns an mp3 data URI."""
    client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))  # az SDK importkor olvasná, a .env addigra még nincs betöltve
    audio = client.text_to_speech.convert(text=text, voice_id=ELEVEN_VOICE, model_id="eleven_v4")
    return "data:audio/mpeg;base64," + base64.b64encode(b"".join(audio)).decode()


def music(text):
    """ElevenLabs Music: a short instrumental backing track that fits the poem; returns an mp3 data URI."""
    client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
    audio = client.music.compose(
        prompt=f"Eerie, haunted instrumental ambient music, slow and quiet, for this poem: {text}",
        music_length_ms=20000, force_instrumental=True)
    return "data:audio/mpeg;base64," + base64.b64encode(b"".join(audio)).decode()


def picture(h):
    """The haiku as a picture: a two-colour gradient, a big faint emoji scene and the poem on top."""
    return dmc.Paper(
        id="card", radius="lg", p="md", mih=170, style={
            "position": "relative", "overflow": "hidden", "display": "flex", "alignItems": "center",
            "justifyContent": "center", "textAlign": "center",
            "background": BOKEH + ", " + f"radial-gradient(circle at 18% 12%, rgba(255,255,255,.30), transparent 42%), "
                          f"radial-gradient(circle at 88% 95%, {mix(h['to'], '#ffffff', 60)}, transparent 55%), "
                          f"linear-gradient(145deg, {mix(h['from'], '#000000', 45)} 0%, "
                          f"{h['from']} 38%, {h['to']} 100%)",
            "boxShadow": f"0 18px 50px {mix(h['from'], '#000000', 45)}, "
                         "inset 0 0 80px rgba(0,0,0,.35), inset 0 0 0 1px rgba(255,255,255,.15)"},
        children=[
            html.Div(h["emoji"], style={"position": "absolute", "right": -6, "bottom": -18,
                                        "fontSize": 110, "opacity": .22, "lineHeight": 1}),
            html.Div(h["emoji"], style={"position": "absolute", "left": 14, "top": 8,
                                        "fontSize": 34, "opacity": .45}),
            dmc.Stack(gap="xs", style={"position": "relative"}, children=[
                dmc.Text(l, size="xl", fs="italic", c="white", ff="Georgia, serif", fw=500,
                         style={"textShadow": "0 2px 12px rgba(0,0,0,.45)"}) for l in h["lines"]])])


HTML2CANVAS = "https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"
BLACK = {"backgroundColor": "#000", "color": "#fff", "borderColor": "#5a2a6b", "fontSize": 16,
         "boxShadow": "0 0 14px rgba(190,75,219,.25)"}  # fekete beviteli mező, lila fénnyel

app = Dash(__name__, title="Haunted Haiku", external_scripts=[HTML2CANVAS])
server = app.server  # gunicorn (e.g. Render) uses this
app.layout = dmc.MantineProvider(forceColorScheme="dark", theme={"primaryColor": "grape", "components": {c: {"styles": {"input": BLACK}} for c in ("TextInput",)}},
    children=dmc.Container(size="xs", py="xl", children=dmc.Stack(gap="md", children=[
        dmc.Title("👻 Haunted Haiku", order=1, ta="center", c="grape.3"),
        dmc.Text(id="status", size="xs", ta="center"),
        dmc.TextInput(id="topic", placeholder="A word or a mood, e.g. empty house, candle, fog", n_submit=0,
                      size="lg", radius="xl", leftSection="👻"),
        dmc.Switch(id="auto", label="✨ Let the AI pick the colours", checked=True, color="grape", size="md"),
        dmc.Group(grow=True, align="flex-end", children=[
            dmc.Stack(gap=4, children=[dmc.Text("Colour", size="sm", fw=500),
                                       dmc.ColorPicker(id="c1", value=HEX["grape"], format="hex", fullWidth=True,
                                                       styles={"saturation": {"display": "none"}})]),  # csak a csúszka
            dmc.Stack(gap=4, children=[dmc.Text("Lines", size="sm", fw=500),
                                       dmc.Group(gap="xs", wrap="nowrap", children=[
                                           dmc.ActionIcon("−", id="minus", n_clicks=0, variant="light", color="grape", size="lg", radius="xl"),
                                           dmc.Text("3", id="nshow", fw=600, w=30, ta="center"),
                                           dmc.ActionIcon("+", id="plus", n_clicks=0, variant="light", color="grape", size="lg", radius="xl"),
                                           dcc.Store(id="nlines", data=3)])])]),
        dmc.Group(justify="center", children=dmc.Button(
            "🕯️ Summon a haiku", id="go", n_clicks=0, size="sm", radius="xl",
            variant="gradient", gradient={"from": "grape", "to": "pink", "deg": 45})),
        dcc.Loading(html.Div(id="out", style={"minHeight": 40}),
                    custom_spinner=dmc.Loader(type="dots", color="pink")),
        dmc.Group(justify="center", gap="xs", children=[
            dmc.Button("🔊 Read aloud", id="speak", n_clicks=0, variant="light", color="gray", size="xs"),
            dmc.Button("🎵 Add music", id="music", n_clicks=0, variant="light", color="gray", size="xs"),
            dmc.Button("💾 Save as PNG", id="save", n_clicks=0, variant="light", color="gray", size="xs")]),
        html.Div(id="voice"), dcc.Loading(html.Div(id="tune"), custom_spinner=dmc.Loader(type="dots", color="pink")),
        dcc.Store(id="current"),
        dcc.Interval(id="tick", interval=10000),
    ])))


@app.callback(Output("status", "children"), Output("status", "c"), Input("tick", "n_intervals"))
def status(_n):  # ha fut az Ollama, kiírja
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        r.raise_for_status()
        names = [m.get("name", "") for m in r.json().get("models", [])]
    except (requests.RequestException, ValueError):
        return "● Ollama is not running (ollama serve)", "red"
    if MODEL not in names:
        return f"● Ollama is running, but {MODEL} is missing (ollama pull {MODEL})", "orange"
    return f"● Ollama is running ({MODEL})", "green"


@app.callback(Output("nlines", "data"), Output("nshow", "children"),
              Input("minus", "n_clicks"), Input("plus", "n_clicks"), State("nlines", "data"),
              prevent_initial_call=True)
def step(_m, _p, n):  # 1-MAX_LINES sor között lépked
    n = max(1, min(MAX_LINES, n + (1 if ctx.triggered_id == "plus" else -1)))
    return n, str(n)


@app.callback(Output("auto", "checked"), Input("c1", "value"), prevent_initial_call=True)
def picked(_c1):  # ha a felhasználó színt választ, kikapcsol az auto
    return False


@app.callback(Output("c1", "style"), Input("auto", "checked"))
def dim(auto):  # auto alatt halvány a választó
    return {"opacity": .4} if auto else {"opacity": 1}


@app.callback(Output("out", "children"), Output("current", "data"), Input("go", "n_clicks"), Input("topic", "n_submit"),
              State("topic", "value"), State("auto", "checked"), State("c1", "value"),
              State("nlines", "data"), prevent_initial_call=True)
def write(_n, _s, topic, auto, c1, nlines):
    if not topic:
        return dmc.Alert("Type a word first.", color="orange"), no_update
    try:
        h = haiku(topic, nlines)
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return dmc.Alert("Could not make the haiku. Is Ollama running? (ollama serve)", color="red"), no_update
    # a kézzel választott szín felülírja a modell választását; auto bekapcsolva = marad a modellé
    if not auto:
        h["from"] = h["to"] = c1
    return picture(h), ". ".join(h["lines"])


@app.callback(Output("voice", "children"), Input("speak", "n_clicks"), State("current", "data"),
              prevent_initial_call=True)
def read_aloud(_n, text):
    if not text:
        return dmc.Alert("Write a haiku first.", color="orange")
    if not os.getenv("ELEVENLABS_API_KEY"):
        return dmc.Alert("Add ELEVENLABS_API_KEY to the .env file and restart the app.", color="orange")
    try:
        src = speak(text)
    except Exception:  # SDK errors: bad key, no credits, network
        return dmc.Alert("ElevenLabs could not read it (check the API key and credits).", color="red")
    return html.Audio(src=src, controls=True, autoPlay=True, style={"width": "100%"})


@app.callback(Output("tune", "children"), Input("music", "n_clicks"), State("current", "data"),
              prevent_initial_call=True)
def add_music(_n, text):
    if not text:
        return dmc.Alert("Write a haiku first.", color="orange")
    if not os.getenv("ELEVENLABS_API_KEY"):
        return dmc.Alert("Add ELEVENLABS_API_KEY to the .env file and restart the app.", color="orange")
    try:
        src = music(text)
    except Exception:  # SDK errors: bad key, free plan (music needs a paid plan), no credits, network
        return dmc.Alert("ElevenLabs could not make the music (music needs a paid plan and credits).", color="red")
    return html.Audio(src=src, controls=True, autoPlay=True, loop=True, style={"width": "100%"})


app.clientside_callback(
    """function(n) {
        const card = document.getElementById("card");
        if (!n || !card) return window.dash_clientside.no_update;
        html2canvas(card, {scale: 2, backgroundColor: null}).then(c => {
            const a = document.createElement("a");
            a.href = c.toDataURL("image/png");
            a.download = "haiku.png";
            a.click();
        });
        return window.dash_clientside.no_update;
    }""",
    Output("save", "n_clicks"), Input("save", "n_clicks"), prevent_initial_call=True)


if __name__ == "__main__":
    app.run(debug=False, host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8063)))
