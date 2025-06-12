import subprocess
import sys
from pathlib import Path
import shutil

# Répertoire libs/ dans le plugin
plugin_dir = Path(__file__).resolve().parent
libs_dir = plugin_dir / "libs"
libs_dir.mkdir(exist_ok=True)

# Installer watchdog dans un dossier temporaire
temp_install_dir = plugin_dir / "temp_libs"
if temp_install_dir.exists():
    shutil.rmtree(temp_install_dir)
temp_install_dir.mkdir()

print("📦 Installation de watchdog dans :", temp_install_dir)
subprocess.check_call([
    sys.executable, "-m", "pip", "install", "watchdog", "--target", str(temp_install_dir)
])

# Copier les fichiers dans libs/
for item in temp_install_dir.iterdir():
    dest = libs_dir / item.name
    if dest.exists():
        if dest.is_dir():
            shutil.rmtree(dest)
        else:
            dest.unlink()
    if item.is_dir():
        shutil.copytree(item, dest)
    else:
        shutil.copy2(item, dest)

# Nettoyage
shutil.rmtree(temp_install_dir)
print("✅ Watchdog installé dans libs/")
