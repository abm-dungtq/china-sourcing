# Phase 1 — Vendor Patch `search-mtop.js` & Multi-Directory `doctor --fix`

## Goal
Extend `1688-cli`'s `dist/session/search-mtop.js` via `patches/1688-cli/` so every `1688 search` / `1688 research` call preserves `trendSignals` (`newProductSellPoints`, `rankBadges`, `businessOppoTopics`, `priceCompetitiveBadges`, `soldCountTotal`, `soldCountText`, `kuaJingPuHuo`, `fenxiaoNewOffer`, `tradeScore`) and fixes `demand.repurchaseRate` extraction from `turnHead.percent` / `afterTags.text` / `offerRepurchaseRate`. Update `verify_and_patch_1688_cli()` in `scripts/china_sourcing.py` to support relative target paths across `dist/` (`dist/commands/*` and `dist/session/*`) and reload the 1688 daemon when patches are applied.

## Files to Create or Modify
- `patches/1688-cli/search-mtop.js` (create)
- `patches/1688-cli/patch-meta.json` (modify)
- `scripts/china_sourcing.py` (modify `verify_and_patch_1688_cli`)

## Tasks & Steps

### Task 1.1 — Create `patches/1688-cli/search-mtop.js` with defensive `guide` & `repurchaseRate` extraction
- **Goal:** Extract all trend, leaderboard, new-arrival, and repeat-rate fields from `mtop.relationrecommend.wirelessrecommend.recommend` (`appId=32517`) in `mapOffer(item)`.
- **Target files and symbols:** `patches/1688-cli/search-mtop.js` (`mapOffer`, `extractTrendSignals`).
- **Steps:**
  1. Copy `/opt/homebrew/lib/node_modules/1688-cli/dist/session/search-mtop.js` into `patches/1688-cli/search-mtop.js` and add helper `extractTrendSignals(d)`:
     - Fix `repurchaseRateText`: check `d.repurchaseRateText ?? d.repurchaseRate ?? d.turnHead?.percent ?? (d.afterTags?.matKey === 'return_rate' ? d.afterTags?.text : null) ?? d.offerRepurchaseRate ?? null`.
     - Extract `soldCountText`: `d.afterPrice?.text ?? d.afterPriceList?.[0]?.text ?? null` and `soldCountTotal`: `parseCountText(soldCountText)`.
     - Scan `guides = [...(d.list?.guide ?? []), ...(d.list?.guide2 ?? []), ...(d.grid?.guide ?? [])]` (deduplicated by `matKey + text`):
       - `newProductSellPoints`: texts where `g.matKey === 'newProductSellPoint'` or `/上新|新品/.test(g.text)`.
       - `rankBadges`: objects `{ text, url, rankName, categoryId, rankFullNameId }` where `g.matKey === 'billboard'` and `(g.url ?? '').includes('newRank')` or `/榜第\d+名/.test(g.text)`.
       - `businessOppoTopics`: objects `{ text, topic, topicId, topicDate, url }` where `g.matKey === 'billboard'` and (`(g.url ?? '').includes('business-oppo')` or `(g.text ?? '').startsWith('商机组货')`), parsing 8-digit `YYYYMMDD` prefix from `topicId` query param if present.
       - `priceCompetitiveBadges`: texts where `g.matKey === 'price_competitive'` or `/近\d+天低价|比同款低/.test(g.text)`.
     - Extract `kuaJingPuHuo: bool(d.kuaJingPuHuo)`, `fenxiaoNewOffer: bool(d.shopAddition?.fenxiaoNewOffer)`, and `tradeScore: d.shopAddition?.tradeService?.compositeNewScore ? parseFloat(d.shopAddition.tradeService.compositeNewScore) : null`.
     - Attach `trendSignals` object to the returned offer object in `mapOffer(item)`.
- **Success criteria:** `patches/1688-cli/search-mtop.js` exists, is valid ES module JavaScript, and contains marker `trendSignals`.
- **Verify:** `node --check /Volumes/1/AGY/china-sourcing/patches/1688-cli/search-mtop.js` exits 0.

### Task 1.2 — Register `search-mtop.js` in `patches/1688-cli/patch-meta.json` and update `verify_and_patch_1688_cli`
- **Goal:** Allow `verify_and_patch_1688_cli()` to resolve `fmeta["target_relpath"]` (such as `dist/session/search-mtop.js`), apply all 4 patches, and reload the 1688 daemon when files are updated.
- **Target files and symbols:** `patches/1688-cli/patch-meta.json`, `scripts/china_sourcing.py` (`verify_and_patch_1688_cli`).
- **Steps:**
  1. Compute the SHA-256 of `patches/1688-cli/search-mtop.js` and add `"search-mtop.js"` to `patches/1688-cli/patch-meta.json` with `"target_relpath": "dist/session/search-mtop.js"`, `"marker": "trendSignals"`, and `"sha256": "<computed_sha256>"`.
  2. In `scripts/china_sourcing.py` (`verify_and_patch_1688_cli`), resolve each file's target path using `target_relpath` relative to `target_dist` (stripping leading `"dist/"` if present, defaulting to `f"commands/{fname}"`).
  3. When `applied_files` is non-empty and `dist_dir is None` (live global `1688-cli`), run `1688 daemon reload` best-effort (`timeout=15`) so the running daemon picks up the newly patched `search-mtop.js`.
- **Success criteria:** `python3 scripts/china_sourcing.py doctor --fix` patches `dist/session/search-mtop.js` and reports `"patched": true` with all 4 files `"ok": true`.
- **Verify:** `python3 /Volumes/1/AGY/china-sourcing/scripts/china_sourcing.py doctor --fix` exits 0 and output contains `"search-mtop.js"` and `"patched": true`.

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
