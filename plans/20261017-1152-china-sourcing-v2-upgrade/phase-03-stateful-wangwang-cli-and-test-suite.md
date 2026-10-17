# Phase 03 — Stateful WangWang CLI (`inquire-wangwang` & `check-wangwang`), Docs Sync, and 18+ Unit Tests

- **Status:** completed
- **Priority:** P1
- **Effort:** 1h
- **Dependencies:** `phase-02-landed-cost-math-and-shortlink-resolver.md`

## Goal
Implement the code-enforced Idempotency Gate (`inquire-wangwang` subcommand writing to `07_inquiry_receipt.json`), upgrade `check_wangwang_replies()` to filter out `autoReply`/system notices and track delta cursor state via atomic `--state-file` writes, synchronize `SKILL.md` and `references/platform-playbooks.md`, expand `scripts/tests/test_china_sourcing.py` to $\ge 18$ unit tests, and run `scripts/install.sh`.

## Files to Create or Modify
- **Modify:** `/Volumes/1/AGY/china-sourcing/scripts/china_sourcing.py` (`is_human_seller_reply`, `compute_inquiry_idempotency_key`, `inquire_wangwang`, `check_wangwang_replies`, `build_parser`, `main`)
- **Modify:** `/Volumes/1/AGY/china-sourcing/scripts/tests/test_china_sourcing.py`
- **Modify:** `/Volumes/1/AGY/china-sourcing/SKILL.md`
- **Modify:** `/Volumes/1/AGY/china-sourcing/references/platform-playbooks.md`

## Tasks & Steps

### Task 3.1 — Implement `inquire-wangwang` Idempotency Gate and Stateful `check-wangwang`
- **Goal:** Enforce `sha256(run_id + offer_id + inquiry_text_hash)` before sending WangWang inquiries, classify human vs. auto/system replies accurately, and support stateful delta polling (`--state-file` / `--only-new`).
- **Target files and symbols:**
  - `/Volumes/1/AGY/china-sourcing/scripts/china_sourcing.py` (`SYSTEM_NOTICE_PATTERNS`, `is_human_seller_reply`, `message_signature`, `compute_inquiry_idempotency_key`, `inquire_wangwang`, `check_wangwang_replies`, `build_parser`, `main`)
- **Steps:**
  1. Add `is_human_seller_reply(msg: dict[str, Any]) -> bool`:
     - Return `False` if `not isinstance(msg, dict)` or `msg.get("isMine")`.
     - Return `False` if `msg.get("kind") in ("assessment", "autoReply", "other", "offerCard", "orderCard", "system", "notice")`.
     - Check `content = str(msg.get("content") or "").strip()`: return `False` if empty or matching known platform system/auto-reply templates (`^\[卡片消息\]$`, `^\[contentType=`, `商家长时间没有回复，平台已通知商家`, `由于当前是节假日期间，卖家可能无法马上回复`, `客服现在比较繁忙，稍等一会马上来回复`).
     - Otherwise return `True` (preserving short genuine human replies like `"可以"`, `"有货的"`, `"单色logo"`).
  2. Update `check_wangwang_replies()`:
     - Accept `state_file_path: str | None = None` and `only_new: bool = False`.
     - Load previously seen message keys from `state_file_path` (if provided and exists).
     - For each conversation, compute `human_replies`, `auto_or_system_messages`, and `new_human_replies` (messages in `human_replies` whose `message_signature(m)` is not in `seen_keys`).
     - Keep `seller_replies = human_replies` and `seller_replies_count = len(human_replies)` so auto-reply noise is never counted as a seller reply, while exposing `auto_or_system_messages`, `new_human_replies`, `new_human_replies_count`, and top-level `has_new_human_replies: bool`.
     - Atomically persist updated `seen_keys` to `state_file_path` via `.tmp` + `os.replace()`.
  3. Add `inquire_wangwang(...)` and the `inquire-wangwang` subparser (`--run-id`, `--offer-id`, `--message`, `--seller`, `--rank`, `--supplier`, `--receipt`, `--screenshot`, `--force`):
     - Compute `idempotency_key = compute_inquiry_idempotency_key(run_id, offer_id, message)`.
     - Load `--receipt` (`07_inquiry_receipt.json`) if it exists; if an entry with the same `idempotency_key` (or `offer_id` + `idempotency_key`) already succeeded and `not force`, return `{"ok": True, "status": "skipped_duplicate", "idempotency_key": idempotency_key, ...}` without invoking `1688`.
     - Otherwise run `1688 seller inquire <offer_id> <message> [--to <seller>] --json` with `BB1688_SCREENSHOT_PATH` set in `env`, append/update the receipt entry in `07_inquiry_receipt.json` atomically, and return the result.
- **Success criteria:** Running `check_wangwang_replies()` on `examples/run-20261017-0831-den-ban-chong-can/08_wangwang_poll.json` conversation #1 (`恒悦亮电器厂`, which only has `[卡片消息]`, busy notice, and platform timeout notice) yields `0` human replies and `3` `auto_or_system_messages`, while conversation #2 (`视力童`) yields `3` human replies (`"单色logo"`, `"可以"`, `"有货的"`).
- **Verify:** `python3 -c 'import json, sys; sys.path.insert(0, "scripts"); import china_sourcing as cs; d=json.loads(open("examples/run-20261017-0831-den-ban-chong-can/08_wangwang_poll.json").read()); c1=[m for m in d["conversations"][0]["all_messages"] if cs.is_human_seller_reply(m)]; c2=[m["content"] for m in d["conversations"][1]["all_messages"] if cs.is_human_seller_reply(m)]; assert len(c1)==0 and c2==["单色logo", "可以", "有货的"]; print("WANGWANG_FILTER_OK")'` exits 0 and prints `WANGWANG_FILTER_OK`.

### Task 3.2 — Expand Unit Test Suite (`scripts/tests/test_china_sourcing.py`) and Sync Docs/Install
- **Goal:** Add comprehensive unit tests covering all 6 upgraded areas ($\ge 18$ total tests), update `SKILL.md` and `references/platform-playbooks.md`, and run `bash scripts/install.sh` to sync the clean v2.0 skill across all agent directories.
- **Target files and symbols:**
  - `/Volumes/1/AGY/china-sourcing/scripts/tests/test_china_sourcing.py`
  - `/Volumes/1/AGY/china-sourcing/SKILL.md`
  - `/Volumes/1/AGY/china-sourcing/references/platform-playbooks.md`
- **Steps:**
  1. Add at least 10 new unit test methods in `scripts/tests/test_china_sourcing.py` (bringing total from 8 to $\ge 18$), including:
     - `test_report_uses_price_tiers_for_target_qty`
     - `test_report_converts_cm3_volume_to_cbm`
     - `test_small_gram_weight_not_inflated_to_kg`
     - `test_volumetric_weight_disambiguation`
     - `test_check_wangwang_filters_autoreply_and_cards`
     - `test_check_wangwang_stateful_delta_only`
     - `test_inquire_wangwang_idempotency_blocks_duplicate`
     - `test_parse_short_link_redirect_resolution_mocked`
     - `test_doctor_detects_and_fixes_1688_cli_patch`
     - `test_alibaba_subcommand_output`
  2. Update `SKILL.md` and `references/platform-playbooks.md` to document `doctor --fix`, `parse-link --resolve`, `inquire-wangwang`, `check-wangwang --state-file`, and `alibaba --query`.
  3. Run `bash scripts/install.sh` and verify that global skill directories contain `SKILL.md`, `scripts/`, `references/`, `patches/` and do NOT contain `examples/`, `docs/`, `assets/`, or `plans/`.
- **Success criteria:** All $\ge 18$ unit tests pass and global skill directories are clean and up to date.
- **Verify:** `python3 -m unittest discover -s scripts/tests -v && bash scripts/install.sh && test ! -d ~/.gemini/config/skills/china-sourcing/examples && echo "ALL_TESTS_AND_INSTALL_OK"` exits 0 and prints `ALL_TESTS_AND_INSTALL_OK`.

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
