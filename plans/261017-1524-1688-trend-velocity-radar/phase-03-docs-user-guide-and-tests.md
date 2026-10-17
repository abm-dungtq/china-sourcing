# Phase 3 — User Guide Documentation, Unit Tests & Live Verification

## Goal
Update all user-facing guides (`HUONG_DAN_SU_DUNG_CHINA_SOURCING.md`, `README.md`, `SKILL.md`, `references/platform-playbooks.md`, and `build_onboarding_guide()`) with clear Vietnamese instructions and copy-paste prompts for scanning hot new products, fast-rising sales, and 1688 trends. Expand `scripts/tests/test_china_sourcing.py` to `>= 24` unit tests, run a live logged-in verification (`trends --keyword "护眼台灯"`), and sync global agent skill directories via `bash scripts/install.sh`.

## Files to Create or Modify
- `HUONG_DAN_SU_DUNG_CHINA_SOURCING.md` (modify)
- `README.md` (modify)
- `SKILL.md` (modify)
- `references/platform-playbooks.md` (modify)
- `scripts/china_sourcing.py` (modify `build_onboarding_guide`)
- `scripts/tests/test_china_sourcing.py` (modify)

## Tasks & Steps

### Task 3.1 — Add Comprehensive User Guides for 1688 Trend & Velocity Radar
- **Goal:** Ensure users and AI Agents know how to use the new 1688 Hot Products, Sales Velocity, and Trend Radar feature both via natural-language chat prompts and via CLI commands.
- **Target files and symbols:** `HUONG_DAN_SU_DUNG_CHINA_SOURCING.md`, `README.md`, `SKILL.md`, `references/platform-playbooks.md`, `scripts/china_sourcing.py` (`build_onboarding_guide`).
- **Steps:**
  1. In `HUONG_DAN_SU_DUNG_CHINA_SOURCING.md`:
     - Add **Kịch bản 6: Quét sản phẩm mới đang hot, lượt bán tăng nhanh & bắt trend ngách 1688 (`trends`)** with natural-language prompt examples (e.g., *"Quét giúp tôi các mẫu quạt cầm tay mini mới ra đang hot, lượt bán tăng nhanh nhất trên 1688 và các ngách xu hướng đang lên kèm giá vốn về Việt Nam"*), explanation of the 4 signal groups (`上新`, `飙升`, `商机组货`, `排行榜`), and CLI usage (`trends --keyword ... --mode all --state-file ...`).
  2. In `README.md`:
     - Update the weapons & copy-paste prompt sections to include the 1688 Trend & Velocity Radar prompt and CLI example.
  3. In `SKILL.md`, `references/platform-playbooks.md`, and `build_onboarding_guide()` in `scripts/china_sourcing.py`:
     - Add routing and onboarding instructions for `python3 scripts/china_sourcing.py trends` and bump version in `SKILL.md` to `2.1.0`.
- **Success criteria:** All 4 documentation files and `build_onboarding_guide()` include clear Vietnamese instructions for `trends`.
- **Verify:** `grep -q "trends" /Volumes/1/AGY/china-sourcing/HUONG_DAN_SU_DUNG_CHINA_SOURCING.md /Volumes/1/AGY/china-sourcing/README.md /Volumes/1/AGY/china-sourcing/SKILL.md` exits 0.

### Task 3.2 — Expand Unit Test Suite (`>= 24` Tests) & Run Live Logged-In 1688 Trend Scan
- **Goal:** Verify all new functions (`parse_cn_count`, `compute_offer_trend_metrics`, `analyze_1688_trends`, snapshot delta velocity, `search-mtop.js` patch verification) with unit tests and run a live `trends` scan on the logged-in 1688 session (`tdhwhosales`).
- **Target files and symbols:** `scripts/tests/test_china_sourcing.py`.
- **Steps:**
  1. Add 6 new unit tests in `scripts/tests/test_china_sourcing.py`:
     - `test_parse_cn_count_variants`
     - `test_velocity_index_log_damped_prevents_small_sample_bias`
     - `test_analyze_1688_trends_clusters_and_leaderboards`
     - `test_analyze_1688_trends_stateful_snapshot_delta`
     - `test_format_trends_markdown_sections`
     - `test_doctor_verifies_four_1688_cli_patches_including_search_mtop`
  2. Run `python3 -m unittest discover -s scripts/tests -v`.
  3. Run `bash scripts/install.sh` to sync the updated skill and apply the 4 `1688-cli` patches globally.
  4. Run a live verification command:
     `python3 scripts/china_sourcing.py trends --keyword "护眼台灯" --max 20 --qty 100 --output-json /tmp/test_trends_live.json --output-md /tmp/test_trends_live.md` and verify that it succeeds (`exit 0`) and populates `hot_new_offers`, `fast_rising_offers`, and `niche_trend_clusters`.
- **Success criteria:** All `>= 24` unit tests pass (`OK`) and live 1688 `trends` command exits 0 with real data.
- **Verify:** `python3 -m unittest discover -s /Volumes/1/AGY/china-sourcing/scripts/tests -v` exits 0 and prints `OK`.

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
