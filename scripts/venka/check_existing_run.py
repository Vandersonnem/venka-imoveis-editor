#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Venka Imóveis
"""Validate native jobs and artifact provenance before collecting an older run."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re

REQUIRED = {
    "desktop / windows-x86_64": ["Smoke test (Windows)", "Native Reels editing and export (9:16, 1080x1920, 30 fps)"],
    "desktop / macos-arm64": ["Smoke test (macOS)", "Native Reels editing and export (9:16, 1080x1920, 30 fps)"],
    "mobile / iOS arm64": ["Bundle"],
    "mobile / Android x86_64": ["Stage"],
    "mobile / iOS simulator smoke": ["Start the app on a simulator"],
    "mobile / Android arm64": ["Stage"],
}
ARTIFACTS = {"Venka-Editor-windows-x86_64", "Venka-Editor-macos-arm64", "Venka-Editor-android-arm64", "Venka-Editor-ios-arm64"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--jobs", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run = json.loads(args.run.read_text(encoding="utf-8"))
    job_pages = json.loads(args.jobs.read_text(encoding="utf-8"))
    artifact_pages = json.loads(args.artifacts.read_text(encoding="utf-8"))
    jobs = [job for page in job_pages for job in page["jobs"]]
    artifacts = [artifact for page in artifact_pages for artifact in page["artifacts"]]
    if run.get("repository", {}).get("full_name") != args.repository or run.get("path") != ".github/workflows/build.yml":
        raise ValueError("The original run is not the Venka build workflow from this repository")
    if run.get("status") != "completed":
        raise ValueError("The original run is still active. Preserve it and collect only after it completes.")
    head_sha = run["head_sha"]
    if not re.fullmatch(r"[a-f0-9]{40}", head_sha):
        raise ValueError("Invalid original head SHA")
    checked = []
    for name, required_steps in REQUIRED.items():
        matching = [job for job in jobs if job["name"] == name]
        if len(matching) != 1 or matching[0].get("conclusion") != "success":
            raise ValueError(f"Native job is missing or did not succeed: {name}: {matching}")
        job = matching[0]
        for step_name in required_steps:
            steps = [step for step in job.get("steps", []) if step["name"] == step_name]
            if len(steps) != 1 or steps[0].get("conclusion") != "success":
                raise ValueError(f"Native step did not succeed: {name}: {step_name}")
        checked.append({"name": name, "id": job["id"], "url": job["html_url"], "conclusion": job["conclusion"], "checked_steps": required_steps})
    # Dependency jobs may be materialized later than the six initial jobs.
    # Their absence does not introduce a platform requirement; a real failed
    # native/emulator job, however, must never be hidden by a new green collector.
    additional = [job for job in jobs if job["name"].startswith(("desktop /", "mobile /")) and job["name"] not in REQUIRED]
    failed = [job for job in additional if job.get("conclusion") != "success"]
    if failed:
        raise ValueError(f"Additional native smoke jobs did not succeed: {failed}")
    available = {artifact["name"]: artifact for artifact in artifacts if not artifact.get("expired") and artifact.get("size_in_bytes", 0) > 0}
    if missing := ARTIFACTS - available.keys():
        raise ValueError(f"Original native artifacts are absent or expired: {sorted(missing)}")
    result = {"status": "PASS", "checked_at": datetime.now(timezone.utc).isoformat(), "repository": args.repository,
              "head_sha": head_sha, "run": {"id": run["id"], "attempt": run["run_attempt"], "url": run["html_url"], "conclusion": run["conclusion"], "workflow": run["path"]},
              "native_jobs": checked, "additional_smokes": [{"name": job["name"], "id": job["id"], "conclusion": job["conclusion"], "url": job["html_url"]} for job in additional],
              "artifacts": [{key: available[name].get(key) for key in ("id", "name", "size_in_bytes", "digest", "archive_download_url", "expires_at")} for name in sorted(ARTIFACTS)],
              "scope": "native jobs and existing artifacts verified; collector itself does not rebuild or certify physical phones"}
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if output := os.environ.get("GITHUB_OUTPUT"):
        with open(output, "a", encoding="utf-8") as stream:
            stream.write(f"compiled_sha={head_sha}\nrun_id={run['id']}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
