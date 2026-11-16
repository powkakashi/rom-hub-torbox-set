"""Regenerate sets.json from what the TorBox account actually holds.

Run:  TORBOX_API_KEY=... python3 scripts/build_sets.py > sets.json

Why generated: TorBox's `torrents/mylist` needs `Authorization: Bearer`, and a
ROM Hub plugin only gets a GET client without headers, so the file list has to
arrive as a pinned data asset. One call here replaces it.
"""
import collections
import json
import os
import re
import sys
import urllib.request

ROM_EXT = (".zip", ".7z", ".rar", ".chd", ".iso", ".cue", ".bin", ".gcm", ".rvz",
           ".gb", ".gbc", ".gba", ".nes", ".sfc", ".smc", ".n64", ".z64", ".nds",
           ".3ds", ".pce", ".sgx")

# Folder text -> hub platform slug. First match wins, longest first.
FOLDER_SLUGS = [
    ("turbografx-cd", "turbografx-cd"),
    ("dreamcast", "dreamcast"),
    ("playstation 2", "ps2"),
    ("playstation", "psx"),
    ("gamecube", "ngc"),
    ("nintendo ds", "nds"),
    ("game boy advance", "gba"),
    ("game boy color", "gbc"),
    ("game boy", "gb"),
    ("nintendo entertainment system", "nes"),
    ("super nintendo", "snes"),
    ("nintendo 64", "n64"),
    ("sega - genesis", "genesis-slash-megadrive"),
]
FOLDER_KEYS = FOLDER_SLUGS + [(s, s) for s in
                              ("gb", "gbc", "gba", "nes", "snes", "n64", "nds", "psx", "ngc")]


def slug_for(path: str) -> str | None:
    low = path.lower()
    for needle, slug in sorted(FOLDER_KEYS, key=lambda p: -len(p[0])):
        if re.search(r"(^|[/ _-])" + re.escape(needle), low):
            return slug
    return None


def api(path: str, key: str):
    request = urllib.request.Request(
        "https://api.torbox.app/v1/api" + path,
        headers={"Authorization": f"Bearer {key}", "User-Agent": "rom-hub-torbox-set"})
    return json.loads(urllib.request.urlopen(request, timeout=180).read())


def main() -> int:
    key = os.environ.get("TORBOX_API_KEY") or ""
    if not key:
        print("TORBOX_API_KEY is not set", file=sys.stderr)
        return 2

    out: dict[str, dict] = {}
    for torrent in api("/torrents/mylist?bypass_cache=true", key)["data"]:
        files = torrent.get("files") or []
        if len(files) < 2:          # one blob: nothing to pick file by file
            continue
        per_platform: dict[str, list] = collections.defaultdict(list)
        for f in files:
            name = f.get("name") or ""
            if not name.lower().endswith(ROM_EXT):
                continue
            # Emulators shipped inside a grab-bag are not ROMs.
            if re.search(r"(^|/)emulators?/", name, re.I) or re.search(
                    r"(visualboyadvance|zsnes|virtuanes|snes9x|nestopia|project64|"
                    r"dolphin|pcsx|epsxe|mupen|retroarch)", os.path.basename(name), re.I):
                continue
            slug = slug_for(name)
            if not slug:
                continue
            title = re.sub(r"\.(zip|7z|rar|chd|iso|cue|bin|gcm|rvz|gb|gbc|gba|nes|sfc"
                           r"|smc|n64|z64|nds|3ds|pce|sgx)$", "", os.path.basename(name),
                           flags=re.I)
            per_platform[slug].append({"id": f["id"], "title": title,
                                       "file": os.path.basename(name), "size": f["size"]})
        for slug, rows in per_platform.items():
            existing = out.get(slug)
            # biggest set wins when two torrents overlap a platform
            if existing and len(existing["files"]) >= len(rows):
                continue
            out[slug] = {"torrent_id": torrent["id"], "torrent": torrent["name"],
                         "state": torrent.get("download_state"),
                         "files": sorted(rows, key=lambda r: r["title"].lower())}

    json.dump({"generated_by": "scripts/build_sets.py", "source": "torbox mylist",
               "platforms": out}, sys.stdout, indent=1, sort_keys=True)
    print("", file=sys.stderr)
    for slug, data in sorted(out.items()):
        print(f"{slug:20} {len(data['files']):5} files  torrent {data['torrent_id']}",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
