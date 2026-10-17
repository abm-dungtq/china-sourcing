#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/abm-dungtq/china-sourcing.git"
TMP_DIR="$(mktemp -d)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

echo "⚡ Đang tải bộ kỹ năng China Sourcing (1688 • Taobao • Alibaba • Pinduoduo • Douyin)..."
if [ -f "SKILL.md" ] && [ -f "scripts/china_sourcing.py" ]; then
  SRC_DIR="$(pwd)"
else
  git clone --depth 1 "$REPO_URL" "$TMP_DIR/china-sourcing" >/dev/null 2>&1
  SRC_DIR="$TMP_DIR/china-sourcing"
fi

TARGETS=(
  "$HOME/.agents/skills/china-sourcing"
  "$HOME/.gemini/config/skills/china-sourcing"
  "$HOME/.claude/skills/china-sourcing"
  "$HOME/.codex/skills/china-sourcing"
)

for dest in "${TARGETS[@]}"; do
  mkdir -p "$dest"
  rsync -a --delete \
    --exclude '.git' \
    --exclude 'examples' \
    --exclude 'docs' \
    --exclude 'assets' \
    --exclude 'plans' \
    --exclude 'runs' \
    --exclude 'scripts/tests' \
    "$SRC_DIR/" "$dest/"
  rm -rf "$dest/examples" "$dest/docs" "$dest/assets" "$dest/plans" "$dest/runs" "$dest/scripts/tests"
  echo "  ✓ Đã cài đặt vào: $dest"
done

if command -v npm >/dev/null 2>&1 && ! command -v 1688 >/dev/null 2>&1; then
  echo "📦 Đang cài đặt 1688-cli@0.1.47..."
  npm install -g 1688-cli@0.1.47 || true
fi

if command -v python3 >/dev/null 2>&1; then
  echo "🔧 Đang kiểm tra & áp dụng bản vá 1688-cli (WangWang screenshot & offer filter)..."
  python3 "$SRC_DIR/scripts/china_sourcing.py" doctor --fix >/dev/null || true
fi

if command -v uv >/dev/null 2>&1 && ! command -v douyin-mcp-server >/dev/null 2>&1; then
  echo "📦 Đang cài đặt douyin-mcp-server..."
  uv tool install douyin-mcp-server || true
fi

echo ""
echo "🎉 Cài đặt hoàn tất China Sourcing Skill!"
echo "👉 Gõ lệnh bằng ngôn ngữ tự nhiên trong Agent (Claude Code / Antigravity / Codex / Cursor):"
echo "   \"Tìm giúp tôi 5 xưởng sản xuất đèn bàn học chống cận trên 1688 dưới 35 tệ, tính giá vốn về kho Việt Nam cho lô 100 chiếc.\""
echo "📞 Hỗ trợ vận chuyển TQ-VN, nhập khẩu & OEM sản phẩm: https://t.me/dungtq87"
