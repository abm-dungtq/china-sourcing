#!/usr/bin/env python3
"""
Unified Multi-Agent CLI for Chinese E-Commerce Product Search & Sourcing
Platforms: 1688.com, Taobao/Tmall, Alibaba.com, Pinduoduo, Douyin.
Standard library only (Python 3.9+) for universal portability across agent runtimes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_EXCHANGE_RATE_VND = 4000.0
DEFAULT_VN_SHIPPING_PER_KG_VND = 30000.0
DEFAULT_OFFICIAL_VN_SHIPPING_PER_CBM_VND = 1600000.0
DEFAULT_OFFICIAL_VN_SHIPPING_PER_KG_VND = 6000.0
DEFAULT_CN_DOMESTIC_SHIPPING_CNY = 6.0
SUPPORT_CONTACT_URL = "https://t.me/dungtq87"
SUPPORT_CONTACT_NOTE = (
    "Liên hệ https://t.me/dungtq87 để hỗ trợ về vận chuyển, nhập khẩu, đổi tệ CNY (4.000đ/CNY) và OEM sản phẩm."
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def check_binary(name: str) -> dict[str, Any]:
    resolved = shutil.which(name)
    return {"installed": bool(resolved), "path": resolved}


def read_1688_state_identity() -> dict[str, Any] | None:
    state_file = Path.home() / ".1688" / "state.json"
    if not state_file.exists():
        return None
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
        if isinstance(data, dict) and (data.get("memberId") or data.get("nick")):
            return {
                "memberId": data.get("memberId"),
                "nick": data.get("nick"),
                "loggedInAt": data.get("loggedInAt"),
                "lastVerifiedAt": data.get("lastVerifiedAt"),
            }
    except Exception:
        return None
    return None


def resolve_1688_dist_dir() -> Path | None:
    binary = shutil.which("1688")
    if binary:
        try:
            resolved_cli = Path(binary).resolve()
            if resolved_cli.name == "cli.js" and resolved_cli.parent.name == "dist":
                return resolved_cli.parent
        except Exception:
            pass
    npm_bin = shutil.which("npm")
    if npm_bin:
        try:
            proc = subprocess.run(
                [npm_bin, "root", "-g"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                candidate = Path(proc.stdout.strip()) / "1688-cli" / "dist"
                if candidate.is_dir():
                    return candidate
        except Exception:
            pass
    return None


def verify_and_patch_1688_cli(
    apply_patch: bool = False,
    dist_dir: Path | None = None,
    patches_dir: Path | None = None,
) -> dict[str, Any]:
    """Verify (and optionally apply) the vendored 1688-cli WangWang screenshot & --offer patches."""
    repo_patches_dir = patches_dir or (Path(__file__).resolve().parent.parent / "patches" / "1688-cli")
    meta_path = repo_patches_dir / "patch-meta.json"
    if not meta_path.exists():
        return {"patched": False, "error": f"patch-meta.json not found at {meta_path}"}

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    target_dist = dist_dir or resolve_1688_dist_dir()
    if not target_dist or not target_dist.is_dir():
        return {"patched": False, "error": "1688-cli dist directory not found"}

    files_meta: dict[str, Any] = meta.get("files", {})
    file_statuses: dict[str, Any] = {}
    applied_files: list[str] = []

    for fname, fmeta in files_meta.items():
        raw_rel = str(fmeta.get("target_relpath") or f"dist/commands/{fname}")
        rel_subpath = raw_rel[5:] if raw_rel.startswith("dist/") else raw_rel
        # Backward compatibility for unit tests that create flat commands_dir without session/
        target_file = target_dist / rel_subpath
        if not target_file.parent.exists() and (target_dist / "commands").exists() and dist_dir is not None:
            target_file.parent.mkdir(parents=True, exist_ok=True)
        vendor_file = repo_patches_dir / fname
        marker = str(fmeta.get("marker") or "")
        expected_sha = str(fmeta.get("sha256") or "")

        is_valid = False
        if target_file.exists():
            raw_bytes = target_file.read_bytes()
            actual_sha = hashlib.sha256(raw_bytes).hexdigest()
            has_marker = marker.encode("utf-8") in raw_bytes if marker else True
            is_valid = (actual_sha == expected_sha) or has_marker

        if not is_valid and apply_patch and vendor_file.exists():
            target_file.parent.mkdir(parents=True, exist_ok=True)
            tmp_target = target_file.parent / f".{fname}.tmp"
            tmp_target.write_bytes(vendor_file.read_bytes())
            os.replace(tmp_target, target_file)
            applied_files.append(fname)
            raw_bytes = target_file.read_bytes()
            actual_sha = hashlib.sha256(raw_bytes).hexdigest()
            has_marker = marker.encode("utf-8") in raw_bytes if marker else True
            is_valid = (actual_sha == expected_sha) or has_marker

        file_statuses[fname] = {"ok": is_valid, "path": str(target_file)}

    if applied_files and dist_dir is None:
        binary = shutil.which("1688")
        if binary:
            try:
                subprocess.run(
                    [binary, "daemon", "reload"],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    check=False,
                )
            except Exception:
                pass

    all_patched = bool(files_meta) and all(v.get("ok") for v in file_statuses.values())
    return {
        "patched": all_patched,
        "tested_version": meta.get("tested_version"),
        "dist_dir": str(target_dist),
        "applied_files": applied_files,
        "files": file_statuses,
    }


def inspect_1688_status(apply_patch: bool = False) -> dict[str, Any]:
    binary = shutil.which("1688")
    if not binary:
        return {
            "installed": False,
            "logged_in": False,
            "patched": False,
            "patched_1688_cli": False,
            "detail": "1688-cli not installed",
        }
    state_file = Path.home() / ".1688" / "state.json"
    identity = read_1688_state_identity()
    patch_info = verify_and_patch_1688_cli(apply_patch=apply_patch)
    is_patched = bool(patch_info.get("patched"))
    try:
        proc = subprocess.run(
            [binary, "doctor"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        logged_in = "not logged in" not in out.lower() and proc.returncode == 0
        return {
            "installed": True,
            "path": binary,
            "logged_in": logged_in,
            "patched": is_patched,
            "patched_1688_cli": is_patched,
            "patch_detail": patch_info,
            "identity": identity,
            "state_file": str(state_file) if state_file.exists() else None,
            "summary": (
                f"Ready (logged in as {identity.get('nick') or identity.get('memberId')})"
                if logged_in and identity
                else ("Ready" if logged_in else "Not logged in (auto-browser login will trigger)")
            ),
        }
    except Exception as exc:
        return {
            "installed": True,
            "path": binary,
            "logged_in": False,
            "patched": is_patched,
            "patched_1688_cli": is_patched,
            "patch_detail": patch_info,
            "identity": identity,
            "detail": str(exc),
        }


def build_onboarding_guide(identity: dict[str, Any] | None = None) -> dict[str, Any]:
    nick = (identity or {}).get("nick") or "Đã xác thực"
    member_id = (identity or {}).get("memberId") or "N/A"
    guide_md = "\n".join(
        [
            f"### Xác Nhận Đăng Nhập Thành Công: `{nick}` (Member ID: `{member_id}`)",
            "",
            "Phiên làm việc đã được lưu cố định vào `~/.1688/profiles/default` và kích hoạt Background Daemon. Từ bây giờ bạn có thể giao việc trực tiếp bằng ngôn ngữ tự nhiên theo 5 kịch bản hiệu quả nhất:",
            "",
            "1. **Tìm Xưởng Sản Xuất Tận Gốc Theo Ngách & Giá Mục Tiêu (1688 Factory Sourcing):**",
            '   - *Ví dụ câu lệnh:* `"Tìm giúp tôi 5 xưởng sản xuất (factory-only) đèn bàn học chống cận trên 1688, giá tại xưởng dưới 35 tệ, tính giá vốn về Việt Nam cho lô 100 chiếc."`',
            "2. **Tìm Nguồn Hàng Bằng Hình Ảnh (Reverse Image Search):**",
            '   - *Ví dụ câu lệnh:* `"Tìm các xưởng 1688 bán sản phẩm giống hệt bức ảnh /đường/dẫn/anh-mau.jpg và so sánh 3 xưởng có tỷ lệ mua lại cao nhất."`',
            "3. **Giải Mã Link Chia Sẻ Điện Thoại & Đối Chiếu Giá Sỉ (Taobao / Pinduoduo / Douyin -> 1688):**",
            '   - *Ví dụ câu lệnh:* `"Phân tích link chia sẻ Taobao/Douyin này, bóc tách thông số và tìm xem trên 1688 xưởng gốc đang chào giá sỉ bao nhiêu."`',
            "4. **Chat WangWang Hỏi Giá & Tự Động Canh Phản Hồi 5 Phút/Lần:**",
            '   - *Ví dụ câu lệnh:* `"Gửi tin hỏi giá sỉ các xưởng trên qua WangWang kèm chụp ảnh bằng chứng."` *(Hệ thống sẽ tự động đặt lịch 5 phút/lần kiểm tra tin nhắn phản hồi trên WangWang, báo cáo lại và hỏi bạn cần hỏi thêm thông tin gì với nhà cung cấp).*',
            "5. **Săn Hàng Hot Trend & Bóc Kịch Bản Video Bán Hàng Douyin:**",
            '   - *Ví dụ câu lệnh:* `"Tải video không logo và trích xuất toàn bộ kịch bản lời thoại bán hàng từ link Douyin này để phân tích USP sản phẩm."`',
            "6. **Quét Sản Phẩm Mới Đang Hot, Lượt Bán Tăng Nhanh & Bắt Trend Ngách 1688 (`trends`):**",
            '   - *Ví dụ câu lệnh:* `"Quét giúp tôi các mẫu đèn bàn chống cận mới ra đang hot, lượt bán tăng nhanh nhất trên 1688 và các ngách xu hướng đang lên kèm giá vốn về Việt Nam cho lô 100 chiếc."`',
            "",
            "---",
            "### Biểu Phí Tham Chiếu Mặc Định & Hỗ Trợ Nhập Khẩu / OEM",
            "- **Tỷ giá CNY:** `4.000đ / 1 CNY` *(Liên hệ [https://t.me/dungtq87](https://t.me/dungtq87) nếu cần)*",
            "- **Giá vận chuyển hàng đi TMĐT:** `30.000đ / 1 kg`",
            "- **Giá vận chuyển hàng đi Chính ngạch (đơn hàng trên 1 m³):** `1.600.000đ / 1 m³` hoặc `6.000đ / 1 kg` + **Thuế VAT** + **Phí dịch vụ**",
            "- **Hỗ trợ Vận chuyển, Nhập khẩu & OEM sản phẩm:** Liên hệ **[https://t.me/dungtq87](https://t.me/dungtq87)**",
        ]
    )
    return {
        "confirmed_account": {"nick": nick, "memberId": member_id},
        "support_contact": SUPPORT_CONTACT_URL,
        "scenarios": [
            "1688 Factory Keyword Sourcing (--factory-only + Landed Cost VND)",
            "1688 Reverse Image Search (local file or image URL)",
            "Cross-Platform Share Link Parsing (Taobao/Pinduoduo/Douyin -> 1688 wholesale match)",
            "WangWang Supplier Inquiry + Automatic 5-Minute Reply Polling Schedule",
            "Douyin Viral Video Download & AI Transcript Extraction",
            "1688 Hot New Products, Fast-Rising Sales Velocity & Niche Trend Radar (trends)",
        ],
        "markdown_guide": guide_md,
    }


def run_doctor(output_path: str | None = None, fix: bool = False) -> dict[str, Any]:
    report: dict[str, Any] = {
        "timestamp": utc_now_iso(),
        "tools": {
            "1688_cli": inspect_1688_status(apply_patch=fix),
            "douyin_mcp_server": check_binary("douyin-mcp-server"),
            "chrome_profile": check_binary("chrome-profile"),
            "uvx": check_binary("uvx"),
            "npx": check_binary("npx"),
        },
        "env_credentials": {
            "NEXSCOPE_API_KEY": bool(os.environ.get("NEXSCOPE_API_KEY")),
            "SILICONFLOW_API_KEY_OR_DASHSCOPE": bool(
                os.environ.get("API_KEY")
                or os.environ.get("SILICONFLOW_API_KEY")
                or os.environ.get("DASHSCOPE_API_KEY")
            ),
            "TAOBAO_UNION_CONFIGURED": bool(
                os.environ.get("TAOBAO_PID") and os.environ.get("TAOBAO_SESSION")
            ),
            "PDD_JINBAO_CONFIGURED": bool(
                os.environ.get("PDD_PID") and os.environ.get("PDD_SESSION_TOKEN")
            ),
        },
    }
    if output_path:
        write_json(Path(output_path), report)
    return report


SHORT_LINK_DOMAINS = (
    "e.tb.cn",
    "m.tb.cn",
    "s.click.taobao.com",
    "v.douyin.com",
    "iesdouyin.com",
    "qr.1688.com",
    "m.1688.com",
)


def _extract_platform_and_id(url_or_text: str, raw_text: str = "") -> tuple[str, str | None]:
    lowered = url_or_text.lower()
    combined = f"{url_or_text} {raw_text}"
    if "1688.com" in lowered:
        m = re.search(r"/offer/(\d+)\.html", combined) or re.search(r"\b(\d{11,13})\b", combined)
        return "1688", (m.group(1) if m else None)
    if any(k in lowered for k in ("taobao.com", "tmall.com", "e.tb.cn", "m.tb.cn")):
        plat = "tmall" if "tmall.com" in lowered else "taobao"
        m = (
            re.search(r"[?&]id=(\d+)", combined)
            or re.search(r"a\.m\.taobao\.com/i(\d+)\.htm", combined)
            or re.search(r"itemId=(\d+)", combined)
        )
        return plat, (m.group(1) if m else None)
    if any(k in lowered for k in ("yangkeduo.com", "pinduoduo.com")):
        m = re.search(r"goods_id=(\d+)", combined)
        return "pinduoduo", (m.group(1) if m else None)
    if "douyin.com" in lowered or "iesdouyin.com" in lowered:
        m = re.search(r"/video/(\d+)", combined) or re.search(r"modal_id=(\d+)", combined)
        return "douyin", (m.group(1) if m else None)
    if "alibaba.com" in lowered:
        m = re.search(r"_(\d{9,16})\.html", combined)
        return "alibaba", (m.group(1) if m else None)
    if re.fullmatch(r"\d{11,13}", url_or_text.strip()):
        return "1688_or_taobao_id", url_or_text.strip()
    return "unknown", None


def resolve_short_url(url: str, timeout: float = 5.0) -> tuple[str, str | None]:
    """Follow HTTP redirects (and embedded JS var url redirects on e.tb.cn) to reveal canonical item URL."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            final_url = resp.geturl() or url
            body_bytes = resp.read(32768)
            html_snippet = body_bytes.decode("utf-8", errors="ignore") if body_bytes else ""
        _, item_id = _extract_platform_and_id(final_url)
        if not item_id and html_snippet:
            js_url_match = re.search(r"var\s+url\s*=\s*['\"](https?://[^'\"]+)['\"]", html_snippet)
            if not js_url_match:
                js_url_match = re.search(
                    r"(https?://(?:item\.taobao\.com|detail\.tmall\.com|a\.m\.taobao\.com|detail\.1688\.com|m\.1688\.com|www\.douyin\.com)[^\s\"'<>]+)",
                    html_snippet,
                )
            if js_url_match:
                final_url = js_url_match.group(1)
        return final_url, (html_snippet or None)
    except Exception:
        return url, None


def parse_share_link(text: str, resolve_redirects: bool = False) -> dict[str, Any]:
    """Extract platform, clean URL, and product/offer/video ID from Chinese share strings."""
    url_match = re.search(r"https?://[^\s「」【】\"'<>]+", text)
    url = url_match.group(0).rstrip(".,;)") if url_match else None

    platform, item_id = _extract_platform_and_id(url or text, text)
    resolved_url: str | None = None

    if resolve_redirects and url and item_id is None:
        final_url, html_snippet = resolve_short_url(url)
        if final_url and final_url != url:
            resolved_url = final_url
            r_plat, r_id = _extract_platform_and_id(final_url, html_snippet or "")
            if r_plat != "unknown":
                platform = r_plat
            if r_id:
                item_id = r_id
        elif html_snippet:
            r_plat, r_id = _extract_platform_and_id(url, html_snippet)
            if r_id:
                item_id = r_id

    title_match = re.search(r"「([^」]+)」", text)
    extracted_title = title_match.group(1) if title_match else None

    result: dict[str, Any] = {
        "raw_input": text,
        "platform": platform,
        "url": url,
        "item_id": item_id,
        "extracted_title": extracted_title,
    }
    if resolved_url is not None or resolve_redirects:
        result["resolved_url"] = resolved_url
    return result


def build_search_matrix(
    product_name: str,
    chinese_keywords: list[str],
    english_keyword: str | None = None,
    max_price_cny: float | None = None,
) -> dict[str, Any]:
    entries = []
    en_query = english_keyword or product_name
    en_encoded = urllib.parse.quote_plus(en_query)

    for kw in chinese_keywords:
        kw_clean = kw.strip()
        if not kw_clean:
            continue
        kw_utf8 = urllib.parse.quote(kw_clean)
        cli_cmd = f'1688 search "{kw_clean}" --sort best-selling --exclude-ads'
        if max_price_cny is not None:
            cli_cmd += f" --price-max {max_price_cny:g}"
        entries.append(
            {
                "keyword_zh": kw_clean,
                "1688_cli_search": cli_cmd,
                "1688_cli_factory": f'1688 supplier search "{kw_clean}" --factory-only --json',
                "urls": {
                    "1688_search": f"https://s.1688.com/selloffer/offer_search.htm?keywords={kw_utf8}",
                    "taobao_search": f"https://s.taobao.com/search?q={kw_utf8}",
                    "douyin_search": f"https://www.douyin.com/search/{kw_utf8}?type=video",
                    "pinduoduo_jinbao": f"https://jinbao.pinduoduo.com/promotion/single-promotion?keyword={kw_utf8}",
                },
            }
        )

    return {
        "timestamp": utc_now_iso(),
        "product_name": product_name,
        "english_keyword": en_query,
        "alibaba_search_url": f"https://www.alibaba.com/trade/search?SearchText={en_encoded}",
        "keywords": entries,
    }


def run_alibaba_search(
    query: str,
    max_results: int = 10,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Generate structured Alibaba.com B2B verified manufacturer search URLs and metadata."""
    q_clean = query.strip()
    encoded = urllib.parse.quote_plus(q_clean)
    search_url = f"https://www.alibaba.com/trade/search?SearchText={encoded}"
    verified_url = f"{search_url}&IndexArea=company_en&verifiedManufactory=true"
    res: dict[str, Any] = {
        "ok": True,
        "timestamp": utc_now_iso(),
        "platform": "alibaba",
        "query": q_clean,
        "max_results": max_results,
        "search_url": search_url,
        "verified_manufacturer_url": verified_url,
        "recommended_filters": ["Verified Supplier", "Trade Assurance", "ISO 9001 / CE / RoHS"],
        "support_contact": SUPPORT_CONTACT_URL,
    }
    if output_path:
        write_json(Path(output_path), res)
    return res


def calculate_landed_cost(
    exw_price_cny: float,
    quantity: int = 1,
    weight_kg_per_unit: float = 0.2,
    exchange_rate_vnd: float = DEFAULT_EXCHANGE_RATE_VND,
    vn_shipping_per_kg_vnd: float = DEFAULT_VN_SHIPPING_PER_KG_VND,
    cn_domestic_total_cny: float = DEFAULT_CN_DOMESTIC_SHIPPING_CNY,
    volume_cbm_per_unit: float = 0.002,
    official_shipping_per_cbm_vnd: float = DEFAULT_OFFICIAL_VN_SHIPPING_PER_CBM_VND,
    official_shipping_per_kg_vnd: float = DEFAULT_OFFICIAL_VN_SHIPPING_PER_KG_VND,
) -> dict[str, Any]:
    if quantity <= 0:
        raise ValueError("quantity must be >= 1")
    if exw_price_cny < 0 or weight_kg_per_unit < 0:
        raise ValueError("exw_price_cny and weight_kg_per_unit must be non-negative")

    unit_exw_vnd = exw_price_cny * exchange_rate_vnd
    unit_cn_ship_vnd = (cn_domestic_total_cny / quantity) * exchange_rate_vnd

    # 1. Hàng đi TMĐT (30.000đ / 1 kg)
    unit_vn_freight_vnd = weight_kg_per_unit * vn_shipping_per_kg_vnd
    unit_landed_vnd = round(unit_exw_vnd + unit_cn_ship_vnd + unit_vn_freight_vnd)
    total_order_vnd = round(unit_landed_vnd * quantity)

    # 2. Hàng đi Chính ngạch (Đơn hàng > 1 m³: 1.600.000đ/m³ hoặc 6.000đ/kg + Thuế VAT + Phí dịch vụ)
    unit_official_freight_kg_vnd = round(weight_kg_per_unit * official_shipping_per_kg_vnd)
    unit_official_freight_cbm_vnd = round(volume_cbm_per_unit * official_shipping_per_cbm_vnd)
    unit_official_freight_base_vnd = max(unit_official_freight_kg_vnd, unit_official_freight_cbm_vnd)
    unit_official_base_landed_vnd = round(unit_exw_vnd + unit_cn_ship_vnd + unit_official_freight_base_vnd)

    return {
        "exw_price_cny": round(exw_price_cny, 2),
        "quantity": quantity,
        "weight_kg_per_unit": round(weight_kg_per_unit, 3),
        "exchange_rate_vnd": exchange_rate_vnd,
        "unit_exw_vnd": round(unit_exw_vnd),
        "unit_cn_domestic_shipping_vnd": round(unit_cn_ship_vnd),
        "unit_vn_freight_vnd": round(unit_vn_freight_vnd),
        "unit_landed_cost_vnd": unit_landed_vnd,
        "total_batch_landed_cost_vnd": total_order_vnd,
        "official_import_over_1cbm": {
            "rate_per_cbm_vnd": round(official_shipping_per_cbm_vnd),
            "rate_per_kg_vnd": round(official_shipping_per_kg_vnd),
            "unit_freight_by_kg_vnd": unit_official_freight_kg_vnd,
            "unit_freight_by_cbm_vnd": unit_official_freight_cbm_vnd,
            "unit_base_landed_before_vat_and_service_vnd": unit_official_base_landed_vnd,
            "formula_note": "1.600.000đ / 1 m³ hoặc 6.000đ / 1 kg + Thuế VAT + Phí dịch vụ (áp dụng đơn hàng trên 1 m³)",
        },
        "support_contact": SUPPORT_CONTACT_URL,
        "support_note": SUPPORT_CONTACT_NOTE,
    }


PLATFORM_LOGIN_URLS: dict[str, str] = {
    "1688": "https://login.1688.com/member/signin.htm?tbpm=1",
    "taobao": "https://login.taobao.com/",
    "tmall": "https://login.taobao.com/",
    "pinduoduo": "https://jinbao.pinduoduo.com/",
    "douyin": "https://www.douyin.com/",
    "alibaba": "https://passport.alibaba.com/",
}


def ensure_1688_browser_login(
    profile: str = "default",
    timeout_sec: int = 300,
    force: bool = False,
) -> dict[str, Any]:
    """Automatically launch a real Chrome browser window, wait for login confirmation, and emit onboarding guide."""
    binary = shutil.which("1688")
    if not binary:
        return {"ok": False, "error": "1688-cli not found."}

    if not force:
        status = inspect_1688_status()
        if status.get("logged_in"):
            identity = status.get("identity") or read_1688_state_identity()
            return {
                "ok": True,
                "confirmed": True,
                "already_logged_in": True,
                "profile": profile,
                "identity": identity,
                "onboarding_guide": build_onboarding_guide(identity),
            }

    cmd = [
        binary,
        "login",
        "--headed",
        "--profile",
        profile,
        "--timeout",
        str(timeout_sec),
    ]
    if force:
        cmd.append("--force")

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_sec + 30,
        check=False,
    )
    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    identity = read_1688_state_identity()
    confirmed = proc.returncode == 0 and identity is not None
    return {
        "ok": confirmed,
        "confirmed": confirmed,
        "exit_code": proc.returncode,
        "profile": profile,
        "identity": identity,
        "onboarding_guide": build_onboarding_guide(identity) if confirmed else None,
        "command": cmd,
        "stdout": stdout or None,
        "stderr": stderr or None,
    }


def open_platform_browser(platform: str, url: str | None = None) -> dict[str, Any]:
    """Automatically open a real browser window for the specified platform without user CLI action."""
    plat = platform.lower().strip()
    if plat == "1688" and url is None:
        return ensure_1688_browser_login(force=False)

    target_url = url or PLATFORM_LOGIN_URLS.get(plat, "https://www.1688.com/")
    if sys.platform == "darwin":
        cmd = ["open", "-a", "Google Chrome", target_url]
    elif sys.platform.startswith("linux"):
        cmd = ["xdg-open", target_url]
    else:
        cmd = ["cmd", "/c", "start", target_url]

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15, check=False)
    return {
        "ok": proc.returncode == 0,
        "platform": plat,
        "url": target_url,
        "command": cmd,
        "stderr": (proc.stderr or "").strip() or None,
    }


def run_1688_command(
    args_list: list[str],
    output_path: str | None = None,
    auto_login: bool = True,
) -> dict[str, Any]:
    binary = shutil.which("1688")
    if not binary:
        result = {"ok": False, "error": "1688-cli not found."}
        if output_path:
            write_json(Path(output_path), result)
        return result

    non_auth_cmds = {"doctor", "login", "logout", "whoami", "help", "--help", "-h", "--version", "-V"}
    first_arg = args_list[0] if args_list else ""

    login_event: dict[str, Any] | None = None
    if auto_login and first_arg not in non_auth_cmds:
        status = inspect_1688_status()
        if not status.get("logged_in"):
            login_event = ensure_1688_browser_login(force=False)

    proc = subprocess.run(
        [binary, *args_list],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()

    combined_lower = f"{stdout}\n{stderr}".lower()
    if (
        auto_login
        and proc.returncode != 0
        and first_arg not in non_auth_cmds
        and any(k in combined_lower for k in ("not logged in", "login_required", "login required", "session expired"))
    ):
        login_event = ensure_1688_browser_login(force=True)
        if login_event.get("ok"):
            proc = subprocess.run(
                [binary, *args_list],
                capture_output=True,
                text=True,
                timeout=90,
                check=False,
            )
            stdout = (proc.stdout or "").strip()
            stderr = (proc.stderr or "").strip()

    parsed_data: Any = None
    if stdout:
        try:
            parsed_data = json.loads(stdout)
        except json.JSONDecodeError:
            parsed_data = stdout

    result = {
        "timestamp": utc_now_iso(),
        "command": ["1688", *args_list],
        "exit_code": proc.returncode,
        "ok": proc.returncode == 0,
        "auto_login_triggered": login_event is not None,
        "login_event": login_event,
        "data": parsed_data,
        "stderr": stderr if stderr else None,
    }
    if output_path:
        write_json(Path(output_path), result)
    return result


def _parse_cny_float(val: Any) -> float | None:
    if val is None:
        return None
    if isinstance(val, dict):
        val = val.get("min") or val.get("value")
    if val is None:
        return None
    try:
        return float(str(val).replace("¥", "").replace("￥", "").replace("$", "").strip())
    except (TypeError, ValueError):
        return None


def resolve_tier_price_cny(item: dict[str, Any], target_qty: int = 50) -> float | None:
    """Resolve EXW unit price in CNY for target_qty using priceTiers when quantity breaks exist."""
    base_price = _parse_cny_float(item.get("price") if item.get("price") is not None else item.get("priceMin"))
    tiers = item.get("priceTiers")
    valid_tiers: list[tuple[int, float]] = []
    if isinstance(tiers, list):
        for t in tiers:
            if not isinstance(t, dict):
                continue
            p = _parse_cny_float(t.get("price"))
            if p is None:
                continue
            try:
                mq = int(t.get("minQty") or t.get("beginAmount") or 1)
            except (TypeError, ValueError):
                mq = 1
            valid_tiers.append((mq, p))

    if valid_tiers:
        distinct_min_qtys = {mq for mq, _ in valid_tiers}
        max_min_qty = max(distinct_min_qtys)
        # Apply tier matching when genuine quantity breaks exist (max_min_qty > 1 or multiple distinct minQty values)
        # or when base_price is missing. Preserve base_price when all entries are SKU variants at minQty==1.
        if max_min_qty > 1 or len(distinct_min_qtys) > 1 or base_price is None:
            eligible = [(mq, p) for mq, p in valid_tiers if mq <= target_qty]
            if eligible:
                max_eligible_mq = max(mq for mq, _ in eligible)
                matching_prices = [p for mq, p in eligible if mq == max_eligible_mq]
                return min(matching_prices)
            lowest_mq = min(mq for mq, _ in valid_tiers)
            lowest_prices = [p for mq, p in valid_tiers if mq == lowest_mq]
            return min(lowest_prices)

    return base_price


def extract_package_metrics(item: dict[str, Any]) -> dict[str, Any]:
    """Extract unit weight (kg) and unit volume (m³) with 3-tier gram/kg disambiguation."""
    volume_cbm: float | None = None
    vol_weight_kg: float = 0.0

    if item.get("volume_cbm") is not None:
        try:
            v_val = float(item["volume_cbm"])
            if v_val > 0:
                volume_cbm = v_val
        except (TypeError, ValueError):
            pass

    pkg: dict[str, Any] | None = None
    if isinstance(item.get("packageInfo"), list) and item["packageInfo"]:
        first_pkg = item["packageInfo"][0]
        if isinstance(first_pkg, dict):
            pkg = first_pkg

    if pkg is not None:
        try:
            length_cm = float(pkg.get("length") or 0.0)
            width_cm = float(pkg.get("width") or 0.0)
            height_cm = float(pkg.get("height") or 0.0)
        except (TypeError, ValueError):
            length_cm = width_cm = height_cm = 0.0

        dim_cm3 = length_cm * width_cm * height_cm if (length_cm > 0 and width_cm > 0 and height_cm > 0) else 0.0
        if dim_cm3 > 0:
            vol_weight_kg = dim_cm3 / 6000.0

        vol_cm3 = 0.0
        if pkg.get("volume") is not None:
            try:
                vol_cm3 = float(pkg["volume"])
            except (TypeError, ValueError):
                vol_cm3 = 0.0
        if vol_cm3 <= 0 and dim_cm3 > 0:
            vol_cm3 = dim_cm3
        if volume_cbm is None and vol_cm3 > 0:
            volume_cbm = round(vol_cm3 / 1_000_000.0, 6)

    def _parse_weight_field(raw_val: Any, from_1688_pkg: bool = False) -> tuple[float | None, str | None]:
        if raw_val is None:
            return None, None
        raw_str = str(raw_val).strip().lower()
        if not raw_str:
            return None, None
        num_match = re.search(r"(\d+(?:\.\d+)?)", raw_str)
        if not num_match:
            return None, None
        w_float = float(num_match.group(1))
        if w_float <= 0:
            return None, None

        if any(u in raw_str for u in ("kg", "千克", "公斤")):
            return round(w_float, 6), "kg_suffix"
        if any(u in raw_str for u in ("g", "克")):
            return round(w_float / 1000.0, 6), "g_suffix->kg"

        if from_1688_pkg:
            # 1688 packageInfo[].weight is denominated in grams (e.g. 161 -> 0.161 kg, 5 -> 0.005 kg)
            if w_float > 10 or (vol_weight_kg > 0 and w_float > 20.0 * vol_weight_kg) or w_float >= 1.0:
                return round(w_float / 1000.0, 6), "g->kg"
            return round(w_float, 6), "sub1_kg"

        return round(w_float, 6), "explicit_kg"

    # Priority 1: explicit weight_kg, unitWeight, or freight.unitWeight
    explicit_candidates = [
        item.get("weight_kg"),
        item.get("unitWeight"),
        (item.get("freight") or {}).get("unitWeight") if isinstance(item.get("freight"), dict) else None,
    ]
    for cand in explicit_candidates:
        w_kg, w_unit = _parse_weight_field(cand, from_1688_pkg=False)
        if w_kg is not None:
            return {
                "weight_kg": w_kg,
                "volume_cbm": volume_cbm,
                "weight_unit_inferred": w_unit,
            }

    # Priority 2: packageInfo[0]["weight"]
    if pkg is not None and pkg.get("weight") is not None:
        w_kg, w_unit = _parse_weight_field(pkg.get("weight"), from_1688_pkg=True)
        if w_kg is not None:
            return {
                "weight_kg": w_kg,
                "volume_cbm": volume_cbm,
                "weight_unit_inferred": w_unit,
            }

    return {
        "weight_kg": None,
        "volume_cbm": volume_cbm,
        "weight_unit_inferred": None,
    }


def generate_sourcing_report(
    offers_json_path: str,
    output_md_path: str,
    output_csv_path: str | None = None,
    output_wangwang_path: str | None = None,
    exchange_rate_vnd: float = DEFAULT_EXCHANGE_RATE_VND,
    vn_shipping_per_kg_vnd: float = DEFAULT_VN_SHIPPING_PER_KG_VND,
    target_qty: int = 50,
) -> dict[str, Any]:
    raw = json.loads(Path(offers_json_path).read_text(encoding="utf-8"))
    if isinstance(raw, dict) and isinstance(raw.get("data"), dict):
        raw = raw["data"]
    offers: list[dict[str, Any]] = (
        raw if isinstance(raw, list) else raw.get("offers") or raw.get("results") or raw.get("items") or []
    )

    normalized_rows: list[dict[str, Any]] = []
    for idx, item in enumerate(offers, start=1):
        offer_id = str(item.get("offerId") or item.get("id") or item.get("item_id") or f"N/A-{idx}")
        title = str(item.get("title") or item.get("subject") or "[Chưa công bố]")
        platform = str(item.get("platform") or "1688")
        supplier = (
            item.get("supplierName")
            or (item.get("supplier", {}) if isinstance(item.get("supplier"), dict) else {}).get("name")
            or item.get("companyName")
            or item.get("shopName")
            or "[Chưa công bố - Cần hỏi xưởng]"
        )
        url = (
            item.get("url")
            or item.get("link")
            or (f"https://detail.1688.com/offer/{offer_id}.html" if offer_id.isdigit() else "[Chưa công bố]")
        )

        price_cny = resolve_tier_price_cny(item, target_qty=target_qty)

        moq_val = item.get("moq") if item.get("moq") is not None else item.get("minOrderQty")
        if isinstance(moq_val, dict):
            moq_val = moq_val.get("quantity")
        moq_str = str(moq_val) if moq_val is not None else "[Chưa công bố - Cần hỏi xưởng]"

        metrics = extract_package_metrics(item)
        weight_kg = metrics["weight_kg"]
        volume_cbm = metrics["volume_cbm"]

        demand_obj = item.get("demand") if isinstance(item.get("demand"), dict) else {}
        repurchase = (
            item.get("repurchaseRate")
            or item.get("rePurchaseRate")
            or (
                f"{demand_obj['repurchaseRateText']} (30d: {demand_obj['orderCountText']})"
                if demand_obj.get("repurchaseRateText") and demand_obj.get("orderCountText")
                else demand_obj.get("repurchaseRateText")
            )
            or (f"Đã bán: {item['saledCount']}" if item.get("saledCount") else None)
            or (f"Đã bán: {demand_obj['orderCountText']}" if demand_obj.get("orderCountText") else None)
            or "[Chưa công bố]"
        )

        if price_cny is not None:
            est_weight = weight_kg if weight_kg is not None else 0.25
            est_volume = volume_cbm if volume_cbm is not None else 0.002
            cost = calculate_landed_cost(
                exw_price_cny=price_cny,
                quantity=target_qty,
                weight_kg_per_unit=est_weight,
                volume_cbm_per_unit=est_volume,
                exchange_rate_vnd=exchange_rate_vnd,
                vn_shipping_per_kg_vnd=vn_shipping_per_kg_vnd,
            )
            landed_str = f"{cost['unit_landed_cost_vnd']:,} VNĐ" + (
                " *(ước tính 0.25kg)*" if weight_kg is None else ""
            )
            official_base = cost["official_import_over_1cbm"]["unit_base_landed_before_vat_and_service_vnd"]
            official_str = f"{official_base:,} VNĐ (+ VAT + phí DV)"
            price_str = f"¥{price_cny:.2f}"
        else:
            landed_str = "[Chưa công bố - Cần hỏi xưởng]"
            official_str = "[Chưa công bố - Cần hỏi xưởng]"
            price_str = "[Chưa công bố]"

        weight_str = f"{weight_kg:.3f} kg" if weight_kg is not None else "[Chưa công bố - Cần hỏi xưởng]"

        normalized_rows.append(
            {
                "rank": idx,
                "platform": platform,
                "offer_id": offer_id,
                "title": title,
                "supplier": supplier,
                "price_exw": price_str,
                "moq": moq_str,
                "weight": weight_str,
                "repurchase_rate": str(repurchase),
                "landed_cost_vnd": landed_str,
                "official_landed_cost_vnd": official_str,
                "url": url,
            }
        )

    md_lines = [
        "# Báo Cáo So Sánh & Thẩm Định Nguồn Hàng Trung Quốc",
        "",
        f"- **Thời gian trích xuất:** `{utc_now_iso()}`",
        f"- **Tỷ giá CNY áp dụng:** `{exchange_rate_vnd:,.0f} VNĐ / 1 CNY` *(Liên hệ [https://t.me/dungtq87]({SUPPORT_CONTACT_URL}) nếu cần hỗ trợ đổi tệ / thanh toán)*",
        f"- **Cước vận chuyển TQ–VN (Hàng đi TMĐT):** `{vn_shipping_per_kg_vnd:,.0f} VNĐ / 1 kg`",
        f"- **Cước vận chuyển TQ–VN (Hàng đi Chính ngạch - đơn trên 1 m³):** `{DEFAULT_OFFICIAL_VN_SHIPPING_PER_CBM_VND:,.0f} VNĐ / 1 m³` hoặc `{DEFAULT_OFFICIAL_VN_SHIPPING_PER_KG_VND:,.0f} VNĐ / 1 kg` + **Thuế VAT** + **Phí dịch vụ**",
        f"- **Số lượng tính giá vốn lô đầu:** `{target_qty} sản phẩm`",
        f"- **Hỗ trợ Vận chuyển, Nhập khẩu & OEM sản phẩm:** Liên hệ **[https://t.me/dungtq87]({SUPPORT_CONTACT_URL})**",
        "",
        "## 1. Bảng So Sánh Các Nguồn Hàng / Xưởng Sản Xuất",
        "",
        "| # | Sàn | Tên Xưởng / Nhà Cung Cấp | Mã / Link Offer | Giá EXW | MOQ | Trọng lượng | Tỷ lệ mua lại | Giá vốn về VN (Hàng TMĐT 30k/kg) | Giá cơ sở Chính ngạch (>1m³: 6k/kg hoặc 1.6tr/m³) |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]

    for r in normalized_rows:
        link_cell = f"[{r['offer_id']}]({r['url']})" if str(r["url"]).startswith("http") else r["offer_id"]
        md_lines.append(
            f"| {r['rank']} | {r['platform']} | {r['supplier']} | {link_cell} | {r['price_exw']} | {r['moq']} | {r['weight']} | {r['repurchase_rate']} | {r['landed_cost_vnd']} | {r['official_landed_cost_vnd']} |"
        )

    md_lines.extend(
        [
            "",
            "---",
            f"> **Liên hệ hỗ trợ trực tiếp:** Cần tư vấn phương án vận chuyển tối ưu (TMĐT 30.000đ/kg hoặc Chính ngạch >1m³: 1.600.000đ/m³ · 6.000đ/kg + VAT + phí dịch vụ), thủ tục nhập khẩu, đổi tệ CNY (4.000đ) hoặc đặt xưởng **OEM sản phẩm** riêng, vui lòng liên hệ **[https://t.me/dungtq87]({SUPPORT_CONTACT_URL})**.",
        ]
    )

    out_md = Path(output_md_path)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    if output_csv_path:
        out_csv = Path(output_csv_path)
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "rank",
            "platform",
            "offer_id",
            "supplier",
            "title",
            "price_exw",
            "moq",
            "weight",
            "repurchase_rate",
            "landed_cost_vnd",
            "official_landed_cost_vnd",
            "url",
        ]
        with out_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(normalized_rows)

    if output_wangwang_path:
        ww_lines = [
            "# Bản Nháp Kịch Bản Đàm Phán WangWang (Song Ngữ Trung – Việt)",
            "",
            "> **Cổng an toàn ABM & Quy trình canh tin tự động 5 phút/lần:**",
            "> 1. Chỉ thực thi lệnh `1688 seller inquire` sau khi người dùng / CEO phê duyệt.",
            "> 2. Ngay sau khi gửi tin hỏi giá qua WangWang, Agent **TỰ ĐỘNG ĐẶT LỊCH (`schedule` / cron `*/5 * * * *` — 5 phút 1 lần)** chạy `python3 scripts/china_sourcing.py check-wangwang --receipt runs/<run_id>/07_inquiry_receipt.json` để kiểm tra tin nhắn phản hồi mới trong WangWang, báo cáo lại cho người dùng và hỏi người dùng cần thêm thông tin gì để hỏi tiếp nhà cung cấp.",
            f"> 3. Hỗ trợ vận chuyển, nhập khẩu & đàm phán OEM sản phẩm: **[https://t.me/dungtq87]({SUPPORT_CONTACT_URL})**.",
            "",
        ]
        for r in normalized_rows[:5]:
            idem_key = hashlib.sha256(f"{r['offer_id']}:{target_qty}".encode("utf-8")).hexdigest()[:16]
            ww_lines.extend(
                [
                    f"## Xưởng #{r['rank']}: {r['supplier']} (`{r['offer_id']}`)",
                    f"- **Idempotency Key:** `{idem_key}`",
                    "- **Câu 1 (Hỏi tồn kho, quy cách đóng gói & trọng lượng thực):**",
                    "  - 🇨🇳 `老板你好，请问这款有现货吗？单件带包装的实际重量和外箱尺寸是多少？`",
                    "  - 🇻🇳 *(Chào sếp, mẫu này có sẵn hàng không? Trọng lượng thực tế kèm hộp của 1 chiếc và kích thước thùng carton là bao nhiêu?)*",
                    f"- **Câu 2 (Hỏi giá lấy mẫu & giá sỉ cho {target_qty} chiếc):**",
                    f"  - 🇨🇳 `我们先拿2个样品测一下质量，后续首批订购 {target_qty} 个，请问拿样怎么算？大货最优惠底价是多少？`",
                    f"  - 🇻🇳 *(Bên mình muốn lấy trước 2 mẫu test chất lượng, lô đầu đặt {target_qty} chiếc, giá mẫu tính thế nào và giá sỉ đáy tốt nhất là bao nhiêu?)*",
                    "- **Câu 3 (Hỏi năng lực in Logo OEM & thời gian giao hàng):**",
                    "  - 🇨🇳 `支持定制Logo和专属包装吗？起订量（MOQ）和打样交期是几天？`",
                    "  - 🇻🇳 *(Xưởng có hỗ trợ in Logo riêng và bao bì OEM không? MOQ và thời gian làm mẫu mất mấy ngày?)*",
                    f"- **Lệnh CLI gửi khi đã được CEO phê duyệt:**",
                    f'  ```bash\n  1688 seller inquire {r["offer_id"]} "老板你好，请问这款有现货吗？单件带包装的实际重量是多少？首批订购{target_qty}个有优惠吗？"\n  ```',
                    "",
                ]
            )
        out_ww = Path(output_wangwang_path)
        out_ww.parent.mkdir(parents=True, exist_ok=True)
        out_ww.write_text("\n".join(ww_lines) + "\n", encoding="utf-8")

    return {
        "ok": True,
        "rows_count": len(normalized_rows),
        "markdown_report": str(out_md),
        "csv_report": output_csv_path,
        "wangwang_draft": output_wangwang_path,
        "support_contact": SUPPORT_CONTACT_URL,
    }


SYSTEM_NOTICE_PATTERNS = (
    r"^\[卡片消息\]$",
    r"^\[contentType=",
    r"商家长时间没有回复",
    r"由于当前是节假日期间",
    r"客服现在比较繁忙",
    r"系统消息",
)


def is_human_seller_reply(msg: dict[str, Any]) -> bool:
    """Return True only when msg is a genuine human reply from the seller (not mine, not autoReply/card/system notice)."""
    if not isinstance(msg, dict) or bool(msg.get("isMine")):
        return False
    kind = str(msg.get("kind") or "text").strip()
    if kind in ("assessment", "autoReply", "other", "offerCard", "orderCard", "system", "notice"):
        return False
    content = str(msg.get("content") or "").strip()
    if not content:
        return False
    for pat in SYSTEM_NOTICE_PATTERNS:
        if re.search(pat, content):
            return False
    return True


def message_signature(msg: dict[str, Any], conv_key: str = "", idx: int = 0) -> str:
    """Build a deterministic signature for a WangWang message scoped to its conversation slot."""
    msg_id = str(msg.get("id") or msg.get("msgId") or msg.get("time") or msg.get("timestamp") or idx)
    sender = str(msg.get("sender") or "")
    content = str(msg.get("content") or "").strip()
    raw = f"{conv_key}|{msg_id}|{sender}|{content}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def compute_inquiry_idempotency_key(run_id: str, offer_id: str, inquiry_text: str) -> str:
    """Compute sha256(run_id + offer_id + inquiry_text_hash) idempotency key per ABM Step B7."""
    text_hash = hashlib.sha256(inquiry_text.strip().encode("utf-8")).hexdigest()
    payload = f"{run_id.strip()}:{offer_id.strip()}:{text_hash}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.parent / f".{path.name}.tmp.{os.getpid()}"
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp_path, path)


def inquire_wangwang(
    offer_id: str,
    message: str,
    run_id: str = "default",
    seller_login_id: str | None = None,
    supplier: str | None = None,
    rank: int = 1,
    receipt_json_path: str | None = None,
    screenshot_path: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Send a WangWang inquiry with SHA-256 idempotency protection and BB1688_SCREENSHOT_PATH proof capture."""
    idem_key = compute_inquiry_idempotency_key(run_id=run_id, offer_id=str(offer_id), inquiry_text=message)
    receipt_path = Path(receipt_json_path) if receipt_json_path else None
    receipt_doc: dict[str, Any] = {"run_id": run_id, "updated_at": utc_now_iso(), "receipts": []}

    if receipt_path and receipt_path.exists():
        try:
            loaded = json.loads(receipt_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                receipt_doc = loaded
                if "receipts" not in receipt_doc:
                    receipt_doc["receipts"] = (
                        receipt_doc.get("inquiries") or receipt_doc.get("results") or []
                    )
            elif isinstance(loaded, list):
                receipt_doc["receipts"] = loaded
        except Exception:
            pass

    existing_receipts: list[dict[str, Any]] = receipt_doc.get("receipts", [])
    if not force:
        for entry in existing_receipts:
            if not isinstance(entry, dict):
                continue
            entry_key = entry.get("idempotency_key")
            same_offer_sent = (
                str(entry.get("offer_id") or "") == str(offer_id)
                and (entry.get("ok") is True or entry.get("status") in ("sent", "ok"))
                and entry_key in (idem_key, None)
            )
            if entry_key == idem_key or same_offer_sent:
                return {
                    "ok": True,
                    "status": "skipped_duplicate",
                    "skipped_duplicate": True,
                    "idempotency_key": idem_key,
                    "run_id": run_id,
                    "offer_id": str(offer_id),
                    "existing_receipt": entry,
                }

    binary = shutil.which("1688")
    if not binary:
        return {
            "ok": False,
            "status": "error",
            "idempotency_key": idem_key,
            "error": "1688-cli not installed",
        }

    cmd_args = [binary, "seller", "inquire", str(offer_id), message]
    if seller_login_id:
        cmd_args.extend(["--to", seller_login_id])
    cmd_args.append("--json")

    env = dict(os.environ)
    if screenshot_path:
        Path(screenshot_path).parent.mkdir(parents=True, exist_ok=True)
        env["BB1688_SCREENSHOT_PATH"] = str(screenshot_path)

    proc = subprocess.run(
        cmd_args,
        capture_output=True,
        text=True,
        timeout=90,
        env=env,
        check=False,
    )
    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    parsed: dict[str, Any] = {}
    if stdout:
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            parsed = {"raw": stdout}

    ok = proc.returncode == 0 and bool(parsed.get("ok", proc.returncode == 0))
    resolved_seller = (
        seller_login_id
        or parsed.get("sentTo")
        or parsed.get("sellerLoginId")
        or supplier
        or str(offer_id)
    )
    entry_record: dict[str, Any] = {
        "rank": rank,
        "offer_id": str(offer_id),
        "supplier": supplier or resolved_seller,
        "seller_login_id": resolved_seller,
        "idempotency_key": idem_key,
        "run_id": run_id,
        "inquiry_text": message,
        "screenshot": str(screenshot_path) if screenshot_path else parsed.get("screenshotPath"),
        "ok": ok,
        "status": "sent" if ok else "failed",
        "sent_at": utc_now_iso(),
        "response": parsed,
        "stderr": stderr or None,
    }

    if receipt_path:
        existing_receipts.append(entry_record)
        receipt_doc["updated_at"] = utc_now_iso()
        receipt_doc["receipts"] = existing_receipts
        _atomic_write_json(receipt_path, receipt_doc)

    return entry_record


def check_wangwang_replies(
    receipt_json_path: str | None = None,
    seller_login_id: str | None = None,
    offer_id: str | None = None,
    limit: int = 20,
    output_path: str | None = None,
    state_file_path: str | None = None,
    only_new: bool = False,
    mock_conversations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Check 1688 WangWang conversations for human seller replies with optional delta state tracking."""
    targets: list[dict[str, Any]] = []
    if receipt_json_path and Path(receipt_json_path).exists():
        raw_receipt = json.loads(Path(receipt_json_path).read_text(encoding="utf-8"))
        receipt_items = (
            raw_receipt
            if isinstance(raw_receipt, list)
            else raw_receipt.get("receipts") or raw_receipt.get("inquiries") or raw_receipt.get("results") or []
        )
        for item in receipt_items:
            if not isinstance(item, dict):
                continue
            targets.append(
                {
                    "rank": item.get("rank"),
                    "offer_id": str(item.get("offer_id") or ""),
                    "supplier": item.get("supplier") or item.get("seller_login_id"),
                    "seller_login_id": item.get("seller_login_id") or item.get("sentTo"),
                }
            )
    elif seller_login_id or offer_id:
        targets.append(
            {
                "rank": 1,
                "offer_id": str(offer_id or ""),
                "supplier": seller_login_id or offer_id,
                "seller_login_id": seller_login_id,
            }
        )

    seen_keys: set[str] = set()
    state_path = Path(state_file_path) if state_file_path else None
    if state_path and state_path.exists():
        try:
            state_data = json.loads(state_path.read_text(encoding="utf-8"))
            if isinstance(state_data, dict) and isinstance(state_data.get("seen_message_keys"), list):
                seen_keys = {str(k) for k in state_data["seen_message_keys"]}
        except Exception:
            pass

    binary = shutil.which("1688")
    conversations: list[dict[str, Any]] = []
    total_human_replies = 0
    total_new_human_replies = 0

    source_items = mock_conversations if mock_conversations is not None else targets
    for t_idx, t in enumerate(source_items):
        if mock_conversations is not None:
            msgs = t.get("all_messages") or t.get("messages") or []
            proc_ok = bool(t.get("ok", True))
            base_meta = {
                k: v
                for k, v in t.items()
                if k
                not in (
                    "all_messages",
                    "messages",
                    "seller_replies",
                    "seller_replies_count",
                    "human_replies",
                    "new_human_replies",
                    "auto_or_system_messages",
                )
            }
        else:
            cmd_args: list[str] = ["seller", "messages"]
            if t.get("seller_login_id"):
                cmd_args.append(str(t["seller_login_id"]))
            if t.get("offer_id"):
                cmd_args.extend(["--offer", str(t["offer_id"])])
            cmd_args.extend(["--limit", str(limit), "--json"])

            if not binary:
                conversations.append({**t, "ok": False, "error": "1688-cli not installed"})
                continue

            proc = subprocess.run(
                [binary, *cmd_args],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            stdout = (proc.stdout or "").strip()
            parsed: dict[str, Any] = {}
            if stdout:
                try:
                    parsed = json.loads(stdout)
                except json.JSONDecodeError:
                    parsed = {"raw": stdout}
            msgs = parsed.get("messages", []) if isinstance(parsed, dict) else []
            proc_ok = proc.returncode == 0
            base_meta = dict(t)

        conv_key = str(
            base_meta.get("seller_login_id")
            or base_meta.get("supplier")
            or base_meta.get("offer_id")
            or f"conv-{t_idx}"
        )
        human_replies: list[dict[str, Any]] = []
        new_human_replies: list[dict[str, Any]] = []
        auto_or_system_messages: list[dict[str, Any]] = []

        for m_idx, m in enumerate(msgs):
            if not isinstance(m, dict) or bool(m.get("isMine")):
                continue
            if is_human_seller_reply(m):
                human_replies.append(m)
                sig = message_signature(m, conv_key=conv_key, idx=m_idx)
                if sig not in seen_keys:
                    new_human_replies.append(m)
                    seen_keys.add(sig)
            else:
                auto_or_system_messages.append(m)

        active_replies = new_human_replies if only_new else human_replies
        total_human_replies += len(human_replies)
        total_new_human_replies += len(new_human_replies)

        conversations.append(
            {
                **base_meta,
                "ok": proc_ok,
                "total_messages": len(msgs),
                "seller_replies_count": len(active_replies),
                "seller_replies": active_replies,
                "human_replies_count": len(human_replies),
                "human_replies": human_replies,
                "new_human_replies_count": len(new_human_replies),
                "new_human_replies": new_human_replies,
                "auto_or_system_count": len(auto_or_system_messages),
                "auto_or_system_messages": auto_or_system_messages,
                "all_messages": msgs,
            }
        )

    if state_path:
        _atomic_write_json(
            state_path,
            {
                "updated_at": utc_now_iso(),
                "seen_message_keys": sorted(seen_keys),
            },
        )

    result = {
        "timestamp": utc_now_iso(),
        "poll_interval_minutes": 5,
        "checked_count": len(conversations),
        "total_human_replies": total_human_replies,
        "total_new_human_replies": total_new_human_replies,
        "has_new_human_replies": total_new_human_replies > 0,
        "conversations": conversations,
        "follow_up_question_for_user": (
            "Bạn có cần hỏi thêm thông tin gì với các nhà cung cấp này không "
            "(ví dụ: xin video quay thực tế tại xưởng, bảng giá bậc thang cho 500-1.000 chiếc, "
            "chứng chỉ CE/RoHS/kiểm định chất lượng, hoặc chốt đặt 2 mẫu về test)?"
        ),
        "support_contact": SUPPORT_CONTACT_URL,
        "support_note": SUPPORT_CONTACT_NOTE,
    }
    if output_path:
        _atomic_write_json(Path(output_path), result)
    return result


def parse_cn_count(text: Any) -> int | None:
    """Parse Chinese sales/order count strings such as '已售3.4万+件', '1.2w', '500+件', '小于10件' into an integer."""
    if text is None or isinstance(text, bool):
        return None
    if isinstance(text, (int, float)):
        return max(0, round(float(text))) if math.isfinite(float(text)) else None
    raw = str(text).strip()
    if not raw:
        return None
    if any(k in raw for k in ("小于", "不足", "未售", "暂无")):
        return 0
    compact = raw.replace(",", "").replace(" ", "")
    m = re.search(r"(\d+(?:\.\d+)?)\s*(亿|万|w|W|千|k|K)?", compact)
    if not m:
        return None
    val = float(m.group(1))
    unit = m.group(2) or ""
    mult = (
        100_000_000
        if unit == "亿"
        else 10_000
        if unit in ("万", "w", "W")
        else 1_000
        if unit in ("千", "k", "K")
        else 1
    )
    return max(0, round(val * mult))


def _parse_percent_float(val: Any) -> float | None:
    if val is None or isinstance(val, bool):
        return None
    if isinstance(val, (int, float)):
        return float(val) if math.isfinite(float(val)) else None
    m = re.search(r"(\d+(?:\.\d+)?)\s*%?", str(val))
    return float(m.group(1)) if m else None


def build_1688_rank_urls(rank_badge: dict[str, Any]) -> dict[str, str]:
    """Generate direct 1688 Leaderboard URLs for Best-Selling (rankType=1), Fast-Rising (rankType=2), and Hot-New (rankType=3)."""
    raw_url = str(rank_badge.get("url") or "").strip()
    if not raw_url:
        return {}
    try:
        parsed = urllib.parse.urlsplit(raw_url)
        qs = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        out: dict[str, str] = {"base_url": raw_url}
        for key_name, rtype in (("hot_selling_url", "1"), ("fast_rising_url", "2"), ("hot_new_url", "3")):
            qs_copy = dict(qs)
            qs_copy["rankType"] = [rtype]
            new_query = urllib.parse.urlencode(qs_copy, doseq=True)
            out[key_name] = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, new_query, parsed.fragment))
        return out
    except Exception:
        return {"base_url": raw_url}


def compute_offer_trend_metrics(
    offer: dict[str, Any],
    prev_snapshot_entry: dict[str, Any] | None = None,
    elapsed_hours: float | None = None,
) -> dict[str, Any]:
    """Compute log-damped VelocityIndex, HotNewScore (0-100), FastRisingScore (0-100), and snapshot delta."""
    demand = offer.get("demand") if isinstance(offer.get("demand"), dict) else {}
    ts = offer.get("trendSignals") if isinstance(offer.get("trendSignals"), dict) else {}

    booked_30d = (
        parse_cn_count(
            demand.get("orderCount")
            if demand.get("orderCount") is not None
            else (demand.get("orderCountText") or offer.get("turnover") or offer.get("saledCount"))
        )
        or 0
    )
    sold_total_raw = parse_cn_count(
        ts.get("soldCountTotal") if ts.get("soldCountTotal") is not None else ts.get("soldCountText")
    )
    sold_total = sold_total_raw if (sold_total_raw is not None and sold_total_raw > 0) else booked_30d

    repurchase_rate = _parse_percent_float(
        demand.get("repurchaseRate")
        if demand.get("repurchaseRate") is not None
        else (demand.get("repurchaseRateText") or offer.get("repurchaseRate"))
    )

    # Log-damped VelocityIndex formula (Kongming checkpoint approved):
    # Prevents small-denominator illusion (5/5 = 100%) and bucket truncation (>1.0)
    denom = max(sold_total, booked_30d, 50)
    recency_share = min(1.0, max(0.0, booked_30d / denom)) if booked_30d > 0 else 0.0
    velocity_index = round(math.log10(booked_30d + 1) * (0.5 + 0.5 * recency_share), 4)

    new_sell_points = [str(x) for x in (ts.get("newProductSellPoints") or []) if x]
    rank_badges = [x for x in (ts.get("rankBadges") or []) if isinstance(x, dict)]
    business_topics = [x for x in (ts.get("businessOppoTopics") or []) if isinstance(x, dict)]
    price_badges = [str(x) for x in (ts.get("priceCompetitiveBadges") or []) if x]
    fenxiao_new = bool(ts.get("fenxiaoNewOffer"))
    kuajing_hot = bool(ts.get("kuaJingPuHuo"))
    trade_score = _parse_cny_float(ts.get("tradeScore"))

    delta_orders: int | None = None
    delta_orders_per_day: float | None = None
    if isinstance(prev_snapshot_entry, dict) and prev_snapshot_entry.get("booked_30d") is not None:
        try:
            prev_b = int(prev_snapshot_entry["booked_30d"])
            delta_orders = booked_30d - prev_b
            eff_hours = max(float(elapsed_hours) if elapsed_hours else 24.0, 0.1)
            delta_orders_per_day = round((delta_orders / eff_hours) * 24.0, 2)
        except (TypeError, ValueError):
            pass

    # Fast-Rising Score (0-100)
    vel_base = min(60.0, velocity_index * 13.5)
    vel_bonus = 0.0
    if rank_badges:
        vel_bonus += 15.0
    if price_badges:
        vel_bonus += 10.0
    if (repurchase_rate or 0.0) >= 20.0:
        vel_bonus += 10.0
    elif (repurchase_rate or 0.0) >= 10.0:
        vel_bonus += 5.0
    if (delta_orders_per_day or 0.0) > 0:
        vel_bonus += min(15.0, 5.0 + math.log10((delta_orders_per_day or 1.0) + 1.0) * 5.0)
    fast_rising_score = min(100, round(vel_base + vel_bonus))

    # Hot-New Score (0-100)
    hot_new_pts = 0.0
    if new_sell_points:
        hot_new_pts += 45.0
    if fenxiao_new:
        hot_new_pts += 15.0
    if business_topics:
        has_recent_topic = any(str(t.get("topicDate") or "").startswith("2026") for t in business_topics)
        hot_new_pts += 22.0 if has_recent_topic else 15.0
    if price_badges:
        hot_new_pts += 8.0
    hot_new_pts += min(25.0, math.log10(booked_30d + 1) * 5.5)
    hot_new_score = min(100, round(hot_new_pts))
    is_hot_new = bool(new_sell_points or fenxiao_new or hot_new_score >= 45)

    return {
        "booked_30d": booked_30d,
        "sold_total": sold_total,
        "sold_count_text": ts.get("soldCountText") or (f"30d:{booked_30d}" if booked_30d else None),
        "recency_share": round(recency_share, 4),
        "velocity_index": velocity_index,
        "fast_rising_score": fast_rising_score,
        "hot_new_score": hot_new_score,
        "is_hot_new": is_hot_new,
        "repurchase_rate": repurchase_rate,
        "new_product_sell_points": new_sell_points,
        "rank_badges": rank_badges,
        "business_oppo_topics": business_topics,
        "price_competitive_badges": price_badges,
        "fenxiao_new_offer": fenxiao_new,
        "kuajing_puhuo": kuajing_hot,
        "trade_score": trade_score,
        "delta_orders": delta_orders,
        "delta_orders_per_day": delta_orders_per_day,
    }


def analyze_1688_trends(
    offers: list[dict[str, Any]],
    keyword: str,
    mode: str = "all",
    target_qty: int = 100,
    exchange_rate_vnd: float = DEFAULT_EXCHANGE_RATE_VND,
    vn_shipping_per_kg_vnd: float = DEFAULT_VN_SHIPPING_PER_KG_VND,
    state_file_path: str | None = None,
    top_limit: int = 10,
) -> dict[str, Any]:
    """Analyze a list of 1688 offers for Hot New Arrivals, Fast-Rising Sales Velocity, and Niche Trends."""
    now_iso = utc_now_iso()
    now_dt = datetime.now(timezone.utc)
    state_path = Path(state_file_path) if state_file_path else None
    prev_offers_map: dict[str, dict[str, Any]] = {}
    elapsed_hours: float | None = None

    if state_path and state_path.exists():
        try:
            prev_doc = json.loads(state_path.read_text(encoding="utf-8"))
            if isinstance(prev_doc, dict):
                prev_offers_map = prev_doc.get("offers") if isinstance(prev_doc.get("offers"), dict) else {}
                prev_ts = str(prev_doc.get("updated_at") or "")
                if prev_ts:
                    prev_dt = datetime.fromisoformat(prev_ts.replace("Z", "+00:00"))
                    elapsed_hours = max(0.01, (now_dt - prev_dt).total_seconds() / 3600.0)
        except Exception:
            prev_offers_map = {}

    enriched_offers: list[dict[str, Any]] = []
    topic_clusters: dict[str, dict[str, Any]] = {}
    leaderboards_map: dict[str, dict[str, Any]] = {}
    new_snapshot_map: dict[str, dict[str, Any]] = dict(prev_offers_map)

    for item in offers:
        if not isinstance(item, dict):
            continue
        offer_id = str(item.get("offerId") or item.get("id") or "").strip()
        if not offer_id:
            continue
        title = str(item.get("title") or "").strip()
        supplier_obj = item.get("supplier") if isinstance(item.get("supplier"), dict) else {}
        supplier_name = (
            item.get("supplierName")
            or supplier_obj.get("name")
            or item.get("companyName")
            or "[Chưa công bố]"
        )
        price_cny = resolve_tier_price_cny(item, target_qty=target_qty)
        pkg_metrics = extract_package_metrics(item)
        est_weight = pkg_metrics["weight_kg"] if pkg_metrics["weight_kg"] is not None else 0.25
        est_vol = pkg_metrics["volume_cbm"] if pkg_metrics["volume_cbm"] is not None else 0.002

        landed_tmdt_vnd: int | None = None
        landed_official_vnd: int | None = None
        if price_cny is not None and price_cny > 0:
            cost = calculate_landed_cost(
                exw_price_cny=price_cny,
                quantity=target_qty,
                weight_kg_per_unit=est_weight,
                volume_cbm_per_unit=est_vol,
                exchange_rate_vnd=exchange_rate_vnd,
                vn_shipping_per_kg_vnd=vn_shipping_per_kg_vnd,
            )
            landed_tmdt_vnd = cost["unit_landed_cost_vnd"]
            landed_official_vnd = cost["official_import_over_1cbm"]["unit_base_landed_before_vat_and_service_vnd"]

        prev_entry = prev_offers_map.get(offer_id)
        t_metrics = compute_offer_trend_metrics(item, prev_snapshot_entry=prev_entry, elapsed_hours=elapsed_hours)

        new_snapshot_map[offer_id] = {
            "offer_id": offer_id,
            "title": title,
            "price_cny": price_cny,
            "booked_30d": t_metrics["booked_30d"],
            "sold_total": t_metrics["sold_total"],
            "updated_at": now_iso,
        }

        verified_obj = item.get("verified") if isinstance(item.get("verified"), dict) else {}
        is_factory = bool(verified_obj.get("factory") or verified_obj.get("superFactory") or item.get("bizType") == "生产加工")

        row = {
            "offer_id": offer_id,
            "title": title,
            "supplier": supplier_name,
            "supplier_years": supplier_obj.get("years"),
            "is_factory": is_factory,
            "price_cny": price_cny,
            "landed_cost_tmdt_vnd": landed_tmdt_vnd,
            "landed_cost_official_base_vnd": landed_official_vnd,
            "url": item.get("url") or f"https://detail.1688.com/offer/{offer_id}.html",
            "image": item.get("image"),
            **t_metrics,
        }
        enriched_offers.append(row)

        for b_topic in t_metrics["business_oppo_topics"]:
            topic_name = str(b_topic.get("topic") or b_topic.get("text") or "").strip()
            if not topic_name:
                continue
            cluster = topic_clusters.setdefault(
                topic_name,
                {
                    "topic": topic_name,
                    "topic_id": b_topic.get("topicId"),
                    "topic_date": b_topic.get("topicDate"),
                    "category_id": b_topic.get("categoryId"),
                    "url": b_topic.get("url"),
                    "offer_count": 0,
                    "total_booked_30d": 0,
                    "sample_offers": [],
                },
            )
            cluster["offer_count"] += 1
            cluster["total_booked_30d"] += t_metrics["booked_30d"]
            if len(cluster["sample_offers"]) < 3:
                cluster["sample_offers"].append(
                    {
                        "offer_id": offer_id,
                        "title": title,
                        "price_cny": price_cny,
                        "booked_30d": t_metrics["booked_30d"],
                    }
                )

        for r_badge in t_metrics["rank_badges"]:
            r_name = str(r_badge.get("rankName") or r_badge.get("text") or "").strip()
            if not r_name:
                continue
            if r_name not in leaderboards_map:
                urls = build_1688_rank_urls(r_badge)
                leaderboards_map[r_name] = {
                    "rank_name": r_name,
                    "badge_text": r_badge.get("text"),
                    "category_id": r_badge.get("categoryId"),
                    "rank_full_name_id": r_badge.get("rankFullNameId"),
                    "featured_offer_id": offer_id,
                    "urls": urls,
                }

    if state_path:
        _atomic_write_json(
            state_path,
            {
                "updated_at": now_iso,
                "keyword": keyword,
                "offers": new_snapshot_map,
            },
        )

    hot_new_offers = sorted(
        [o for o in enriched_offers if o["is_hot_new"]],
        key=lambda x: (x["hot_new_score"], x["velocity_index"], x["booked_30d"]),
        reverse=True,
    )[:top_limit]
    if not hot_new_offers:
        hot_new_offers = sorted(
            enriched_offers,
            key=lambda x: (x["hot_new_score"], x["velocity_index"]),
            reverse=True,
        )[:top_limit]

    fast_rising_offers = sorted(
        enriched_offers,
        key=lambda x: (
            x["delta_orders_per_day"] if x["delta_orders_per_day"] is not None else -1e9,
            x["fast_rising_score"],
            x["velocity_index"],
            x["booked_30d"],
        ),
        reverse=True,
    )[:top_limit]

    niche_trend_clusters = sorted(
        topic_clusters.values(),
        key=lambda c: (c["offer_count"], c["total_booked_30d"]),
        reverse=True,
    )

    return {
        "ok": True,
        "timestamp": now_iso,
        "keyword": keyword,
        "mode": mode,
        "target_qty": target_qty,
        "total_scanned": len(enriched_offers),
        "snapshot_tracking": {
            "enabled": bool(state_path),
            "state_file": str(state_path) if state_path else None,
            "previous_snapshot_found": elapsed_hours is not None,
            "elapsed_hours": round(elapsed_hours, 2) if elapsed_hours is not None else None,
        },
        "summary_counts": {
            "hot_new_candidates": sum(1 for o in enriched_offers if o["is_hot_new"]),
            "offers_with_new_sell_point": sum(1 for o in enriched_offers if o["new_product_sell_points"]),
            "niche_trend_clusters": len(niche_trend_clusters),
            "category_leaderboards": len(leaderboards_map),
        },
        "hot_new_offers": hot_new_offers,
        "fast_rising_offers": fast_rising_offers,
        "niche_trend_clusters": niche_trend_clusters,
        "category_leaderboards": list(leaderboards_map.values()),
        "support_contact": SUPPORT_CONTACT_URL,
        "support_note": SUPPORT_CONTACT_NOTE,
    }


def format_trends_markdown(report: dict[str, Any]) -> str:
    """Format the 1688 Trend & Velocity Radar output into a comprehensive Vietnamese Markdown report."""
    kw = report.get("keyword") or "N/A"
    qty = report.get("target_qty") or 100
    counts = report.get("summary_counts") or {}
    snap = report.get("snapshot_tracking") or {}
    mode = str(report.get("mode") or "all")

    lines = [
        f"# Báo Cáo Radar Bắt Trend, Sản Phẩm Mới & Tốc Độ Bán 1688 (`{kw}`)",
        "",
        f"- **Thời gian quét:** `{report.get('timestamp')}`",
        f"- **Tổng số mẫu phân tích:** `{report.get('total_scanned', 0)}` sản phẩm (`{counts.get('offers_with_new_sell_point', 0)}` mẫu mới lên kệ `上新`, `{counts.get('niche_trend_clusters', 0)}` cụm xu hướng ngách `商机组货`, `{counts.get('category_leaderboards', 0)}` bảng xếp hạng `排行榜`)",
        f"- **Lô tính giá vốn dự kiến về Việt Nam:** `{qty} chiếc` *(Tỷ giá `4.000đ/CNY`, TMĐT `30.000đ/kg`, Chính ngạch `>1m³`: `1.600.000đ/m³` hoặc `6.000đ/kg`)*",
        f"- **Hỗ trợ Vận chuyển, Nhập khẩu & Đặt xưởng OEM:** **[https://t.me/dungtq87]({SUPPORT_CONTACT_URL})**",
    ]
    if snap.get("enabled"):
        status_txt = (
            f"Đã đối chiếu snapshot trước (cách đây `{snap.get('elapsed_hours')} giờ`)"
            if snap.get("previous_snapshot_found")
            else "Đã lưu snapshot mốc T0 (chạy lại sau để đo tốc độ tăng đơn tuyệt đối Δ đơn/ngày)"
        )
        lines.append(f"- **Theo dõi chênh lệch thời gian thực (`--state-file`):** {status_txt}")
    lines.append("")

    if mode in ("all", "new-hot"):
        lines.extend(
            [
                "## 1. Sản Phẩm Mới Đang Hot (`上新热销 / Hot New Arrivals`)",
                "",
                "| # | Mã Offer | Tên Sản Phẩm & Xưởng | Điểm Nâng Cấp Mới (`上新`) / Nhãn Trend | Giá EXW | Đơn 30 Ngày | Điểm Hot New | Giá Vốn TMĐT (30k/kg) |",
                "|---|---|---|---|---|---|---|---|",
            ]
        )
        for idx, o in enumerate(report.get("hot_new_offers") or [], start=1):
            badges = list(o.get("new_product_sell_points") or [])
            for bt in o.get("business_oppo_topics") or []:
                if bt.get("topic"):
                    badges.append(f"Trend: {bt['topic']}")
            if o.get("fenxiao_new_offer"):
                badges.append("Phân phối mới")
            badge_str = " · ".join(badges) if badges else "Mẫu mới tiềm năng"
            price_str = f"¥{o['price_cny']:.2f}" if o.get("price_cny") is not None else "N/A"
            landed_str = f"{o['landed_cost_tmdt_vnd']:,}đ" if o.get("landed_cost_tmdt_vnd") else "N/A"
            fac_tag = " *(Xưởng)*" if o.get("is_factory") else ""
            lines.append(
                f"| {idx} | [{o['offer_id']}]({o['url']}) | **{o['supplier']}**{fac_tag}<br>{o['title'][:45]} | {badge_str} | {price_str} | {o['booked_30d']:,} | **{o['hot_new_score']}/100** | {landed_str} |"
            )
        lines.append("")

    if mode in ("all", "fast-rising"):
        lines.extend(
            [
                "## 2. Sản Phẩm Có Lượt Bán Tăng Tốc Nhanh Nhất (`飙升 / Fast-Rising Velocity`)",
                "",
                "| # | Mã Offer | Nhà Cung Cấp | Giá EXW | Đơn 30 Ngày / Tổng Bán | Tỷ Lệ Mua Lại | Chỉ Số Tăng Tốc (`Velocity`) | Δ Đơn/Ngày | Giá Vốn TMĐT |",
                "|---|---|---|---|---|---|---|---|---|",
            ]
        )
        for idx, o in enumerate(report.get("fast_rising_offers") or [], start=1):
            price_str = f"¥{o['price_cny']:.2f}" if o.get("price_cny") is not None else "N/A"
            sold_str = f"{o['booked_30d']:,} / {o.get('sold_count_text') or o['sold_total']}"
            rep_str = f"{o['repurchase_rate']:g}%" if o.get("repurchase_rate") is not None else "N/A"
            delta_str = (
                f"{o['delta_orders_per_day']:+g}/ngày ({o['delta_orders']:+d})"
                if o.get("delta_orders_per_day") is not None
                else "Mốc T0"
            )
            landed_str = f"{o['landed_cost_tmdt_vnd']:,}đ" if o.get("landed_cost_tmdt_vnd") else "N/A"
            extra_badges = []
            for rb in o.get("rank_badges") or []:
                if rb.get("text"):
                    extra_badges.append(str(rb["text"]))
            for pb in o.get("price_competitive_badges") or []:
                extra_badges.append(str(pb))
            vel_cell = f"**{o['fast_rising_score']}/100** (`{o['velocity_index']:.2f}`)"
            if extra_badges:
                vel_cell += "<br>" + " · ".join(extra_badges[:2])
            lines.append(
                f"| {idx} | [{o['offer_id']}]({o['url']}) | {o['supplier']} | {price_str} | {sold_str} | {rep_str} | {vel_cell} | {delta_str} | {landed_str} |"
            )
        lines.append("")

    if mode in ("all", "niche-trends"):
        lines.extend(
            [
                "## 3. Cụm Xu Hướng Ngách Đang Lên (`1688 商机组货 / Emerging Niche Clusters`)",
                "",
                "| # | Chủ Đề Ngách Đang Hot (`商机组货`) | Ngày Phát Hiện | Số Mẫu Trong Top | Tổng Đơn 30 Ngày | Sản Phẩm Tiêu Biểu |",
                "|---|---|---|---|---|---|",
            ]
        )
        clusters = report.get("niche_trend_clusters") or []
        if clusters:
            for idx, c in enumerate(clusters, start=1):
                samples = ", ".join(
                    f"`{s['offer_id']}` (¥{s['price_cny']})" if s.get("price_cny") else f"`{s['offer_id']}`"
                    for s in (c.get("sample_offers") or [])
                )
                lines.append(
                    f"| {idx} | **{c['topic']}** | `{c.get('topic_date') or 'Mới'}` | {c['offer_count']} | {c['total_booked_30d']:,} | {samples} |"
                )
        else:
            lines.append("| - | *(Chưa có nhãn cụm 商机组货 cho từ khóa này)* | - | 0 | 0 | - |")
        lines.append("")

        leaderboards = report.get("category_leaderboards") or []
        if leaderboards:
            lines.extend(
                [
                    "## 4. Bảng Xếp Hạng Ngành Hàng Chính Thức 1688 (`1688 排行榜`)",
                    "",
                    "| Tên Bảng Xếp Hạng | Mã Danh Mục | Link Bảng Bán Chạy (`热销榜`) | Link Bảng Tăng Tốc (`飙升榜`) | Link Bảng Hàng Mới (`新品榜`) |",
                    "|---|---|---|---|---|",
                ]
            )
            for lb in leaderboards:
                urls = lb.get("urls") or {}
                u_hot = f"[Mở 热销榜]({urls['hot_selling_url']})" if urls.get("hot_selling_url") else "-"
                u_rise = f"[Mở 飙升榜]({urls['fast_rising_url']})" if urls.get("fast_rising_url") else "-"
                u_new = f"[Mở 新品榜]({urls['hot_new_url']})" if urls.get("hot_new_url") else "-"
                lines.append(
                    f"| **{lb['rank_name']}** ({lb.get('badge_text')}) | `{lb.get('category_id') or 'N/A'}` | {u_hot} | {u_rise} | {u_new} |"
                )
            lines.append("")

    lines.extend(
        [
            "---",
            f"> **Bước tiếp theo:** Bạn có thể chọn bất kỳ mã sản phẩm nào ở trên để yêu cầu Agent **nhắn WangWang hỏi giá sỉ / xin mẫu test (`inquire-wangwang`)** hoặc liên hệ **[https://t.me/dungtq87]({SUPPORT_CONTACT_URL})** để được hỗ trợ vận chuyển và làm hàng OEM.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_1688_trends(
    keywords: list[str] | None = None,
    input_json_path: str | None = None,
    mode: str = "all",
    max_per_keyword: int = 40,
    target_qty: int = 100,
    price_max_cny: float | None = None,
    factory_only: bool = False,
    state_file_path: str | None = None,
    output_json_path: str | None = None,
    output_md_path: str | None = None,
    top_limit: int = 10,
) -> dict[str, Any]:
    """Run live 1688 search (or load saved JSON) and analyze Hot New Products, Fast-Rising Sales, and Niche Trends."""
    collected_offers: list[dict[str, Any]] = []
    seen_offer_ids: set[str] = set()
    kw_label = ", ".join(keywords) if keywords else (Path(input_json_path).stem if input_json_path else "1688")

    if input_json_path:
        raw = json.loads(Path(input_json_path).read_text(encoding="utf-8"))
        if isinstance(raw, dict) and isinstance(raw.get("data"), dict):
            raw = raw["data"]
        items = raw if isinstance(raw, list) else (raw.get("offers") or raw.get("items") or [])
        for it in items:
            if not isinstance(it, dict):
                continue
            cand = it.get("offer") if isinstance(it.get("offer"), dict) else it
            oid = str(cand.get("offerId") or cand.get("id") or "")
            if oid and oid not in seen_offer_ids:
                seen_offer_ids.add(oid)
                collected_offers.append(cand)
    else:
        verify_and_patch_1688_cli(apply_patch=True)
        kw_list = [k.strip() for k in (keywords or []) if k.strip()]
        if not kw_list:
            raise ValueError("Provide at least one --keyword or --input JSON path.")
        for kw in kw_list:
            for sort_mode in ("best-selling", "relevance"):
                cmd_args = ["search", kw, "--sort", sort_mode, "--exclude-ads", "--max", str(max_per_keyword), "--json"]
                if price_max_cny is not None:
                    cmd_args.extend(["--price-max", f"{price_max_cny:g}"])
                if factory_only:
                    cmd_args.extend(["--verified", "factory"])
                res = run_1688_command(cmd_args, output_path=None, auto_login=True)
                data = res.get("data") if isinstance(res.get("data"), dict) else {}
                for cand in data.get("offers") or []:
                    if not isinstance(cand, dict):
                        continue
                    oid = str(cand.get("offerId") or "")
                    if oid and oid not in seen_offer_ids:
                        seen_offer_ids.add(oid)
                        collected_offers.append(cand)

    report = analyze_1688_trends(
        offers=collected_offers,
        keyword=kw_label,
        mode=mode,
        target_qty=target_qty,
        state_file_path=state_file_path,
        top_limit=top_limit,
    )
    if output_md_path:
        md_text = format_trends_markdown(report)
        out_md = Path(output_md_path)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_md.write_text(md_text, encoding="utf-8")
        report["markdown_report"] = str(out_md)
    if output_json_path:
        _atomic_write_json(Path(output_json_path), report)
        report["json_report"] = str(output_json_path)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="china_sourcing.py",
        description="Unified multi-agent CLI for sourcing products across 1688, Taobao, Alibaba, Pinduoduo, and Douyin.",
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    p_doc = sub.add_parser("doctor", help="Check installed tools, sessions, and API credentials.")
    p_doc.add_argument("--output", help="Optional path to write JSON doctor report.")
    p_doc.add_argument("--fix", action="store_true", help="Apply vendored 1688-cli patches if missing or outdated.")

    p_link = sub.add_parser("parse-link", help="Extract platform, URL, and item ID from mobile share text.")
    p_link.add_argument("text", help="Share text or URL from Taobao, 1688, Pinduoduo, Douyin, or Alibaba.")
    p_link.add_argument(
        "--resolve",
        action="store_true",
        help="Follow HTTP redirects on mobile short links (e.tb.cn, v.douyin.com, qr.1688.com) to extract item_id.",
    )

    p_ali = sub.add_parser("alibaba", help="Build structured Alibaba.com B2B verified manufacturer search metadata.")
    p_ali.add_argument("--query", "-q", required=True, help="English product keyword for Alibaba.com.")
    p_ali.add_argument("--limit", type=int, default=10, help="Target supplier count.")
    p_ali.add_argument("--output", help="Optional path to write JSON output.")

    p_kw = sub.add_parser("translate-keywords", help="Build cross-platform search URLs and CLI commands.")
    p_kw.add_argument("--product", required=True, help="Product name in Vietnamese or English.")
    p_kw.add_argument("--zh", nargs="+", required=True, help="One or more Simplified Chinese sourcing keywords.")
    p_kw.add_argument("--en", help="Optional English keyword for Alibaba.com.")
    p_kw.add_argument("--max-price-cny", type=float, help="Optional maximum EXW price in CNY.")
    p_kw.add_argument("--output", help="Optional path to save JSON keyword matrix.")

    p_cost = sub.add_parser("landed-cost", help="Calculate estimated landed cost to Vietnam in VND.")
    p_cost.add_argument("--price-cny", type=float, required=True, help="EXW unit price in CNY.")
    p_cost.add_argument("--qty", type=int, default=50, help="Order quantity.")
    p_cost.add_argument("--weight-kg", type=float, default=0.25, help="Unit weight in kg including packaging.")
    p_cost.add_argument("--volume-cbm", type=float, default=0.002, help="Unit volume in m3 including packaging.")
    p_cost.add_argument("--exchange-rate", type=float, default=DEFAULT_EXCHANGE_RATE_VND)
    p_cost.add_argument("--vn-shipping-per-kg", type=float, default=DEFAULT_VN_SHIPPING_PER_KG_VND)
    p_cost.add_argument("--cn-domestic-cny", type=float, default=DEFAULT_CN_DOMESTIC_SHIPPING_CNY)

    p_login = sub.add_parser(
        "login",
        help="Automatically launch a real browser window for the user to log in (no user CLI needed).",
    )
    p_login.add_argument(
        "--platform",
        default="1688",
        choices=["1688", "taobao", "tmall", "pinduoduo", "douyin", "alibaba"],
        help="Target platform to open browser login for.",
    )
    p_login.add_argument("--profile", default="default", help="1688 profile name.")
    p_login.add_argument("--timeout", type=int, default=300, help="Seconds to wait for login.")
    p_login.add_argument("--force", action="store_true", help="Force re-login.")

    p_open = sub.add_parser("open-browser", help="Automatically open a browser window to a platform or URL.")
    p_open.add_argument("--platform", default="1688", help="Platform key.")
    p_open.add_argument("--url", help="Explicit URL to open.")

    p_1688 = sub.add_parser("1688", help="Execute 1688-cli command (auto-launches browser login if needed).")
    p_1688.add_argument("--output", help="Path to write JSON output artifact.")
    p_1688.add_argument("--no-auto-login", action="store_true", help="Disable automatic browser login popup.")
    p_1688.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed directly to 1688-cli.")

    p_trends = sub.add_parser(
        "trends",
        help="Scan 1688 for hot new products (上新), fast-rising sales velocity (飙升), and emerging niche trends (商机组货 / 排行榜).",
    )
    p_trends.add_argument(
        "--keyword",
        "-k",
        nargs="+",
        help="One or more Simplified Chinese keywords to scan on 1688.",
    )
    p_trends.add_argument(
        "--input",
        help="Optional path to existing 1688 search JSON file (offline/replay mode).",
    )
    p_trends.add_argument(
        "--mode",
        default="all",
        choices=["all", "new-hot", "fast-rising", "niche-trends"],
        help="Filter report focus: all, new-hot (上新), fast-rising (飙升), or niche-trends (商机组货/排行榜).",
    )
    p_trends.add_argument("--max", type=int, default=40, help="Max offers per search pass (default: 40).")
    p_trends.add_argument("--top", type=int, default=10, help="Number of top offers per table (default: 10).")
    p_trends.add_argument("--qty", type=int, default=100, help="Target batch quantity for Vietnam Landed Cost.")
    p_trends.add_argument("--price-max", type=float, help="Optional maximum unit price in CNY.")
    p_trends.add_argument("--factory-only", action="store_true", help="Restrict scan to verified factories (生产厂家).")
    p_trends.add_argument(
        "--state-file",
        help="Optional path to trends_state.json to track delta orders/day across time intervals.",
    )
    p_trends.add_argument("--output-json", help="Optional path to write structured JSON trend report.")
    p_trends.add_argument("--output-md", help="Optional path to write Vietnamese Markdown trend report.")

    p_rep = sub.add_parser("report", help="Generate Markdown/CSV comparison report and WangWang inquiry draft.")
    p_rep.add_argument("--input", required=True, help="Path to JSON file containing offers.")
    p_rep.add_argument("--output-md", required=True, help="Path to output Markdown report.")
    p_rep.add_argument("--output-csv", help="Optional path to output CSV file.")
    p_rep.add_argument("--output-wangwang", help="Optional path to output WangWang draft Markdown.")
    p_rep.add_argument("--qty", type=int, default=50, help="Target batch quantity for landed cost calculation.")
    p_rep.add_argument("--exchange-rate", type=float, default=DEFAULT_EXCHANGE_RATE_VND)
    p_rep.add_argument("--vn-shipping-per-kg", type=float, default=DEFAULT_VN_SHIPPING_PER_KG_VND)

    p_inq = sub.add_parser(
        "inquire-wangwang",
        help="Send a 1688 WangWang inquiry with SHA-256 idempotency gate and screenshot proof capture.",
    )
    p_inq.add_argument("--offer-id", "--offer", dest="offer_id", required=True, help="1688 offer ID.")
    p_inq.add_argument("--message", "-m", required=True, help="Chinese inquiry message to send.")
    p_inq.add_argument("--run-id", default="default", help="Run identifier for idempotency hashing.")
    p_inq.add_argument("--seller", help="Optional seller loginId or shop name.")
    p_inq.add_argument("--supplier", help="Optional supplier display name.")
    p_inq.add_argument("--rank", type=int, default=1, help="Supplier rank in sourcing report.")
    p_inq.add_argument("--receipt", help="Path to 07_inquiry_receipt.json for idempotency check and logging.")
    p_inq.add_argument("--screenshot", help="Path to save PNG proof via BB1688_SCREENSHOT_PATH.")
    p_inq.add_argument("--force", action="store_true", help="Bypass idempotency check and re-send.")

    p_ww = sub.add_parser(
        "check-wangwang",
        help="Check 1688 WangWang replies for contacted suppliers (used by the 5-minute auto-polling schedule).",
    )
    p_ww.add_argument("--receipt", help="Path to 07_inquiry_receipt.json containing contacted sellers.")
    p_ww.add_argument("--seller", help="Single seller loginId to check.")
    p_ww.add_argument("--offer", help="Offer ID to scope the WangWang check.")
    p_ww.add_argument("--limit", type=int, default=20, help="Max messages per conversation.")
    p_ww.add_argument("--state-file", help="Optional path to 08_wangwang_state.json for delta message tracking.")
    p_ww.add_argument("--only-new", action="store_true", help="Only return unseen human replies in seller_replies.")
    p_ww.add_argument("--output", help="Optional path to write JSON poll report.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)

    if ns.subcommand == "doctor":
        res = run_doctor(ns.output, fix=ns.fix)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    if ns.subcommand == "parse-link":
        res = parse_share_link(ns.text, resolve_redirects=ns.resolve)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    if ns.subcommand == "alibaba":
        res = run_alibaba_search(query=ns.query, max_results=ns.limit, output_path=ns.output)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    if ns.subcommand == "translate-keywords":
        res = build_search_matrix(
            product_name=ns.product,
            chinese_keywords=ns.zh,
            english_keyword=ns.en,
            max_price_cny=ns.max_price_cny,
        )
        if ns.output:
            write_json(Path(ns.output), res)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    if ns.subcommand == "landed-cost":
        res = calculate_landed_cost(
            exw_price_cny=ns.price_cny,
            quantity=ns.qty,
            weight_kg_per_unit=ns.weight_kg,
            volume_cbm_per_unit=ns.volume_cbm,
            exchange_rate_vnd=ns.exchange_rate,
            vn_shipping_per_kg_vnd=ns.vn_shipping_per_kg,
            cn_domestic_total_cny=ns.cn_domestic_cny,
        )
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    if ns.subcommand == "login":
        if ns.platform == "1688":
            res = ensure_1688_browser_login(
                profile=ns.profile,
                timeout_sec=ns.timeout,
                force=ns.force,
            )
        else:
            res = open_platform_browser(platform=ns.platform)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res.get("ok") else 1

    if ns.subcommand == "open-browser":
        res = open_platform_browser(platform=ns.platform, url=ns.url)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res.get("ok") else 1

    if ns.subcommand == "1688":
        clean_args = [a for a in ns.args if a != "--"]
        res = run_1688_command(clean_args, ns.output, auto_login=not ns.no_auto_login)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res.get("ok") else 1

    if ns.subcommand == "trends":
        res = run_1688_trends(
            keywords=ns.keyword,
            input_json_path=ns.input,
            mode=ns.mode,
            max_per_keyword=ns.max,
            target_qty=ns.qty,
            price_max_cny=ns.price_max,
            factory_only=ns.factory_only,
            state_file_path=ns.state_file,
            output_json_path=ns.output_json,
            output_md_path=ns.output_md,
            top_limit=ns.top,
        )
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res.get("ok") else 1

    if ns.subcommand == "report":
        res = generate_sourcing_report(
            offers_json_path=ns.input,
            output_md_path=ns.output_md,
            output_csv_path=ns.output_csv,
            output_wangwang_path=ns.output_wangwang,
            exchange_rate_vnd=ns.exchange_rate,
            vn_shipping_per_kg_vnd=ns.vn_shipping_per_kg,
            target_qty=ns.qty,
        )
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    if ns.subcommand == "inquire-wangwang":
        res = inquire_wangwang(
            offer_id=ns.offer_id,
            message=ns.message,
            run_id=ns.run_id,
            seller_login_id=ns.seller,
            supplier=ns.supplier,
            rank=ns.rank,
            receipt_json_path=ns.receipt,
            screenshot_path=ns.screenshot,
            force=ns.force,
        )
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res.get("ok") else 1

    if ns.subcommand == "check-wangwang":
        res = check_wangwang_replies(
            receipt_json_path=ns.receipt,
            seller_login_id=ns.seller,
            offer_id=ns.offer,
            limit=ns.limit,
            output_path=ns.output,
            state_file_path=ns.state_file,
            only_new=ns.only_new,
        )
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
