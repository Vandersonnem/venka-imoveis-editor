#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Venka Imóveis
"""Exercise the real native project/edit/export API on a synthetic 9:16 reel.

Requires an already compiled concat-cli and FFmpeg/ffprobe. No model, cloud,
stub API or pre-rendered video substitutes for the export.done event.
"""
from __future__ import annotations

import argparse
from array import array
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]


class NativeApi:
    def __init__(self, cli: Path, out: Path):
        self.log = (out / "rpc.jsonl").open("w", encoding="utf-8")
        self.errors = (out / "native-stderr.log").open("w", encoding="utf-8")
        self.messages: queue.Queue = queue.Queue()
        self.events: list[dict] = []
        self.request_id = 0
        env = os.environ.copy()
        home = out / "isolated-home"
        home.mkdir()
        for key, suffix in {"HOME": "", "APPDATA": "roaming", "LOCALAPPDATA": "local", "XDG_CONFIG_HOME": "config", "XDG_DATA_HOME": "data"}.items():
            destination = home / suffix
            destination.mkdir(exist_ok=True)
            env[key] = str(destination)
        self.process = subprocess.Popen([str(cli), "api"], cwd=out, env=env,
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=self.errors, text=True, encoding="utf-8", bufsize=1)

        def read() -> None:
            assert self.process.stdout is not None
            for line in self.process.stdout:
                self.log.write(line)
                self.log.flush()
                try:
                    self.messages.put(json.loads(line))
                except json.JSONDecodeError:
                    self.messages.put({"_invalid_line": line})
            self.messages.put({"_eof": True})

        self.reader = threading.Thread(target=read, daemon=True)
        self.reader.start()

    def next(self, deadline: float) -> dict:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Native API deadline expired")
        try:
            message = self.messages.get(timeout=remaining)
        except queue.Empty as exc:
            raise TimeoutError("No native API message before deadline") from exc
        if "_eof" in message:
            raise RuntimeError(f"Native API closed stdout (exit {self.process.poll()})")
        if "_invalid_line" in message:
            raise RuntimeError(f"Non-JSON native API output: {message['_invalid_line']}")
        return message

    def call(self, method: str, **params) -> dict:
        self.request_id += 1
        request = {"jsonrpc": "2.0", "id": self.request_id, "method": method, "params": params}
        self.log.write(json.dumps({"sent": request}, ensure_ascii=False) + "\n")
        self.log.flush()
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(request, ensure_ascii=False) + "\n")
        self.process.stdin.flush()
        deadline = time.monotonic() + 180
        while True:
            reply = self.next(deadline)
            if "method" in reply:
                self.events.append(reply)
            elif reply.get("id") == self.request_id:
                if "error" in reply:
                    raise RuntimeError(f"{method}: {reply['error']}")
                if "result" not in reply:
                    raise RuntimeError(f"Missing result for {method}: {reply}")
                return reply["result"]
            else:
                raise RuntimeError(f"Unexpected native reply: {reply}")

    def wait_export(self, job: str, timeout: int) -> dict:
        deadline = time.monotonic() + timeout
        cursor = 0
        while True:
            if cursor < len(self.events):
                event = self.events[cursor]
                cursor += 1
            else:
                event = self.next(deadline)
                if "method" not in event:
                    raise RuntimeError(f"Unexpected reply during export: {event}")
                self.events.append(event)
                cursor += 1
            if event.get("params", {}).get("job") != job:
                continue
            if event["method"] == "export.failed":
                raise RuntimeError(f"Native export failed: {event['params']}")
            if event["method"] == "export.done":
                return event["params"]

    def close(self, success: bool) -> None:
        if self.process.poll() is None:
            if self.process.stdin:
                self.process.stdin.close()
            try:
                self.process.wait(timeout=30 if success else 5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=10)
        self.reader.join(timeout=5)
        self.log.close()
        self.errors.close()
        if success and self.process.returncode != 0:
            raise RuntimeError(f"Native CLI exited {self.process.returncode} after export")


def clips(document: dict) -> list[dict]:
    active = document.get("activeTimelineId")
    for timeline in document.get("timelines", []):
        if timeline.get("id") == active:
            return timeline["clips"]
    return document["clips"]


def run() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--runtime-bundle", type=Path, help="Windows DLLs from the validated desktop stage")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    cli = args.cli.resolve(strict=True)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report: dict = {"status": "RUNNING", "scope": "real native project open, text edit, cut, save and H264/AAC export; not touch UI or physical-phone performance", "cli": str(cli)}
    api = None
    success = False
    started_at = time.monotonic()
    try:
        if args.runtime_bundle:
            runtime = out / "runtime"
            runtime.mkdir()
            shutil.copy2(cli, runtime / cli.name)
            for dll in args.runtime_bundle.resolve(strict=True).glob("*.dll"):
                shutil.copy2(dll, runtime / dll.name)
            (runtime / "portable").mkdir()
            cli = runtime / cli.name
        fixture = ROOT / "examples/venka-reel-9x16"
        project = out / "project"
        subprocess.run([sys.executable, str(fixture / "prepare.py"), "--output", str(project)], check=True, timeout=30)
        project_path = str(project)
        api = NativeApi(cli, out)
        version = api.call("version")
        if version.get("apiVersion") != "0.2" or not version.get("concat"):
            raise AssertionError(f"Unexpected native API contract: {version}")
        opened = api.call("project.open", path=project_path)
        if (opened["settings"]["width"], opened["settings"]["height"], opened["settings"]["rateNum"], opened["settings"]["rateDen"]) != (1080, 1920, 30, 1):
            raise AssertionError(f"Wrong native project settings: {opened['settings']}")
        original = api.call("project.document", path=project_path)
        # `concat` in the saved document is a historical format marker
        # (the native writer uses 0.1.0), not the application's build version.
        if original.get("version") != 1:
            raise AssertionError(f"Unexpected native document version: {original.get('version')}")
        original_clips = clips(original)
        if len(original_clips) != 5:
            raise AssertionError(f"Fixture did not open with five clips: {original_clips}")
        style = dict(next(clip for clip in original_clips if clip["id"] == "c3")["text"])
        style["content"] = "VENKA IMÓVEIS\nREEL TESTADO"
        api.call("edit.apply", path=project_path, command={"op": "updateClip", "clipId": "c3", "patch": {"text": style}})
        api.call("edit.apply", path=project_path, command={"op": "splitClips", "clipIds": ["c1"], "time": 2.0})
        edited = api.call("project.document", path=project_path)
        edited_clips = clips(edited)
        if next(clip for clip in edited_clips if clip["id"] == "c3")["text"]["content"] != style["content"]:
            raise AssertionError("Native text edit was not applied")
        pieces = sorted((clip for clip in edited_clips if clip.get("mediaId") == "m1"), key=lambda clip: clip["start"])
        if len(pieces) != 2 or any(abs(clip["duration"] - 2) > 0.001 for clip in pieces) or [clip["start"] for clip in pieces] != [0, 2]:
            raise AssertionError(f"Native two-second cut not applied: {pieces}")
        api.call("project.save", path=project_path)
        export_path = out / "venka-native-reel.mp4"
        job = api.call("export.run", path=project_path, output=str(export_path), width=1080, height=1920, rateNum=30, rateDen=1, codec="h264", preset="ultrafast", crf=23, hdr=False)
        done = api.wait_export(job["job"], args.timeout)
        if Path(done["output"]).resolve() != export_path or (done["width"], done["height"]) != (1080, 1920):
            raise AssertionError(f"Export completion described a different output: {done}")
        api.close(True)
        api = None
        ffprobe = shutil.which("ffprobe")
        ffmpeg = shutil.which("ffmpeg")
        if not ffprobe or not ffmpeg:
            raise RuntimeError("FFmpeg and ffprobe must be available on PATH")
        probe = json.loads(subprocess.check_output([ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(export_path)], text=True, encoding="utf-8", timeout=30))
        (out / "ffprobe.json").write_text(json.dumps(probe, indent=2), encoding="utf-8")
        video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
        audio = next(stream for stream in probe["streams"] if stream["codec_type"] == "audio")
        if (video["codec_name"], video["width"], video["height"], Fraction(video["avg_frame_rate"])) != ("h264", 1080, 1920, Fraction(30)):
            raise AssertionError(f"Unexpected exported video format: {video}")
        if audio["codec_name"] != "aac" or not 3.8 <= float(probe["format"]["duration"]) <= 4.2:
            raise AssertionError(f"Unexpected audio or duration: {probe}")
        subprocess.run([ffmpeg, "-v", "error", "-xerror", "-i", str(export_path), "-f", "null", "-"], check=True, timeout=120, capture_output=True)
        pcm = subprocess.check_output([ffmpeg, "-v", "error", "-i", str(export_path), "-vn", "-ac", "1", "-ar", "8000", "-f", "f32le", "pipe:1"], timeout=60)
        samples = array("f", pcm)
        rms = math.sqrt(sum(sample * sample for sample in samples) / len(samples)) if samples else 0
        if rms < 0.001:
            raise AssertionError("The fixture's test tone is missing or effectively silent in the native export")
        for instant in (0.7, 2.7):
            subprocess.run([ffmpeg, "-v", "error", "-ss", str(instant), "-i", str(export_path), "-frames:v", "1", str(out / f"frame-{instant}.png")], check=True, timeout=60, capture_output=True)
        digest = hashlib.sha256(export_path.read_bytes()).hexdigest()
        report.update(status="PASS", version=version, native_export_done=done, edits={"title": style["content"], "base_video_cut_seconds": 2.0, "video_pieces": pieces}, output={"file": export_path.name, "bytes": export_path.stat().st_size, "sha256": digest, "width": 1080, "height": 1920, "fps": "30/1", "duration": float(probe["format"]["duration"]), "video_codec": "h264", "audio_codec": "aac", "audio_rms": rms, "full_decode": "PASS"})
        success = True
    except Exception as error:
        report.update(status="FAIL", error=str(error))
        raise
    finally:
        if api:
            api.close(False)
        report["elapsed_seconds"] = round(time.monotonic() - started_at, 3)
        (out / "QA_REEL_RESULT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if not success:
            print(f"Native QA failed. Evidence preserved under {out}", file=sys.stderr)


if __name__ == "__main__":
    run()
