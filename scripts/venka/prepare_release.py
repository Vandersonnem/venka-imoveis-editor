#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Venka Imóveis
"""Collect real native builds under the stable names used by Venka's page.

Does not compile, sign, download, publish, or manufacture a missing installer.
The upstream smoke jobs must succeed before the CI job calls this script.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import plistlib
import re
import shutil
import subprocess
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
PRODUCT = "Venka Imóveis Editor"
BUNDLE_ID = "com.venkaimoveis.editor"


def sha256(path: pathlib.Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify(path: pathlib.Path, kind: str) -> dict:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"Build ausente ou vazio: {path}")
    detail: dict = {"format": kind}
    if kind == "exe":
        with path.open("rb") as stream:
            if stream.read(2) != b"MZ":
                raise ValueError(f"O arquivo não é um executável PE: {path}")
            stream.seek(0x3C)
            offset = int.from_bytes(stream.read(4), "little")
            stream.seek(offset)
            if stream.read(4) != b"PE\0\0":
                raise ValueError(f"Cabeçalho PE inválido: {path}")
            machine = int.from_bytes(stream.read(2), "little")
            if machine not in (0x8664, 0x14C):
                raise ValueError(f"Instalador Windows não é x86/x64: {path}")
            detail["pe_machine"] = hex(machine)
    elif kind == "dmg":
        with path.open("rb") as stream:
            stream.seek(-512, 2)
            if stream.read(4) != b"koly":
                raise ValueError(f"Trailer UDIF ausente no DMG: {path}")
    elif kind in ("apk", "ipa"):
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
            if bad:
                raise ValueError(f"CRC inválido: {path}: {bad}")
            names = set(archive.namelist())
            if kind == "apk":
                if "AndroidManifest.xml" not in names:
                    raise ValueError(f"Manifesto Android ausente: {path}")
                if not any(name.startswith("lib/arm64-v8a/") and name.endswith(".so") for name in names):
                    raise ValueError(f"Biblioteca Android arm64 ausente: {path}")
                detail["architecture"] = "arm64-v8a"
            else:
                plist_name = "Payload/VenkaEditor.app/Info.plist"
                if plist_name not in names:
                    raise ValueError(f"Payload do aplicativo Venka ausente: {path}")
                info = plistlib.loads(archive.read(plist_name))
                if info.get("CFBundleIdentifier") != BUNDLE_ID:
                    raise ValueError(f"Bundle ID diferente do Venka: {path}")
                if info.get("CFBundleDisplayName") != PRODUCT:
                    raise ValueError(f"Nome visível diferente do Venka: {path}")
                executable = info.get("CFBundleExecutable", "")
                if f"Payload/VenkaEditor.app/{executable}" not in names:
                    raise ValueError(f"Executável iOS ausente: {path}")
                detail.update(bundle_id=BUNDLE_ID, architecture="arm64", signing="ad-hoc; re-sign before installing on device")
    else:
        raise ValueError(f"Formato desconhecido: {kind}")
    return detail


def unique(bundles: pathlib.Path, name: str) -> pathlib.Path:
    matches = [path for path in bundles.rglob(name) if path.is_file()]
    if len(matches) != 1:
        raise ValueError(f"Esperado exatamente um build {name}; encontrados {len(matches)}")
    return matches[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundles", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--repository", required=True, help="Fork OWNER/REPO que receberá a release")
    parser.add_argument("--archive-source", action="store_true", help="Inclui o código correspondente do commit compilado")
    parser.add_argument("--archive-ref", default="HEAD", help="Commit/ref efetivamente compilado; permite recuperar um run anterior sem recompilar")
    parser.add_argument("--distribution-notice", type=pathlib.Path, help="Aviso legal complementar, separado da árvore de código compilada")
    parser.add_argument("--provenance", type=pathlib.Path, help="Recibo de validação do run original, incluindo commit e jobs nativos")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository):
        parser.error("--repository precisa ser OWNER/REPO")
    if args.repository.casefold() == "jub0t/concat":
        parser.error("A release Venka precisa apontar para seu fork, não para jub0t/Concat")
    if args.distribution_notice and not args.archive_source:
        parser.error("--distribution-notice requires --archive-source")
    commit = subprocess.check_output(["git", "rev-parse", "--verify", "--end-of-options", f"{args.archive_ref}^{{commit}}"], cwd=ROOT, text=True).strip()
    collector_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    provenance = None
    if args.provenance:
        provenance = json.loads(args.provenance.read_text(encoding="utf-8"))
        if provenance.get("head_sha") != commit or provenance.get("repository") != args.repository or provenance.get("status") != "PASS":
            raise ValueError("O recibo do run não corresponde ao commit/fork compilado, ou não passou na validação")
    cargo = subprocess.check_output(["git", "show", f"{commit}:src/Cargo.toml"], cwd=ROOT, text=True, encoding="utf-8")
    version_match = re.search(r'^version = "([0-9]+\.[0-9]+\.[0-9]+)"$', cargo, re.M)
    if not version_match:
        raise ValueError("Versão do workspace ausente")
    version = version_match[1]
    mapping = {
        f"Venka-Editor-{version}-windows-x86_64-setup.exe": ("venka-editor-windows.exe", "exe", "Windows x64"),
        f"Venka-Editor-{version}-macos-arm64.dmg": ("venka-editor-macos.dmg", "dmg", "macOS Apple silicon"),
        f"Venka-Editor-{version}-android-arm64.apk": ("venka-editor-android.apk", "apk", "Android arm64"),
        f"Venka-Editor-{version}-ios-arm64.ipa": ("venka-editor-ios.ipa", "ipa", "iOS/iPadOS arm64"),
    }
    intel = f"Venka-Editor-{version}-macos-x86_64.dmg"
    if any(args.bundles.rglob(intel)):
        mapping[intel] = ("venka-editor-macos-intel.dmg", "dmg", "macOS Intel")
    # Inspect every required build before creating even the first output file.
    verified = [(unique(args.bundles, original), target, kind, platform) for original, (target, kind, platform) in mapping.items()]
    formats = {target: verify(path, kind) for path, target, kind, _ in verified}
    args.out.mkdir(parents=True, exist_ok=True)
    entries = []
    for source, target, _, platform in verified:
        destination = args.out / target
        if destination.exists():
            raise ValueError(f"Saída já existe; use uma pasta nova: {destination}")
        shutil.copy2(source, destination)
        entries.append({"file": target, "platform": platform, "bytes": destination.stat().st_size,
                        "sha256": sha256(destination), **formats[target]})
    supplementary_notice = None
    if args.archive_source:
        for tracked in ("LICENSE", "src/Cargo.toml", "scripts/venka/prepare_release.py"):
            subprocess.run(["git", "cat-file", "-e", f"{commit}:{tracked}"], cwd=ROOT, check=True, capture_output=True)
        if args.archive_ref == "HEAD":
            # The implicit default should not accidentally publish a local
            # working-tree build with older sources. An explicit compiled ref
            # archives that exact tree even when only this collector changed.
            subprocess.run(["git", "diff", "--quiet", "HEAD", "--"], cwd=ROOT, check=True)
        archive = args.out.resolve() / "venka-editor-codigo-fonte.zip"
        subprocess.run(["git", "archive", "--format=zip", "--prefix=venka-imoveis-editor/", "-o", str(archive), commit], cwd=ROOT, check=True)
        if args.distribution_notice:
            notice = args.distribution_notice.resolve(strict=True)
            if not notice.is_file() or not notice.stat().st_size:
                raise ValueError(f"Aviso complementar ausente ou vazio: {notice}")
            supplementary_notice = {"file": f"DISTRIBUTION_NOTICES/{notice.name}", "bytes": notice.stat().st_size,
                                    "sha256": sha256(notice), "scope": "supplementary distribution notice; not compiled source"}
            with zipfile.ZipFile(archive, "a", compression=zipfile.ZIP_DEFLATED) as source_zip:
                source_zip.write(notice, supplementary_notice["file"])
                source_zip.writestr("DISTRIBUTION_NOTICES/README.txt", f"Compiled source is the unchanged venka-imoveis-editor/ tree from commit {commit}.\nFiles in DISTRIBUTION_NOTICES/ are supplemental distribution documents and were not compiled.\n")
        entries.append({"file": archive.name, "bytes": archive.stat().st_size, "sha256": sha256(archive), "kind": "corresponding-source"})
    report = {"product": PRODUCT, "version": version, "bundle_id": BUNDLE_ID, "commit": commit,
              "collector_commit": collector_commit, "supplementary_notice": supplementary_notice,
              "build_run": provenance.get("run") if provenance else None,
              "source": f"https://github.com/{args.repository}/tree/{commit}",
              "license": "AGPL-3.0-or-later", "upstream": "https://github.com/jub0t/Concat",
              "validation_scope": "format/integrity only; native launch checks are separate CI jobs", "artifacts": entries}
    if provenance is not None:
        receipt = args.out / "ORIGINAL_RUN_VALIDATION.json"
        receipt.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report["provenance"] = {"file": receipt.name, "sha256": sha256(receipt)}
    (args.out / "VENKA_RELEASE.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    files = sorted(path for path in args.out.iterdir() if path.is_file() and path.name != "SHA256SUMS")
    (args.out / "SHA256SUMS").write_text("".join(f"{sha256(path)}  {path.name}\n" for path in files), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
