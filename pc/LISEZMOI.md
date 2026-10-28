# Jarvis version PC

Cette version t'entend vraiment, se réveille quand tu dis **« Jarvis »** et agit sur ton ordinateur (ouvrir un site, une appli, chercher sur YouTube ou Google, donner l'heure…).

## Installation (une seule fois)

1. Installe **Python 3.10 ou plus** : https://www.python.org/downloads/ (sur Windows, coche « Add Python to PATH »).
2. Ouvre un terminal dans ce dossier et tape :
   ```
   pip install -r requirements.txt
   ```
   Si PyAudio ne s'installe pas sur Windows : `pip install pipwin` puis `pipwin install pyaudio`.
3. (Recommandé) Pour que Jarvis comprenne tout, crée une clé API sur https://console.anthropic.com puis :
   - Windows : `setx ANTHROPIC_API_KEY "ta-cle"` (puis rouvre le terminal)
   - Mac/Linux : `export ANTHROPIC_API_KEY="ta-cle"`

   Sans clé, Jarvis marche quand même avec des commandes simples : « ouvre youtube.com », « lance calculatrice », « cherche la météo », « quelle heure est-il ».

## Lancer

```
python jarvis_pc.py
```

Puis dis par exemple :
- « Jarvis, mets de la musique de AC/DC sur YouTube »
- « Jarvis, ouvre la calculatrice »
- « Jarvis, quelle heure est-il ? »
- « Jarvis, au revoir » pour l'arrêter

## Changer la voix

En haut de `jarvis_pc.py` : `VOICE` (ex. `fr-FR-HenriNeural`, ou `en-GB-RyanNeural` pour l'accent anglais) et `PITCH` (`-8Hz` = plus grave).
