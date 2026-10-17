# Phase 2 — 1688 Trends & Velocity Engine (`trends` Subcommand & `report` Enrichment)

## Goal
Implement the pure-Python trend & velocity scoring engine (`parse_cn_count`, `compute_offer_trend_metrics`, `analyze_1688_trends`, `run_1688_trends`) and the `trends` CLI subcommand in `scripts/china_sourcing.py`, plus enrich `generate_sourcing_report()` with trend/new-product badges when present.

## Files to Create or Modify
- `scripts/china_sourcing.py` (modify: add `parse_cn_count`, `compute_offer_trend_metrics`, `analyze_1688_trends`, `run_1688_trends`, `trends` parser in `build_parser()`, `trends` handler in `main()`, and trend badge column/notes in `generate_sourcing_report()`)

## Tasks & Steps

### Task 2.1 — Implement `parse_cn_count` and `compute_offer_trend_metrics` with Log-Damped `VelocityIndex`
- **Goal:** Accurately parse Chinese sales/percentage strings (`"已售3.4万+件"`, `"小于10件"`, `"28%"`) and score every offer on **Hot New Score (`0-100`)** and **Fast-Rising Velocity Score (`0-100`)** without small-denominator distortion.
- **Target files and symbols:** `scripts/china_sourcing.py` (`parse_cn_count`, `compute_offer_trend_metrics`).
- **Steps:**
  1. Add `parse_cn_count(text: Any) -> int | None` handling numbers, `"3.4万+件"` ($\to 34000$), `"1.2w"` ($\to 12000$), `"500+件"` ($\to 500$), and returning `0` for `"小于10"` / `"0"`.
  2. Add `compute_offer_trend_metrics(offer: dict[str, Any], prev_snapshot: dict[str, Any] | None = None, elapsed_hours: float | None = None) -> dict[str, Any]`:
     - Extract `booked_30d` from `offer["demand"]["orderCount"]` or `parse_cn_count(offer.get("turnover"))`.
     - Extract `sold_total` from `trendSignals.soldCountTotal` or `parse_cn_count(trendSignals.soldCountText)` (fallback to `booked_30d`).
     - Compute clamped 30-day recency share:
       `recency_share = min(1.0, max(0.0, booked_30d / max(sold_total, booked_30d, 50)))`
     - Compute `velocity_index = math.log10(booked_30d + 1) * (0.5 + 0.5 * recency_share)` (scaled to a 0–100 `fast_rising_score` with additive bonuses for `rankBadges` `+20`, `priceCompetitiveBadges` `+10`, `repurchase_rate >= 20%` `+10`, and positive snapshot `delta_orders_per_day` `+15`).
     - Compute `hot_new_score` (0–100): base points from `newProductSellPoints` (`+40`), `fenxiaoNewOffer` (`+15`), `businessOppoTopics` with recent `topicDate` (`+20`), plus `min(25, round(math.log10(booked_30d + 1) * 6))`.
     - If `prev_snapshot` has a previous `booked_30d` for this `offerId`, compute `delta_orders = booked_30d - prev_booked` and `delta_orders_per_day`.
- **Success criteria:** Pure functions exist in `scripts/china_sourcing.py` and handle both patched `trendSignals` offers and fallback raw offers cleanly.
- **Verify:** `python3 -c "import sys; sys.path.insert(0, 'scripts'); import china_sourcing as cs; assert cs.parse_cn_count('已售3.4万+件') == 34000; print('OK')"` exits 0 and prints `OK`.

### Task 2.2 — Implement `analyze_1688_trends`, `run_1688_trends`, and CLI `trends` subcommand
- **Goal:** Provide `python3 scripts/china_sourcing.py trends` to scan/analyze 1688 keywords for hot new products (`new-hot`), fast-growing sales (`fast-rising`), and emerging niche trends (`niche-trends`), complete with estimated Vietnam Landed Cost (`TMĐT` & `Chính ngạch`), direct 1688 Leaderboard URLs (`热销榜`, `飙升榜`, `新品榜`), and optional Markdown + JSON output.
- **Target files and symbols:** `scripts/china_sourcing.py` (`analyze_1688_trends`, `format_trends_markdown`, `run_1688_trends`, `build_parser`, `main`).
- **Steps:**
  1. Implement `analyze_1688_trends(offers, keyword, mode="all", target_qty=100, exchange_rate_vnd=DEFAULT_EXCHANGE_RATE_VND, vn_shipping_per_kg_vnd=DEFAULT_VN_SHIPPING_PER_KG_VND, state_file_path=None)`:
     - Load previous snapshot from `state_file_path` if provided, compute `elapsed_hours`, score all offers via `compute_offer_trend_metrics`, and save updated snapshot atomically.
     - Rank **Top Hot New Products (`hot_new_offers`)**, **Top Fast-Rising Sales (`fast_rising_offers`)**, **Niche Trend Clusters (`niche_trend_clusters` grouped by `商机组货` topic)**, and **Official 1688 Category Leaderboards (`category_leaderboards` with generated `rankType=1` 热销榜, `rankType=2` 飙升榜, `rankType=3` 新品榜 URLs)**.
     - Compute Vietnam Landed Cost (`calculate_landed_cost`) for each top offer at `target_qty`.
  2. Implement `format_trends_markdown(report_data)` producing a clear Vietnamese Markdown report with tables for:
     - **1. Sản phẩm mới đang Hot (`上新热销 / New & Hot`)**
     - **2. Sản phẩm có lượt bán tăng tốc nhanh (`飙升 / Fast-Rising Velocity`)**
     - **3. Cụm xu hướng ngách đang lên (`商机组货 / Emerging Niche Trends`)**
     - **4. Bảng xếp hạng chính thức 1688 (`1688 排行榜`: Bán chạy · Tăng tốc · Hàng mới)**
  3. Wire `trends` subcommand in `build_parser()` and `main()` supporting:
     - `--keyword` / `-k` (one or more Chinese keywords)
     - `--input` (optional path to existing search JSON for offline/replay analysis)
     - `--mode` (`all`, `new-hot`, `fast-rising`, `niche-trends`, default `all`)
     - `--max` (default `40`), `--qty` (default `100`), `--price-max`, `--factory-only`
     - `--state-file` (optional path to `trends_state.json` for delta velocity tracking)
     - `--output-json` and `--output-md`.
- **Success criteria:** `python3 scripts/china_sourcing.py trends --help` displays all flags and `trends` executes end-to-end on both live 1688 search and `--input` JSON fixtures.
- **Verify:** `python3 /Volumes/1/AGY/china-sourcing/scripts/china_sourcing.py trends --help` exits 0 and prints `--mode {all,new-hot,fast-rising,niche-trends}`.

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
