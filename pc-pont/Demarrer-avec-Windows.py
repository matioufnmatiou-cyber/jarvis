"""Double-clique ici une fois : le pont Jarvis se lancera tout seul à chaque démarrage du PC."""
import os
from pathlib import Path

pont = Path(__file__).resolve().with_name("jarvis_pont.py")
dest = Path(os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")) / "Jarvis.pyw"
dest.write_text(f'import runpy, sys\nsys.argv = [{str(pont)!r}]\nrunpy.run_path({str(pont)!r}, run_name="__main__")\n', encoding="utf-8")
print("C'est fait : Jarvis démarrera tout seul avec Windows.")
print("Pour arrêter ça, supprime ce fichier :", dest)
input("Appuie sur Entrée pour fermer.")
