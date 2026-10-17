# Phase 01 — Vendor Patch (`1688-cli@0.1.47`), Self-Healing `doctor --fix`, and Repo Hygiene

- **Status:** completed
- **Priority:** P1
- **Effort:** 1h
- **Dependencies:** none

## Goal
Package the 3 hot-patched `1688-cli` command files (`seller-chat.js`, `seller-inquire.js`, `seller-messages.js`) into `patches/1688-cli/`, add self-healing verification/application (`doctor --fix`) in `scripts/china_sourcing.py`, remove duplicate files in `docs/`, `assets/`, and `examples/`, and restrict `scripts/install.sh` `rsync` to runtime skill directories only.

## Files to Create or Modify
- **Create:** `/Volumes/1/AGY/china-sourcing/patches/1688-cli/seller-chat.js`
- **Create:** `/Volumes/1/AGY/china-sourcing/patches/1688-cli/seller-inquire.js`
- **Create:** `/Volumes/1/AGY/china-sourcing/patches/1688-cli/seller-messages.js`
- **Create:** `/Volumes/1/AGY/china-sourcing/patches/1688-cli/patch-meta.json`
- **Modify:** `/Volumes/1/AGY/china-sourcing/scripts/china_sourcing.py` (`inspect_1688_status`, `verify_and_patch_1688_cli`, `run_doctor`, `build_parser`, `main`)
- **Modify:** `/Volumes/1/AGY/china-sourcing/scripts/install.sh`
- **Delete:** `/Volumes/1/AGY/china-sourcing/docs/HUONG_DAN_SU_DUNG_CHINA_SOURCING.md`
- **Delete:** `/Volumes/1/AGY/china-sourcing/assets/07_wangwang_proof_1_624406159076.png` (and `2..5` duplicate PNGs in `assets/`, keeping `assets/wangwang-proof-demo.png` and the 5 canonical PNGs in `examples/run-20261017-0831-den-ban-chong-can/`)
- **Delete:** `/Volumes/1/AGY/china-sourcing/examples/run-20261017-0831-den-ban-chong-can/07_receipt_2.json` (and `07_receipt_3.json`, `07_receipt_4.json`, `07_receipt_5.json`)

## Tasks & Steps

### Task 1.1 — Vendor `1688-cli@0.1.47` patched command files and `patch-meta.json`
- **Goal:** Store the exact patched `seller-chat.js`, `seller-inquire.js`, and `seller-messages.js` files inside the repository with SHA-256 checksums.
- **Target files and symbols:**
  - `/Volumes/1/AGY/china-sourcing/patches/1688-cli/seller-chat.js`
  - `/Volumes/1/AGY/china-sourcing/patches/1688-cli/seller-inquire.js`
  - `/Volumes/1/AGY/china-sourcing/patches/1688-cli/seller-messages.js`
  - `/Volumes/1/AGY/china-sourcing/patches/1688-cli/patch-meta.json`
- **Steps:**
  1. Copy `seller-chat.js`, `seller-inquire.js`, and `seller-messages.js` from `/opt/homebrew/lib/node_modules/1688-cli/dist/commands/` into `/Volumes/1/AGY/china-sourcing/patches/1688-cli/`.
  2. Compute the SHA-256 hex digest of each of the 3 files and write `/Volumes/1/AGY/china-sourcing/patches/1688-cli/patch-meta.json` with `package: "1688-cli"`, `tested_version: "0.1.47"`, `markers: {"seller-chat.js": "args.screenshotPath", "seller-inquire.js": "BB1688_SCREENSHOT_PATH", "seller-messages.js": "opts.offer"}`, and `sha256` per file.
- **Success criteria:** All 3 JS files and `patch-meta.json` exist in `/Volumes/1/AGY/china-sourcing/patches/1688-cli/` with non-empty SHA-256 digests.
- **Verify:** `python3 -c 'import json, pathlib; p=pathlib.Path("patches/1688-cli/patch-meta.json"); d=json.loads(p.read_text()); assert d["tested_version"]=="0.1.47" and len(d["files"])==3; print("PATCH_META_OK")'` exits 0 and prints `PATCH_META_OK`.

### Task 1.2 — Implement `verify_and_patch_1688_cli` and `doctor --fix` in `scripts/china_sourcing.py`
- **Goal:** Detect the installed `1688-cli` dist directory (via `realpath` of `shutil.which("1688")` or `npm root -g`), verify patch markers/checksums in `inspect_1688_status()`, and apply vendored patches when `doctor --fix` is invoked.
- **Target files and symbols:**
  - `/Volumes/1/AGY/china-sourcing/scripts/china_sourcing.py` (`resolve_1688_dist_dir`, `verify_and_patch_1688_cli`, `inspect_1688_status`, `run_doctor`, `build_parser`, `main`)
- **Steps:**
  1. Add `resolve_1688_dist_dir() -> Path | None` that resolves `Path(shutil.which("1688")).resolve().parent` (where `cli.js` lives, i.e., `.../1688-cli/dist`) or falls back to `npm root -g`.
  2. Add `verify_and_patch_1688_cli(apply_patch: bool = False, dist_dir: Path | None = None) -> dict[str, Any]` that checks `patches/1688-cli/patch-meta.json` markers and SHA-256 hashes against `dist/commands/{seller-chat,seller-inquire,seller-messages}.js`. When `apply_patch=True` and any file is unpatched, atomically copy the vendored files from `patches/1688-cli/` and re-verify.
  3. Include `"patched": patch_status["patched"]` and `"patch_detail": patch_status` inside `inspect_1688_status()` and `run_doctor(output_path, fix=...)`, and add `--fix` to the `doctor` subparser in `build_parser()`.
- **Success criteria:** `python3 scripts/china_sourcing.py doctor --fix` reports `"patched": true` inside `tools.1688_cli`.
- **Verify:** `python3 scripts/china_sourcing.py doctor --fix | python3 -c 'import sys, json; d=json.load(sys.stdin); assert d["tools"]["1688_cli"]["patched"] is True; print("DOCTOR_PATCH_OK")'` exits 0 and prints `DOCTOR_PATCH_OK`.

### Task 1.3 — Remove duplicate repo files and tighten `scripts/install.sh`
- **Goal:** Eliminate duplicate documentation/screenshots/stray receipts and prevent `scripts/install.sh` from copying non-runtime folders (`examples/`, `docs/`, `assets/`, `plans/`, `scripts/tests/`) into global agent skill directories.
- **Target files and symbols:**
  - `/Volumes/1/AGY/china-sourcing/scripts/install.sh`
  - `/Volumes/1/AGY/china-sourcing/docs/HUONG_DAN_SU_DUNG_CHINA_SOURCING.md`
  - `/Volumes/1/AGY/china-sourcing/assets/07_wangwang_proof_*.png`
  - `/Volumes/1/AGY/china-sourcing/examples/run-20261017-0831-den-ban-chong-can/07_receipt_*.json`
- **Steps:**
  1. Delete `/Volumes/1/AGY/china-sourcing/docs/HUONG_DAN_SU_DUNG_CHINA_SOURCING.md`, `/Volumes/1/AGY/china-sourcing/assets/07_wangwang_proof_1_624406159076.png` through `07_wangwang_proof_5_858955223080.png`, and `examples/run-20261017-0831-den-ban-chong-can/07_receipt_2.json` through `07_receipt_5.json`.
  2. Update `/Volumes/1/AGY/china-sourcing/scripts/install.sh`:
     - Exclude `.git`, `examples`, `docs`, `assets`, `plans`, `runs`, `scripts/tests`, `__pycache__`, and `.DS_Store` in `rsync`.
     - Pin `npm install -g 1688-cli@0.1.47 || true`.
     - Run `python3 "$SRC_DIR/scripts/china_sourcing.py" doctor --fix >/dev/null 2>&1 || true` right after `1688-cli` check/install so every target machine gets the WangWang screenshot & `--offer` patches automatically.
- **Success criteria:** Duplicate files are removed and `scripts/install.sh` excludes heavy directories and runs `doctor --fix`.
- **Verify:** `test ! -f docs/HUONG_DAN_SU_DUNG_CHINA_SOURCING.md && test ! -f assets/07_wangwang_proof_1_624406159076.png && test ! -f examples/run-20261017-0831-den-ban-chong-can/07_receipt_2.json && grep -q "doctor --fix" scripts/install.sh && echo "HYGIENE_OK"` exits 0 and prints `HYGIENE_OK`.

## Failure Protocol
If any Verify step does not meet its stated pass condition, STOP this phase.
Do not improvise a fix, retry blindly, or reason around the failure.
Spawn the `kongming` subagent for next-step counsel and pass:
- the phase and task id,
- what you attempted (the steps you ran),
- the exact command and its full output,
- the pass condition it failed to meet.
Apply kongming's guidance, then re-run the Verify step.
If `kongming` cannot be spawned in this environment, STOP and report the same
failure evidence to the user. Never continue by self-reasoning.
