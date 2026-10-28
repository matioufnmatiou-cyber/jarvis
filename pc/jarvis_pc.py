"""
J.A.R.V.I.S. version PC
Ecoute le micro, se reveille quand on dit "Jarvis", execute les commandes
(ouvrir un site, une appli, chercher sur YouTube/Google, donner l'heure...)
et repond avec une voix grave de majordome.

Lancer :  python jarvis_pc.py
"""
import asyncio
import datetime
import os
import platform
import subprocess
import tempfile
import urllib.parse
import webbrowser

import edge_tts
import pygame
import speech_recognition as sr

try:
    import anthropic
except ImportError:
    anthropic = None

WAKE_WORD = "jarvis"
VOICE = "fr-FR-RemyMultilingualNeural"   # voix masculine grave ; essayez aussi "fr-FR-HenriNeural"
PITCH = "-8Hz"                # plus grave = plus "Jarvis"
RATE = "+0%"
MODEL = "claude-sonnet-5-5"

SYSTEM = (
    "Tu es J.A.R.V.I.S., l'intelligence artificielle majordome de Tony Stark, au service de "
    "l'utilisateur que tu appelles 'monsieur'. Flegme britannique, poli, tres competent, humour "
    "pince-sans-rire discret. Reponds toujours en francais, en 1 a 3 phrases courtes faites pour "
    "etre dites a voix haute, sans listes ni markdown ni emoji. Quand on te demande d'agir sur "
    "l'ordinateur, utilise les outils, puis confirme brievement ce que tu as fait."
)

# ---------------------------------------------------------------- voix

pygame.mixer.init()


def say(text: str) -> None:
    print(f"JARVIS : {text}")
    path = os.path.join(tempfile.gettempdir(), "jarvis_voice.mp3")
    try:
        pygame.mixer.music.unload()
    except Exception:
        pass
    asyncio.run(edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH).save(path))
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.wait(50)


# ---------------------------------------------------------------- actions sur le PC

APPS = {
    "Windows": {
        "bloc-notes": "notepad", "calculatrice": "calc", "explorateur": "explorer",
        "paint": "mspaint", "parametres": "start ms-settings:", "chrome": "start chrome",
        "spotify": "start spotify:", "discord": "start discord:", "edge": "start msedge",
    },
    "Darwin": {
        "calculatrice": "open -a Calculator", "notes": "open -a Notes", "safari": "open -a Safari",
        "chrome": "open -a 'Google Chrome'", "spotify": "open -a Spotify", "finder": "open .",
    },
    "Linux": {
        "calculatrice": "gnome-calculator", "terminal": "x-terminal-emulator", "firefox": "firefox",
        "fichiers": "xdg-open .",
    },
}


def open_website(url: str) -> str:
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"ouvert : {url}"


def search_google(query: str) -> str:
    webbrowser.open("https://www.google.com/search?q=" + urllib.parse.quote(query))
    return f"recherche Google : {query}"


def search_youtube(query: str) -> str:
    webbrowser.open("https://www.youtube.com/results?search_query=" + urllib.parse.quote(query))
    return f"recherche YouTube : {query}"


def open_app(name: str) -> str:
    table = APPS.get(platform.system(), {})
    key = next((k for k in table if k in name.lower() or name.lower() in k), None)
    cmd = table[key] if key else name
    try:
        subprocess.Popen(cmd, shell=True)
        return f"application lancee : {key or name}"
    except Exception as e:
        return f"echec : {e}"


def get_datetime() -> str:
    return datetime.datetime.now().strftime("%A %d %B %Y, %H:%M")


TOOLS = [
    {"name": "open_website", "description": "Ouvre un site web dans le navigateur.",
     "input_schema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}},
    {"name": "search_google", "description": "Lance une recherche Google.",
     "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "search_youtube", "description": "Cherche une video ou une musique sur YouTube.",
     "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "open_app", "description": "Ouvre une application de l'ordinateur. Connues : "
     + ", ".join(APPS.get(platform.system(), {})) + ".",
     "input_schema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}},
    {"name": "get_datetime", "description": "Donne la date et l'heure actuelles.",
     "input_schema": {"type": "object", "properties": {}}},
]
ACTIONS = {"open_website": open_website, "search_google": search_google,
           "search_youtube": search_youtube, "open_app": open_app,
           "get_datetime": lambda: get_datetime()}

# ---------------------------------------------------------------- cerveau

client = anthropic.Anthropic() if anthropic and os.environ.get("ANTHROPIC_API_KEY") else None
history = []


def think(command: str) -> str:
    if client is None:
        return simple_brain(command)
    history.append({"role": "user", "content": command})
    del history[:-20]
    # l'historique doit commencer par un vrai message de l'utilisateur
    while history and not (history[0]["role"] == "user" and isinstance(history[0]["content"], str)):
        history.pop(0)
    for _ in range(5):
        resp = client.messages.create(model=MODEL, max_tokens=400, system=SYSTEM,
                                      tools=TOOLS, messages=history)
        history.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason != "tool_use":
            return "".join(b.text for b in resp.content if b.type == "text").strip()
        results = []
        for b in resp.content:
            if b.type == "tool_use":
                out = ACTIONS[b.name](**b.input)
                print(f"   [action] {b.name} -> {out}")
                results.append({"type": "tool_result", "tool_use_id": b.id, "content": out})
        history.append({"role": "user", "content": results})
    return "C'est fait, monsieur."


def simple_brain(c: str) -> str:
    """Mode sans cle API : quelques commandes de base."""
    s = c.lower()
    if "heure" in s:
        return f"Il est {datetime.datetime.now():%H heures %M}, monsieur."
    if "youtube" in s:
        q = s.split("youtube", 1)[1].strip(" :,")
        search_youtube(q) if q else open_website("youtube.com")
        return "YouTube est ouvert, monsieur."
    if s.startswith(("cherche", "recherche")):
        search_google(s.split(" ", 1)[1] if " " in s else "")
        return "Voici les resultats, monsieur."
    if s.startswith(("ouvre", "lance")):
        target = s.split(" ", 1)[1] if " " in s else ""
        if "." in target:
            open_website(target.replace(" ", ""))
        else:
            open_app(target)
        return f"J'ouvre {target}, monsieur."
    return "Sans ma cle d'acces, mes capacites sont limitees, monsieur. Ajoutez une cle API Anthropic pour que je puisse tout comprendre."


# ---------------------------------------------------------------- boucle principale

def main() -> None:
    r = sr.Recognizer()
    r.pause_threshold = 0.8
    mic = sr.Microphone()
    with mic as source:
        r.adjust_for_ambient_noise(source, duration=1)
    say("Bonjour monsieur. Tous les systemes sont en ligne. Dites Jarvis quand vous avez besoin de moi.")
    awake_until = datetime.datetime.min
    while True:
        with mic as source:
            print("... (j'ecoute)")
            try:
                audio = r.listen(source, timeout=None, phrase_time_limit=10)
            except Exception:
                continue
        try:
            heard = r.recognize_google(audio, language="fr-FR")
        except sr.UnknownValueError:
            continue
        except sr.RequestError:
            print("Reconnaissance vocale indisponible (pas d'internet ?)")
            continue
        print(f"VOUS : {heard}")
        low = heard.lower()
        now = datetime.datetime.now()
        if WAKE_WORD not in low and now > awake_until:
            continue
        command = low.split(WAKE_WORD, 1)[1].strip(" ,.") if WAKE_WORD in low else low
        if not command:
            say("Oui monsieur ?")
            awake_until = now + datetime.timedelta(seconds=15)
            continue
        if any(w in command for w in ("au revoir", "eteins-toi", "arrete-toi", "desactive-toi")):
            say("Tres bien monsieur. Je me mets en veille.")
            break
        say(think(command))
        awake_until = datetime.datetime.now() + datetime.timedelta(seconds=15)


if __name__ == "__main__":
    main()
