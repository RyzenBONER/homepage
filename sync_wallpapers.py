from pathlib import Path
import json
import re
import shutil
import subprocess

from PIL import Image, ImageOps

REPO = Path(__file__).resolve().parent
SOURCE = Path.home() / "WALLZ"
OUTPUT = REPO / "wallpapers"
SUPPORTED = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def natural_key(path: Path):
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", path.name)]


images = sorted(
    (path for path in SOURCE.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED),
    key=natural_key,
)
if not images:
    raise SystemExit(f"No supported wallpaper images found in {SOURCE}")

staging = REPO / "wallpapers-new"
if staging.exists():
    shutil.rmtree(staging)
staging.mkdir()

for number, source_path in enumerate(images, start=1):
    with Image.open(source_path) as opened:
        image = ImageOps.exif_transpose(opened)
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")
        image.save(staging / f"{number}.webp", "WEBP", quality=86, method=6)

if OUTPUT.exists():
    shutil.rmtree(OUTPUT)
staging.rename(OUTPUT)

entries = [f"wallpapers/{number}.webp" for number in range(1, len(images) + 1)]
(REPO / "wallpapers.js").write_text(
    "window.MICHAEL_WALLPAPERS = " + json.dumps(entries, indent=2) + ";\n",
    encoding="utf-8",
)

subprocess.run(["git", "add", "wallpapers", "wallpapers.js"], cwd=REPO, check=True)
changes = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=REPO)
if changes.returncode == 0:
    print(f"No wallpaper changes found. {len(images)} images are already published.")
else:
    subprocess.run(["git", "commit", "-m", f"Update-wallpapers-{len(images)}"], cwd=REPO, check=True)
    subprocess.run(["git", "push"], cwd=REPO, check=True)
    print(f"Published {len(images)} wallpapers from {SOURCE}")
