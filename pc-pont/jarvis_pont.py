"""
Pont PC de J.A.R.V.I.S.
Petit programme qui tourne sur ton PC (Windows) et laisse le Jarvis du site
https://matioufnmatiou-cyber.github.io/jarvis/ ouvrir tes applis, régler le son,
mettre la musique en pause, verrouiller ou éteindre le PC, etc.

Il n'écoute que ton propre PC (127.0.0.1) et n'accepte que le site de Jarvis.
Aucune installation de module : Python suffit.
"""
import ctypes
import glob
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 8765
SITE = "https://matioufnmatiou-cyber.github.io/jarvis/"
ALLOWED = {"https://matioufnmatiou-cyber.github.io", "http://localhost:8000", "http://127.0.0.1:8000"}
WINDOWS = sys.platform == "win32"

# nom dit à voix haute -> (comment l'ouvrir, nom du processus pour le fermer)
APPS = {
    "whatsapp": ("whatsapp:", "WhatsApp.exe"),
    "discord": ("discord:", "Discord.exe"),
    "spotify": ("spotify:", "Spotify.exe"),
    "steam": ("steam:", "steam.exe"),
    "epic games": ("com.epicgames.launcher:", "EpicGamesLauncher.exe"),
    "roblox": ("roblox:", "RobloxPlayerBeta.exe"),
    "minecraft": ("minecraft:", "Minecraft.Windows.exe"),
    "xbox": ("xbox:", "XboxPcApp.exe"),
    "teams": ("msteams:", "ms-teams.exe"),
    "calculatrice": ("calc", "CalculatorApp.exe"),
    "bloc-notes": ("notepad", "notepad.exe"),
    "bloc notes": ("notepad", "notepad.exe"),
    "paint": ("mspaint", "mspaint.exe"),
    "explorateur": ("explorer", None),
    "fichiers": ("explorer", None),
    "parametres": ("ms-settings:", "SystemSettings.exe"),
    "reglages": ("ms-settings:", "SystemSettings.exe"),
    "gestionnaire des taches": ("taskmgr", "Taskmgr.exe"),
    "invite de commande": ("cmd", "cmd.exe"),
    "word": ("winword", "WINWORD.EXE"),
    "excel": ("excel", "EXCEL.EXE"),
    "powerpoint": ("powerpnt", "POWERPNT.EXE"),
    "obs": ("obs64", "obs64.exe"),
    "vlc": ("vlc", "vlc.exe"),
    "camera": ("microsoft.windows.camera:", "WindowsCamera.exe"),
    "store": ("ms-windows-store:", "WinStore.App.exe"),
    "opera": ("opera", "opera.exe"),
}
SITES = {
    "youtube": "https://www.youtube.com", "google": "https://www.google.com", "gmail": "https://mail.google.com",
    "instagram": "https://www.instagram.com", "tiktok": "https://www.tiktok.com", "twitch": "https://www.twitch.tv",
    "netflix": "https://www.netflix.com", "snapchat": "https://web.snapchat.com", "twitter": "https://x.com",
    "amazon": "https://www.amazon.fr", "chatgpt": "https://chatgpt.com", "claude": "https://claude.ai",
    "facebook": "https://www.facebook.com", "wikipedia": "https://fr.wikipedia.org", "deezer": "https://www.deezer.com",
    "google maps": "https://maps.google.com", "maps": "https://maps.google.com", "github": "https://github.com",
}
FOLDERS = {"telechargements": ("Downloads", "vos téléchargements"), "documents": ("Documents", "vos documents"),
           "bureau": ("Desktop", "le bureau"), "images": ("Pictures", "vos images"), "photos": ("Pictures", "vos photos"),
           "musique": ("Music", "votre musique"), "videos": ("Videos", "vos vidéos")}

# touches spéciales Windows
VK = {"vol_up": 0xAF, "vol_down": 0xAE, "mute": 0xAD, "play": 0xB3, "next": 0xB0, "prev": 0xB1,
      "win": 0x5B, "snap": 0x2C, "d": 0x44}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[.!?,;]+", " ", s).strip()


def press(*keys, times=1):
    if not WINDOWS:
        print("[test] touches", keys, "x", times)
        return
    kb = ctypes.windll.user32.keybd_event
    for _ in range(times):
        for k in keys:
            kb(VK[k], 0, 0, 0)
        for k in reversed(keys):
            kb(VK[k], 0, 2, 0)
        time.sleep(0.01)


def run(cmd):
    """Lance une commande Windows sans passer par cmd.exe (que l'antivirus peut bloquer)."""
    print("[pc]", cmd)
    if WINDOWS:
        subprocess.Popen(cmd, creationflags=0x08000000)  # sans fenêtre noire


def start(target):
    print("[app]", target)
    if WINDOWS:
        os.startfile(target)


def open_jarvis():
    """Jarvis lui-même s'ouvre dans Edge (il n'entend pas dans les autres navigateurs)."""
    print("[jarvis]", SITE)
    if WINDOWS:
        try:
            os.startfile("microsoft-edge:" + SITE)
            return
        except OSError:
            pass
    webbrowser.open(SITE)


def open_url(url):
    """Les sites demandés (YouTube, Google…) s'ouvrent dans Firefox."""
    print("[web]", url)
    if WINDOWS:
        for exe in ("firefox.exe", os.path.expandvars(r"%ProgramFiles%\Mozilla Firefox\firefox.exe"),
                    os.path.expandvars(r"%ProgramFiles(x86)%\Mozilla Firefox\firefox.exe")):
            try:
                os.startfile(exe, arguments=f'"{url}"')
                return
            except OSError:
                continue
        os.startfile(url)   # Firefox introuvable : navigateur par défaut
    else:
        webbrowser.open(url)


def find_shortcut(name):
    """Cherche une appli dans le menu Démarrer par son nom (ex. « fortnite »)."""
    roots = [os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
             os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs"),
             str(Path.home() / "Desktop"), os.path.expandvars(r"%PUBLIC%\Desktop")]
    best = None
    for root in roots:
        for f in glob.glob(os.path.join(root, "**", "*.lnk"), recursive=True) + glob.glob(os.path.join(root, "**", "*.url"), recursive=True):
            stem = norm(Path(f).stem)
            if "uninstall" in stem or "desinstall" in stem:
                continue
            if stem == name:
                return f
            if name in stem and (best is None or len(stem) < len(norm(Path(best).stem))):
                best = f
    return best


def pick_app(t):
    for k in sorted(APPS, key=len, reverse=True):
        if k in t:
            return k
    return None


def handle(text):
    """Renvoie la phrase de Jarvis, ou None si ce n'est pas une commande pour le PC."""
    s = norm(text)
    low = re.sub(r"[.!?]+$", "", text.lower().strip())   # garde les accents pour les recherches
    s = re.sub(r"^(jarvis\s+)?(est-ce que tu peux |tu peux |peux-tu |stp |s'il te plait )", "", s)
    pc = r"(pc|ordi|ordinateur)"

    # son
    if re.search(r"(coupe|enleve|desactive|mute)\w* (le )?(son|volume)|mode muet", s):
        press("mute"); return "Son coupé, monsieur. Le silence est d'or."
    if re.search(r"(remet|reactive)\w* (le )?son", s):
        press("mute"); return "Le son est de retour, monsieur."
    if re.search(r"(volume|son) (a fond|au max)|(met|mets) (le son|le volume) (a fond|au max)", s):
        press("vol_up", times=50); return "Volume au maximum, monsieur. Pensez à vos voisins."
    if re.search(r"(monte|augmente|plus fort|hausse)", s) and re.search(r"son|volume|fort", s):
        press("vol_up", times=5); return "Volume augmenté, monsieur."
    if re.search(r"(baisse|diminue|moins fort)", s) and re.search(r"son|volume|fort", s):
        press("vol_down", times=5); return "Volume baissé, monsieur."

    # musique / vidéo
    if re.search(r"(musique|chanson|son|titre|piste|video) suivante|(chanson|musique|piste) d'apres|passe (a la )?(chanson|musique)|^suivant", s):
        press("next"); return "Morceau suivant, monsieur."
    if re.search(r"(musique|chanson|piste|video) precedente|reviens (a la )?(chanson|musique)", s):
        press("prev"); press("prev"); return "Morceau précédent, monsieur."
    if re.search(r"(pause|reprend\w*|relance\w*|arrete\w*|met\w* pause|play)\b.*(musique|chanson|video|lecture|spotify|son)|^(pause|play|reprends)$", s):
        press("play"); return "C'est fait, monsieur."

    # PC entier
    if re.search(r"(annule|stop|arrete)\w* (l'|le |la )?(extinction|redemarrage|arret)", s):
        run("shutdown /a"); return "Extinction annulée, monsieur. Vous m'avez fait peur."
    if re.search(rf"(eteins|eteint|eteindre|arrete|ferme)\w* (le |l'|mon )?{pc}", s):
        run("shutdown /s /t 30"); return "J'éteins le PC dans trente secondes, monsieur. Dites « annule l'extinction » si vous changez d'avis."
    if re.search(rf"redemarre\w* (le |l'|mon )?{pc}", s):
        run("shutdown /r /t 30"); return "Redémarrage dans trente secondes, monsieur. Dites « annule le redémarrage » pour l'arrêter."
    if re.search(rf"(verrouille|bloque)\w* (le |l'|mon )?({pc}|ecran|session)", s):
        run("rundll32.exe user32.dll,LockWorkStation"); return "PC verrouillé, monsieur. Personne ne passera."
    if re.search(rf"(met|mets|passe)\w* (le |l'|mon )?{pc} en veille", s):
        run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0"); return "Mise en veille du PC, monsieur. Bonne nuit à lui."
    if re.search(r"capture d'ecran|screenshot|capture (l'|de l')?ecran", s):
        press("win", "snap"); return "Capture d'écran enregistrée dans Images, Captures d'écran, monsieur."
    if re.search(r"(montre|affiche|va sur) (le )?bureau|reduis tout|cache tout", s):
        press("win", "d"); return "Voici le bureau, monsieur."

    # YouTube / recherche
    m = re.search(r"(?:mets|met|joue|lance|passe|cherche|ouvre)\s+(.+?)\s+sur youtube", low) or re.search(r"^youtube\s+(.+)", low)
    if m:
        open_url("https://www.youtube.com/results?search_query=" + urllib.parse.quote(m.group(1)))
        return f"Je lance {m.group(1)} sur YouTube, monsieur."
    m = re.search(r"^(?:cherche|recherche|google)\s+(.+?)(?:\s+sur google)?$", low)
    if m:
        open_url("https://www.google.com/search?q=" + urllib.parse.quote(m.group(1)))
        return f"Voici les résultats pour {m.group(1)}, monsieur."

    # fermer une appli
    m = re.search(r"(?:^(?:coupe|arrete|tue)|\b(?:ferme|fermer|quitte|quitter))\s+(?:l'appli |l'application |le |la |l'|les )?(.+)", s)
    if m:
        t = m.group(1).strip()
        if re.search(r"edge|chrome|navigateur", t):
            return "Je préfère ne pas fermer le navigateur dans lequel je vis, monsieur. Question de survie."
        key = pick_app(t)
        if key and APPS[key][1]:
            run(f"taskkill /im {APPS[key][1]} /f")
            return f"{key.capitalize()} est fermé, monsieur."
        return None

    # ouvrir : dossier, site, appli connue, ou n'importe quelle appli du menu Démarrer
    m = re.search(r"(?:^(?:mets|met|affiche)|\b(?:ouvre|ouvrir|lance|lancer|demarre|demarrer|va sur))\s+(?:moi\s+)?(?:l'appli |l'application |le site |le dossier |le |la |l'|les |mes |mon |ma )?(.+)", s)
    if m:
        t = re.sub(r"\s+(stp|s'il te plait|steuplait|merci)$", "", m.group(1).strip())
        for k, (sub, label) in FOLDERS.items():
            if t.startswith(k):
                p = Path.home() / sub
                print("[dossier]", p)
                if WINDOWS:
                    os.startfile(p)
                return f"Voici {label}, monsieur."
        for k in sorted(SITES, key=len, reverse=True):
            if t == k or t.startswith(k + " "):
                open_url(SITES[k]); return f"J'ouvre {k.capitalize()}, monsieur."
        key = pick_app(t)
        if key == "whatsapp" and WINDOWS and not find_shortcut("whatsapp"):
            open_url("https://web.whatsapp.com"); return "WhatsApp n'est pas installé sur le PC, j'ouvre WhatsApp Web, monsieur."
        if key:
            try:
                start(APPS[key][0]); return f"J'ouvre {key.capitalize()}, monsieur."
            except OSError:
                lnk = find_shortcut(key) if WINDOWS else None
                if lnk:
                    os.startfile(lnk); return f"J'ouvre {key.capitalize()}, monsieur."
                return f"Je ne trouve pas {key.capitalize()} sur ce PC, monsieur. Il faudrait peut-être l'installer."
        if WINDOWS:
            lnk = find_shortcut(t)
            if lnk:
                os.startfile(lnk); return f"J'ouvre {Path(lnk).stem}, monsieur."
        if re.search(r"\.[a-z]{2,}$", t):
            open_url("https://" + t.replace(" ", "")); return f"J'ouvre {t}, monsieur."
        return None
    return None


class Handler(BaseHTTPRequestHandler):
    def cors(self):
        origin = self.headers.get("Origin", "")
        if origin in ALLOWED:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "content-type")
            self.send_header("Access-Control-Allow-Private-Network", "true")
        return origin in ALLOWED

    def reply(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204 if self.headers.get("Origin", "") in ALLOWED else 403)
        self.cors()
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/ping"):
            return self.reply(200, {"ok": True, "jarvis": "pont-pc", "v": 1})
        self.reply(404, {"ok": False})

    def do_POST(self):
        if self.headers.get("Origin", "") not in ALLOWED:   # seul le site de Jarvis peut commander le PC
            return self.reply(403, {"ok": False})
        if not self.path.startswith("/cmd"):
            return self.reply(404, {"ok": False})
        try:
            n = min(int(self.headers.get("Content-Length", 0)), 4000)
            text = json.loads(self.rfile.read(n) or b"{}").get("text", "")
        except Exception:
            return self.reply(400, {"ok": False})
        try:
            say = handle(str(text))
        except Exception as e:
            print("[erreur]", e)
            say = "Je n'ai pas réussi, monsieur. Mon pont avec le PC a eu un petit raté."
        print(f"VOUS : {text}  ->  {say}")
        self.reply(200, {"ok": True, "say": say})

    def log_message(self, *a):
        pass


def main():
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        print("Le pont Jarvis tourne déjà.")
        if "--no-browser" not in sys.argv:
            open_jarvis()
        return
    print(f"Pont PC de Jarvis prêt sur le port {PORT}. Laisse cette fenêtre ouverte (tu peux la réduire).")
    if "--no-browser" not in sys.argv:
        open_jarvis()
    srv.serve_forever()


if __name__ == "__main__":
    main()
