# Platform Playbooks & Multi-Agent Configuration (1688, Taobao, Alibaba, Pinduoduo, Douyin)

This reference defines the exact commands, MCP configurations, and anti-bot recovery rules for each Chinese e-commerce platform across different AI agent runtimes (Antigravity, Claude Code, Codex, OpenCode, Cursor).

---

## 1. 1688.com (Domestic B2B Wholesale & Factory Sourcing)

### Primary Engine: `1688-cli` (`superjack2050/1688-cli`)
Runs a persistent real Chrome profile (`~/.1688/profiles/default`) with a background daemon. Automatically outputs JSON when piped (`stdout` is not a TTY).

#### Automatic Browser Authentication (Executed by Agent — Never Ask User to Run CLI)
```bash
python3 scripts/china_sourcing.py login --platform 1688 --force
```
- **Agent Rule:** The agent must execute `china_sourcing.py login` (or let `china_sourcing.py 1688` auto-trigger it) so a real Chrome browser window opens directly on the user's screen. Never ask the user to open a terminal or run CLI commands.
- **User Login Options Inside the Opened Chrome Window:**
  1. **SMS / Password (No QR needed):** Enter Taobao/1688 username & password or `+84` phone number + SMS code directly in the Chrome window.
  2. **QR Scan:** Scan the sharp QR code in the Chrome window using the **Taobao App (淘宝)**, **1688 App (阿里巴巴)**, or **Alipay (支付宝)**.

#### Core Sourcing Commands
```bash
# Keyword product search (sorted by sales, price cap in CNY, ad-free)
1688 search "<chinese_keyword>" --sort best-selling --price-max 50 --exclude-ads --max 20

# Multi-keyword dataset research with top-N enrichment
1688 research <kw1> <kw2> --max-per-query 30 --enrich top:5 --jsonl

# Reverse image search (local image path or public HTTP/HTTPS URL)
1688 image-search ./sample.jpg
1688 image-search "https://example.com/product.jpg"

# Direct factory discovery (filters out trading companies)
1688 supplier search "<chinese_keyword>" --factory-only --json
1688 supplier inspect <offerId>

# Single or batch offer detail extraction (price ladders, MOQ, SKU weight/volume)
1688 offer <offerId1> <offerId2> --pro --json --pretty

# Side-by-side offer comparison
1688 compare <offerId1> <offerId2>

# Pre-sale WangWang inquiry + screenshot proof (never places an order)
BB1688_SCREENSHOT_PATH="runs/<run_id>/07_wangwang_proof_<offerId>.png" \
  1688 seller inquire <offerId> "你好，请问这款支持定制Logo吗？拿样怎么算？" --to "<sellerLoginId>" --json

# Check seller replies in WangWang (triggered automatically every 5 minutes via schedule */5 * * * *)
1688 seller messages "<sellerLoginId>" --offer <offerId> --json
python3 scripts/china_sourcing.py check-wangwang --receipt runs/<run_id>/07_inquiry_receipt.json --output runs/<run_id>/08_wangwang_poll.json
```

#### Automatic 5-Minute WangWang Polling & Logistics Pricing Rules
- **5-Minute WangWang Polling Rule:** Whenever the user asks to chat on WangWang (`1688 seller inquire` / `1688 seller chat`), the agent must automatically schedule a recurring 5-minute job (`CronExpression="*/5 * * * *"`) to check incoming messages in WangWang (`china_sourcing.py check-wangwang`), report new replies to the user, and ask the user what additional information they want to ask the supplier.
- **Standard Exchange Rate & Shipping Formula:**
  - **CNY Exchange Rate:** `4,000 VNĐ / 1 CNY` *(Liên hệ [https://t.me/dungtq87](https://t.me/dungtq87) nếu cần)*
  - **E-Commerce Shipping (Hàng đi TMĐT):** `30,000 VNĐ / 1 kg`
  - **Official Import Shipping (Hàng đi Chính ngạch — đơn hàng trên 1 m³):** `1,600,000 VNĐ / 1 m³` hoặc `6,000 VNĐ / 1 kg` + **Thuế VAT** + **Phí dịch vụ**
  - **Logistics, Import & OEM Support:** Liên hệ **[https://t.me/dungtq87](https://t.me/dungtq87)** để hỗ trợ về vận chuyển, nhập khẩu, và OEM sản phẩm.

#### Optional Cloud Skill Fallback (`nexscope-ecommerce-skills`)
When running in a headless container without Chrome:
```bash
export NEXSCOPE_PROXY_BASE=https://api.nexscope.ai/
export NEXSCOPE_API_KEY="<your_api_key>"
npx skills add nexscope-ai/nexscope-ecommerce-skills --skill ecommerce-1688-product-search
npx skills add nexscope-ai/nexscope-ecommerce-skills --skill ecommerce-1688-search-by-image
```

---

## 2. Taobao & Tmall (B2C Retail Trends, Specs & Real Buyer Reviews)

### Primary Engines
1. **Product Deep-Dive (`JeremyDong22/taobao_mcp`)**: Extracts title, price, SKU attributes, detail images, customer reviews with photos, and Q&A from any Taobao/Tmall link, short link (`e.tb.cn`), or share text.
2. **Keyword Search (`liuliang520530/taoke-mcp`)**: Searches Taobao catalog via official Taobao Union API (`TAOBAO_PID` + `TAOBAO_SESSION`) without triggering `x5sec` slider captchas.
3. **Browser Fallback (`chrome-profile` / Chrome DevTools)**: Opens `https://s.taobao.com/search?q=<encoded_keyword>` in the user's logged-in Chrome profile.

### Share-Text & Link Parsing
Use `python3 scripts/china_sourcing.py parse-link "<share_text_or_url>"` to extract canonical URLs and item IDs from mobile share strings such as:
`【淘宝】假一赔四 https://e.tb.cn/h.StvCjJlWxkNatsx?tk=xxx MF937 「商品名称」`

---

## 3. Alibaba.com (International B2B Export Benchmark)

### Primary Engines
1. **Built-in CLI Scraper (`scripts/china_sourcing.py alibaba`)**: Fetches and parses Alibaba.com public search listings (price range in USD, MOQ, supplier country, years active, review score) directly into structured JSON.
2. **Local REST API (`omkarcloud/alibaba-scraper`)**:
   ```bash
   git clone https://github.com/omkarcloud/alibaba-scraper.git ~/.local/share/alibaba-scraper
   cd ~/.local/share/alibaba-scraper && python3 -m pip install -r requirements.txt
   python3 run.py   # Exposes 12 endpoints at http://localhost:8000
   curl -s "http://localhost:8000/products/search?query=magnetic+power+bank"
   ```

---

## 4. Pinduoduo (Value B2C & Viral Low-Cost Supply Chain)

### Anti-Bot Reality & Approved Pathways
Direct headless scraping of `yangkeduo.com` is blocked by Pinduoduo's `anti_content` signature and TLS fingerprinting. Always use one of these two stable pathways:

1. **Official Affiliate Search MCP (`liuliang520530/taoke-mcp`)**:
   - Configure `PDD_PID` and `PDD_SESSION_TOKEN` from `jinbao.pinduoduo.com`.
   - Call MCP tools `pdd.ddk.goods.search` (keyword search), `pdd.ddk.goods.recommend.get` (viral low-price rankings), and `pdd.ddk.goods.detail`.
2. **Temu Supply-Chain Mirror (`nexscope-ecommerce-skills`)**:
   - Pinduoduo and Temu share the same PDD Holdings factory base. Use `ecommerce-geekbi-temu-product` and `ecommerce-geekbi-temu-search-by-image` when `NEXSCOPE_API_KEY` is configured.

---

## 5. Douyin (Viral Video Product Discovery & Script Extraction)

### Primary Engines
1. **Video & Transcript Extraction (`yzfly/douyin-mcp-server`)**:
   - Installed via `uv tool install douyin-mcp-server` (command: `douyin-mcp-server`).
   - Parses Douyin share links (`https://v.douyin.com/...`), retrieves watermark-free video URLs, and transcribes spoken product pitches into Markdown via SenseVoice (`API_KEY` from SiliconFlow or `DASHSCOPE_API_KEY`).
2. **Keyword & Comment Mining (`NanmiCoder/MediaCrawler`)**:
   - Connects to the user's real Chrome instance via CDP (`chrome://inspect/#remote-debugging` on `127.0.0.1:9222`) to search Douyin videos by keyword and scrape 1st/2nd-level buyer comments (`uv run main.py --platform dy --lt qrcode --type search`).

---

## 6. Cross-Agent Installation & MCP Config Matrix

### Skill Directory Locations Across Agents
Install or symlink the `china-sourcing` folder into:
- **Workspace (Antigravity / OpenCode / Cursor):** `<repo>/.agents/skills/china-sourcing`
- **Global Antigravity:** `~/.gemini/config/skills/china-sourcing`
- **Global `.agents` Standard:** `~/.agents/skills/china-sourcing`
- **Global Claude Code:** `~/.claude/skills/china-sourcing`
- **Global Codex:** `~/.codex/skills/china-sourcing`

### Unified MCP Server Configuration (`.mcp.json` / `claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "douyin-mcp": {
      "command": "douyin-mcp-server",
      "args": [],
      "env": {
        "API_KEY": "${SILICONFLOW_API_KEY}"
      }
    },
    "taoke-mcp": {
      "command": "npx",
      "args": ["-y", "@liuliang520500/sinataoke_cn@latest"],
      "env": {
        "ENV_URL": "https://config.sinataoke.cn/api/mcp/secret",
        "ENV_SECRET": "url:mcp.sinataoke.cn",
        "ENV_OVERRIDE": "false",
        "TAOBAO_PID": "${TAOBAO_PID}",
        "TAOBAO_SESSION": "${TAOBAO_SESSION}",
        "PDD_PID": "${PDD_PID}",
        "PDD_SESSION_TOKEN": "${PDD_SESSION_TOKEN}"
      }
    }
  }
}
```
