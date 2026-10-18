#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Synthetic demonstration fixture, Venka Imoveis adaptation, 2026.
"""Copy this fixture and bind its media paths for the native document reader.

Usage: python examples/venka-reel-9x16/prepare.py --output <new-scratch-dir>
Only the destination copy is written. No application is launched.
"""
from pathlib import Path
import argparse
import json
import shutil

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
source = Path(__file__).resolve().parent
target = args.output.resolve()
if target == source or source in target.parents:
    parser.error("Choose a scratch directory outside the example source")
if target.exists() and any(target.iterdir()):
    parser.error("Destination must be absent or empty; existing files are preserved")
shutil.copytree(source, target, dirs_exist_ok=True)
manifest = target / "concat.json"
document = json.loads(manifest.read_text(encoding="utf-8"))
expected = {"m1": "venka-test-1080x1920-30fps.mp4", "m2": "venka-logo.png"}
if {item["id"] for item in document["media"]} != set(expected):
    raise SystemExit("Unexpected fixture media IDs")
for item in document["media"]:
    media = target / "media" / expected[item["id"]]
    if not media.is_file():
        raise SystemExit(f"Missing fixture asset: {media}")
    item["path"] = str(media)
manifest.write_text(json.dumps(document, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(target)
