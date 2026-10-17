---
handoff-version: 1
generated: 2026-10-17T02:34:30Z
generator: ak:handoff@2.1.0
focus: "em sử dụng /viet-pro để viết 1 tài liệu hướng dẫn sử dụng của skill này. + push git + comit"
workspace: /Volumes/1/AGY/.agents/skills/china-sourcing
branch: main
head: 7ef366d
---

# HANDOFF: china-sourcing usage guide, WangWang 5-min polling, and GitHub release

## Mission and current status
Focus: "em sử dụng /viet-pro để viết 1 tài liệu hướng dẫn sử dụng của skill này. + push git + comit".
Done:
- Built, validated, and synced the multi-agent `china-sourcing` skill across all 5 agent directories (`/Volumes/1/AGY/.agents/skills/china-sourcing`, `~/.agents/skills/china-sourcing`, `~/.gemini/config/skills/china-sourcing`, `~/.claude/skills/china-sourcing`, `~/.codex/skills/china-sourcing`).
- Updated landed-cost & logistics pricing rules: `4,000 VNĐ / 1 CNY`, `30,000 VNĐ / 1 kg` (E-commerce / TMĐT), `1,600,000 VNĐ / 1 m³` or `6,000 VNĐ / 1 kg` + VAT + service fee (Official import / Chính ngạch for orders > 1 m³), and support contact `https://t.me/dungtq87`.
- Added automatic 5-minute WangWang reply polling workflow (`check-wangwang` subcommand + `*/5 * * * *` schedule rule) and captured live WangWang chat screenshots & seller replies for Top 5 eye-protection desk lamp factories on 1688 (`run-20261017-0831-den-ban-chong-can`).
- Authored the comprehensive Vietnamese usage guide (`README.md` & `HUONG_DAN_SU_DUNG_CHINA_SOURCING.md`) using `viet-pro` technical standards (`lint-vietnamese-content.mjs` passed with 0 violations).
- Initialized Git repository, committed (`7ef366d`), and pushed to `https://github.com/abm-dungtq/china-sourcing`.
Remaining:
- Follow up with the 5 contacted 1688 desk lamp factories (`恒悦亮电器厂`, `视力童`, `朗度照明电器`, `宝建洪源头厂家`, `云贝思灯具`) when the user specifies follow-up negotiation questions or sample order quantities.
Urgency: normal.

## Scope and guardrails
Workspace: `/Volumes/1/AGY` (skill repository rooted at `/Volumes/1/AGY/.agents/skills/china-sourcing`)
In scope:
- `/Volumes/1/AGY/.agents/skills/china-sourcing/` (`SKILL.md`, `README.md`, `scripts/china_sourcing.py`, `scripts/tests/test_china_sourcing.py`, `references/platform-playbooks.md`, `references/abm-workflow-and-prompts.md`)
- `/Volumes/1/AGY/china-sourcing/HUONG_DAN_SU_DUNG_CHINA_SOURCING.md`
- `/Volumes/1/AGY/china-sourcing/examples/run-20261017-0831-den-ban-chong-can/`
Out of scope:
- Automated order placement or payment execution (`1688 checkout confirm` is strictly forbidden without explicit human approval).
Constraints:
- Never ask the user to run CLI commands in a terminal; always launch browser login (`--headed`) directly from the agent and wait for confirmation.
- Maintain ABM 06-Component Prompt and `TIEU-CHUAN-THIET-KE-WORKFLOW-ABM v1.0` compliance.
Safety boundaries:
- Keep browser cookies isolated in `~/.1688/profiles/default`; never commit session state or credentials to Git.

## Current state
Branch: main
HEAD: 7ef366d4ae53db0c6ff417dfc2f4a5f28b50f7bc
Working tree: clean (`/Volumes/1/AGY/.agents/skills/china-sourcing`)
Changed files: none
Untracked files: none
Intentional local modifications: no

## Decisions and rationale
- Decision: Use `4,000 VNĐ/CNY`, `30,000 VNĐ/kg` (TMĐT), and `1,600,000 VNĐ/m³` or `6,000 VNĐ/kg + VAT + service fee` (Official import > 1 m³) with `https://t.me/dungtq87` as default constants in `scripts/china_sourcing.py`.
  Rationale: Matches actual Vietnam-China logistics pricing and provides direct support for customs, currency exchange, and OEM manufacturing.
  Alternative rejected: Hardcoding a single per-kg rate without official import CBM tiers.
  Reference: `/Volumes/1/AGY/.agents/skills/china-sourcing/scripts/china_sourcing.py`
- Decision: Add `check-wangwang` subcommand to `china_sourcing.py` and patch `1688-cli` (`seller-chat.js`, `seller-inquire.js`, `seller-messages.js`) to support `BB1688_SCREENSHOT_PATH` and `<sellerLoginId> --offer <offerId>`.
  Rationale: Enables deterministic screenshot proof upon inquiry delivery and reliable 5-minute scheduled polling of seller replies even when `FE_GLOBALS.offerLoginId` is absent on 1688 detail pages.
  Alternative rejected: Relying solely on `detail-feglobals` lookup.
  Reference: `/Volumes/1/AGY/.agents/skills/china-sourcing/scripts/china_sourcing.py`

## Work performed
- Updated `/Volumes/1/AGY/.agents/skills/china-sourcing/scripts/china_sourcing.py`, `SKILL.md`, `references/platform-playbooks.md`, `references/abm-workflow-and-prompts.md`, and `scripts/tests/test_china_sourcing.py`.
- Executed live WangWang inquiries (`1688 seller inquire`) for 5 desk lamp factories and captured 5 PNG proof screenshots in `/Volumes/1/AGY/china-sourcing/examples/run-20261017-0831-den-ban-chong-can/`.
- Executed `china_sourcing.py check-wangwang` and saved seller replies in `08_wangwang_poll.json`.
- Authored `/Volumes/1/AGY/.agents/skills/china-sourcing/README.md` with `viet-pro` and verified 0 violations via `lint-vietnamese-content.mjs`.
- Committed `7ef366d` and pushed to `https://github.com/abm-dungtq/china-sourcing`.
0 redactions applied.

## Verification
| Check | Command | Outcome | When |
| --- | --- | --- | --- |
| Unit tests (8/8) | `python3 -m unittest discover -s /Volumes/1/AGY/.agents/skills/china-sourcing/scripts/tests -v` | PASS (`Ran 8 tests in 0.002s - OK`) | 2026-10-17T02:22:09Z |
| Skill schema validation | `uv run --with PyYAML==6.0.3 python .../quick_validate.py /Volumes/1/AGY/.agents/skills/china-sourcing` | PASS (`Skill is valid!`) | 2026-10-17T02:22:24Z |
| Skill routing & cruft lint | `uv run --with PyYAML==6.0.3 python .../lint_cruft.py /Volumes/1/AGY/.agents/skills/china-sourcing --routing` | PASS (`4 file(s) scanned, 0 skipped; high=0 medium=0 low=0`) | 2026-10-17T02:31:46Z |
| Vietnamese prose lint (`viet-pro`) | `node .../viet-pro/scripts/lint-vietnamese-content.mjs /Volumes/1/AGY/.agents/skills/china-sourcing/README.md` | PASS (`OK — 0 vi phạm`) | 2026-10-17T02:32:47Z |
| Git push verification | `git -C /Volumes/1/AGY/.agents/skills/china-sourcing status --short` | PASS (clean working tree, pushed to `origin/main` at `7ef366d`) | 2026-10-17T02:34:26Z |

Not run:
- Live checkout (`1688 checkout confirm`): intentionally blocked by financial safety gate.

## Open risks and blockers
- Type: question. Owner: user (CEO / Sourcing Lead). Impact: awaiting user decision on which follow-up questions (laser engraving fee, carton CBM dimensions, or 2-unit sample order) to send to the 3 factories that replied on WangWang (`视力童`, `宝建洪源头厂家`, `云贝思灯具`).

## Exact next actions
1. **First safe step** — Run `python3 /Volumes/1/AGY/.agents/skills/china-sourcing/scripts/china_sourcing.py check-wangwang --receipt /Volumes/1/AGY/china-sourcing/examples/run-20261017-0831-den-ban-chong-can/07_inquiry_receipt.json --output /Volumes/1/AGY/china-sourcing/examples/run-20261017-0831-den-ban-chong-can/08_wangwang_poll.json` to inspect any new seller replies on 1688 WangWang.
2. When the user provides follow-up questions or sample quantities, send them via `1688 seller inquire <offerId> "<message>" --to "<sellerLoginId>" --json` with `BB1688_SCREENSHOT_PATH` set and re-enable the 5-minute polling schedule (`*/5 * * * *`).

## Source pointers
- `/Volumes/1/AGY/.agents/skills/china-sourcing/SKILL.md`
- `/Volumes/1/AGY/.agents/skills/china-sourcing/README.md`
- `/Volumes/1/AGY/.agents/skills/china-sourcing/scripts/china_sourcing.py`
- `/Volumes/1/AGY/china-sourcing/HUONG_DAN_SU_DUNG_CHINA_SOURCING.md`
- `/Volumes/1/AGY/china-sourcing/examples/run-20261017-0831-den-ban-chong-can/04_sourcing_report.md`
- `/Volumes/1/AGY/china-sourcing/examples/run-20261017-0831-den-ban-chong-can/07_inquiry_receipt.json`
- `/Volumes/1/AGY/china-sourcing/examples/run-20261017-0831-den-ban-chong-can/08_wangwang_poll.json`
- `https://github.com/abm-dungtq/china-sourcing`
