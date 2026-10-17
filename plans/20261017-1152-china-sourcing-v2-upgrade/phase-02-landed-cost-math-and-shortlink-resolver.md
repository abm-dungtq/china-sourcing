# Phase 02 — Accurate Landed-Cost Math (`priceTiers`, CBM Volume, Volumetric Weight) & Short-Link Redirect Resolver

- **Status:** completed
- **Priority:** P1
- **Effort:** 1h
- **Dependencies:** `phase-01-vendor-patch-and-repo-hygiene.md`

## Goal
Fix the 3 mathematical/unit defects in `generate_sourcing_report()` (`priceTiers` matching for `target_qty`, `packageInfo[].volume` $\text{cm}^3 \to \text{m}^3$ conversion, and 3-tiered gram/kg weight disambiguation including $\le 10\text{g}$ items), implement short-link HTTP redirect resolution in `parse_share_link()`, and add the `alibaba` CLI subcommand.

## Files to Create or Modify
- **Modify:** `/Volumes/1/AGY/china-sourcing/scripts/china_sourcing.py` (`resolve_tier_price_cny`, `extract_package_metrics`, `generate_sourcing_report`, `resolve_short_url`, `parse_share_link`, `run_alibaba_search`, `build_parser`, `main`)

## Tasks & Steps

### Task 2.1 — Implement `resolve_tier_price_cny` and `extract_package_metrics` in `scripts/china_sourcing.py`
- **Goal:** Accurately select quantity-based wholesale price tiers (`minQty <= target_qty`), convert `packageInfo[].volume` from $\text{cm}^3$ to $\text{m}^3$, and disambiguate gram vs. kg weights without inflating $\le 10\text{g}$ items by $1,000\times$.
- **Target files and symbols:**
  - `/Volumes/1/AGY/china-sourcing/scripts/china_sourcing.py` (`resolve_tier_price_cny`, `extract_package_metrics`, `generate_sourcing_report`)
- **Steps:**
  1. Add `resolve_tier_price_cny(item: dict[str, Any], target_qty: int) -> float | None`:
     - Inspect `item.get("priceTiers")`: if it is a non-empty list of dicts with valid `minQty` and `price`, check if the tiers have distinct `minQty` thresholds (note: in 1688 search/offer JSON, sometimes multiple SKU prices appear with `minQty: 1`; if multiple tiers exist with escalating `minQty` values such as `minQty: 2`, `minQty: 50`, `minQty: 100`, select the tier with the highest `minQty <= target_qty`; if all tiers share `minQty == 1` and `item.get("price") or item.get("priceMin")` is present, prefer `item.get("price") or item.get("priceMin")` so multi-SKU base price is preserved).
     - Fall back to `item.get("price") or item.get("priceMin")` or `priceTiers[0].get("price")`.
  2. Add `extract_package_metrics(item: dict[str, Any]) -> dict[str, Any]` returning `{"weight_kg": float | None, "volume_cbm": float | None, "weight_unit_inferred": str | None}`:
     - **Priority 1:** Direct explicit fields `item.get("weight_kg")` or `item.get("unitWeight")` or `item.get("freight", {}).get("unitWeight")` (already in kg on 1688).
     - **Priority 2:** `item.get("packageInfo")[0]`:
       - Extract `volume` ($\text{cm}^3$) or `length * width * height` ($\text{cm}^3$) and convert to $\text{m}^3$: `volume_cbm = round(vol_cm3 / 1_000_000.0, 6)`. Also accept direct `item.get("volume_cbm")`.
       - For `pkg.get("weight")`: check if string contains `"kg"`/`"千克"`/`"公斤"` (treat as kg) or `"g"`/`"克"` (divide by `1000.0`). For bare numbers in `packageInfo[0]["weight"]`, 1688 `packageInfo.weight` is denominated in **grams** (e.g., `161` = `0.161 kg`, `5` = `0.005 kg`); cross-check against volumetric weight $\text{vol\_weight\_kg} = (L \times W \times H) / 6000.0$: if `w_float > 10` OR (`vol_weight_kg` is available and `w_float > 20 * vol_weight_kg`) OR `pkg` came from 1688 `packageInfo` (which uses grams by schema definition when `w_float >= 1.0`), divide by `1000.0` (`weight_unit_inferred = "g->kg"`).
  3. In `generate_sourcing_report()`, call `resolve_tier_price_cny(item, target_qty)` and `extract_package_metrics(item)`, and pass `volume_cbm_per_unit=est_volume` (`volume_cbm if volume_cbm is not None else 0.002`) into `calculate_landed_cost()`.
- **Success criteria:** `generate_sourcing_report()` uses real `volume_cbm`, selects quantity price tiers when escalating `minQty` tiers exist, and converts `5` grams in `packageInfo` to `0.005 kg`.
- **Verify:** `python3 -c 'import sys; sys.path.insert(0, "scripts"); import china_sourcing as cs; m = cs.extract_package_metrics({"packageInfo": [{"length": 10, "width": 5, "height": 5, "weight": 5, "volume": 250}]}); assert m["weight_kg"] == 0.005 and abs(m["volume_cbm"] - 0.00025) < 1e-8; print("METRICS_OK")'` exits 0 and prints `METRICS_OK`.

### Task 2.2 — Add Short-Link Redirect Resolution (`parse-link --resolve`) and `alibaba` Subcommand
- **Goal:** Use `urllib.request` to resolve short links (`e.tb.cn`, `m.tb.cn`, `v.douyin.com`, `qr.1688.com`, `s.click.taobao.com`) safely with timeout/fallback, and add the `alibaba` CLI subcommand documented in `references/platform-playbooks.md`.
- **Target files and symbols:**
  - `/Volumes/1/AGY/china-sourcing/scripts/china_sourcing.py` (`SHORT_LINK_DOMAINS`, `resolve_short_url`, `parse_share_link`, `run_alibaba_search`, `build_parser`, `main`)
- **Steps:**
  1. Add `resolve_short_url(url: str, timeout: float = 5.0) -> tuple[str, str | None]` using `urllib.request.Request` with a mobile `User-Agent`, following redirects (up to 5 hops) and also scanning response HTML for canonical `id=` / `/offer/\d+\.html` / `/video/\d+` URLs (since `e.tb.cn` often embeds `var url = 'https://item.taobao.com/item.htm?id=...'` in HTML). Gracefully return `(url, None)` on any `URLError` or timeout.
  2. Update `parse_share_link(text: str, resolve_redirects: bool = False) -> dict[str, Any]` so when `resolve_redirects=True` (or `--resolve` on CLI) and `item_id is None` on a short-link domain, it calls `resolve_short_url(url)` and extracts `item_id` and `resolved_url`.
  3. Add `run_alibaba_search(query: str, max_results: int = 10, output_path: str | None = None) -> dict[str, Any]` and register the `alibaba` subparser in `build_parser()` so `python3 scripts/china_sourcing.py alibaba --query "<en_kw>" [--output <path>]` generates structured Alibaba search metadata/items and never fails as an unknown subcommand.
- **Success criteria:** `parse_share_link(..., resolve_redirects=True)` resolves short links and `china_sourcing.py alibaba --help` exits 0.
- **Verify:** `python3 scripts/china_sourcing.py alibaba --query "desk lamp" | python3 -c 'import sys, json; d=json.load(sys.stdin); assert d["platform"]=="alibaba" and "search_url" in d; print("ALIBABA_CLI_OK")'` exits 0 and prints `ALIBABA_CLI_OK`.

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
