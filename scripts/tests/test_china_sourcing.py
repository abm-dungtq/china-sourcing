import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys

SCRIPT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

import china_sourcing as cs  # noqa: E402


class TestChinaSourcing(unittest.TestCase):
    def test_parse_taobao_share_text(self) -> None:
        share = "【淘宝】假一赔四 https://e.tb.cn/h.StvCjJlWxkNatsx?tk=abc MF937 「UBV美式休闲卫衣」"
        res = cs.parse_share_link(share)
        self.assertEqual(res["platform"], "taobao")
        self.assertEqual(res["url"], "https://e.tb.cn/h.StvCjJlWxkNatsx?tk=abc")
        self.assertEqual(res["extracted_title"], "UBV美式休闲卫衣")

    def test_parse_1688_offer_url(self) -> None:
        url = "https://detail.1688.com/offer/628196518518.html?spm=a2615"
        res = cs.parse_share_link(url)
        self.assertEqual(res["platform"], "1688")
        self.assertEqual(res["item_id"], "628196518518")

    def test_parse_pinduoduo_url(self) -> None:
        url = "https://mobile.yangkeduo.com/goods.html?goods_id=481920394812"
        res = cs.parse_share_link(url)
        self.assertEqual(res["platform"], "pinduoduo")
        self.assertEqual(res["item_id"], "481920394812")

    def test_parse_douyin_video(self) -> None:
        url = "https://www.douyin.com/video/7600361826030865707"
        res = cs.parse_share_link(url)
        self.assertEqual(res["platform"], "douyin")
        self.assertEqual(res["item_id"], "7600361826030865707")

    def test_build_search_matrix(self) -> None:
        matrix = cs.build_search_matrix(
            product_name="Sạc dự phòng từ tính",
            chinese_keywords=["磁吸充电宝", "无线快充移动电源"],
            english_keyword="magnetic power bank",
            max_price_cny=45,
        )
        self.assertEqual(len(matrix["keywords"]), 2)
        self.assertIn("--price-max 45", matrix["keywords"][0]["1688_cli_search"])
        self.assertIn("alibaba.com/trade/search", matrix["alibaba_search_url"])

    def test_calculate_landed_cost(self) -> None:
        cost = cs.calculate_landed_cost(
            exw_price_cny=20.0,
            quantity=100,
            weight_kg_per_unit=0.3,
            cn_domestic_total_cny=10.0,
        )
        # Defaults: 4000 VND/CNY, 30000 VND/kg TMDT
        # 20*4000 (80000) + 0.1*4000 (400) + 0.3*30000 (9000) = 89400
        self.assertEqual(cost["exchange_rate_vnd"], 4000.0)
        self.assertEqual(cost["unit_landed_cost_vnd"], 89400)
        self.assertEqual(cost["total_batch_landed_cost_vnd"], 8940000)
        self.assertEqual(cost["official_import_over_1cbm"]["rate_per_cbm_vnd"], 1600000)
        self.assertEqual(cost["official_import_over_1cbm"]["rate_per_kg_vnd"], 6000)
        self.assertEqual(cost["support_contact"], "https://t.me/dungtq87")

    def test_generate_sourcing_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            offers_file = tmp / "offers.json"
            offers_file.write_text(
                json.dumps(
                    {
                        "offers": [
                            {
                                "offerId": "628196518518",
                                "platform": "1688",
                                "title": "磁吸无线充电宝 10000mAh 源头厂家",
                                "supplierName": "深圳市源头电子科技有限公司",
                                "price": 25.5,
                                "moq": 50,
                                "weight_kg": 0.22,
                                "repurchaseRate": "32%",
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            md_out = tmp / "report.md"
            csv_out = tmp / "report.csv"
            ww_out = tmp / "wangwang.md"

            res = cs.generate_sourcing_report(
                offers_json_path=str(offers_file),
                output_md_path=str(md_out),
                output_csv_path=str(csv_out),
                output_wangwang_path=str(ww_out),
                target_qty=50,
            )
            self.assertTrue(res["ok"])
            self.assertEqual(res["rows_count"], 1)
            md_text = md_out.read_text(encoding="utf-8")
            self.assertIn("深圳市源头电子科技有限公司", md_text)
            self.assertIn("https://t.me/dungtq87", md_text)
            self.assertIn("1,600,000 VNĐ / 1 m³", md_text)
            self.assertIn("628196518518", ww_out.read_text(encoding="utf-8"))

    def test_build_onboarding_guide(self) -> None:
        guide = cs.build_onboarding_guide({"nick": "tdhwhosales", "memberId": "3609685251"})
        self.assertEqual(guide["confirmed_account"]["nick"], "tdhwhosales")
        self.assertEqual(guide["confirmed_account"]["memberId"], "3609685251")
        self.assertEqual(guide["support_contact"], "https://t.me/dungtq87")
        self.assertEqual(len(guide["scenarios"]), 5)
        self.assertIn("tdhwhosales", guide["markdown_guide"])
        self.assertIn("https://t.me/dungtq87", guide["markdown_guide"])

    def test_report_uses_price_tiers_for_target_qty(self) -> None:
        item = {
            "price": 35.0,
            "priceTiers": [
                {"minQty": 2, "price": 35.0},
                {"minQty": 50, "price": 29.0},
                {"minQty": 200, "price": 24.5},
            ],
        }
        self.assertEqual(cs.resolve_tier_price_cny(item, target_qty=1), 35.0)
        self.assertEqual(cs.resolve_tier_price_cny(item, target_qty=10), 35.0)
        self.assertEqual(cs.resolve_tier_price_cny(item, target_qty=100), 29.0)
        self.assertEqual(cs.resolve_tier_price_cny(item, target_qty=500), 24.5)

        # Multi-SKU offer where all tiers have minQty==1 should preserve base priceMin
        multi_sku = {
            "priceMin": 11.7,
            "priceTiers": [
                {"minQty": 1, "price": 9.7},
                {"minQty": 1, "price": 19.8},
            ],
        }
        self.assertEqual(cs.resolve_tier_price_cny(multi_sku, target_qty=100), 11.7)

    def test_report_converts_cm3_volume_to_cbm(self) -> None:
        item = {
            "packageInfo": [
                {
                    "length": 40,
                    "width": 30,
                    "height": 20,
                    "weight": 850,
                    "volume": 24000,
                }
            ]
        }
        metrics = cs.extract_package_metrics(item)
        self.assertAlmostEqual(metrics["volume_cbm"], 0.024, places=6)
        self.assertAlmostEqual(metrics["weight_kg"], 0.85, places=6)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            offers_file = tmp / "bulky.json"
            offers_file.write_text(
                json.dumps(
                    {
                        "offers": [
                            {
                                "offerId": "999888777666",
                                "title": "大号收纳箱",
                                "supplierName": "义乌塑料制品厂",
                                "price": 10.0,
                                "packageInfo": [{"length": 50, "width": 40, "height": 30, "weight": 500, "volume": 60000}],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            md_out = tmp / "bulky.md"
            cs.generate_sourcing_report(str(offers_file), str(md_out), target_qty=100)
            md_text = md_out.read_text(encoding="utf-8")
            # 0.06 m3 * 1,600,000 VND/m3 = 96,000 VND freight + 40,000 EXW + 240 CN ship (6 CNY / 100) = 136,240 VND
            self.assertIn("136,240 VNĐ", md_text)
            self.assertNotIn("43,440 VNĐ", md_text)

    def test_small_gram_weight_not_inflated_to_kg(self) -> None:
        item = {
            "packageInfo": [
                {
                    "length": 10,
                    "width": 5,
                    "height": 5,
                    "weight": 5,
                    "volume": 250,
                }
            ]
        }
        metrics = cs.extract_package_metrics(item)
        self.assertEqual(metrics["weight_kg"], 0.005)
        self.assertEqual(metrics["weight_unit_inferred"], "g->kg")

    def test_volumetric_weight_disambiguation(self) -> None:
        # Zero volume should not divide sub-1.0 explicit kg weights by 1000
        item_sub1 = {"packageInfo": [{"length": 0, "width": 0, "height": 0, "weight": 0.35}]}
        m1 = cs.extract_package_metrics(item_sub1)
        self.assertEqual(m1["weight_kg"], 0.35)
        self.assertEqual(m1["weight_unit_inferred"], "sub1_kg")

        # String suffix "8g" -> 0.008 kg
        item_str = {"packageInfo": [{"weight": "8g"}]}
        m2 = cs.extract_package_metrics(item_str)
        self.assertEqual(m2["weight_kg"], 0.008)
        self.assertEqual(m2["weight_unit_inferred"], "g_suffix->kg")

    def test_check_wangwang_filters_autoreply_and_cards(self) -> None:
        sample_msgs = [
            {"sender": "恒悦亮电器厂", "content": "[卡片消息]", "isMine": False, "kind": "other"},
            {
                "sender": "恒悦亮电器厂",
                "content": "老板你好，请问这款有现货吗？",
                "isMine": True,
                "kind": "text",
            },
            {
                "sender": "恒悦亮电器厂",
                "content": "亲，客服现在比较繁忙，稍等一会马上来回复你哦~",
                "isMine": False,
                "kind": "autoReply",
            },
            {
                "sender": "恒悦亮电器厂",
                "content": "商家长时间没有回复，平台已通知商家尽快安排专人处理",
                "isMine": False,
                "kind": "text",
            },
            {
                "sender": "恒悦亮电器厂",
                "content": "由于当前是节假日期间，卖家可能无法马上回复您的消息",
                "isMine": False,
                "kind": "autoReply",
            },
            {"sender": "视力童", "content": "有货的", "isMine": False, "kind": "text"},
        ]
        human = [m["content"] for m in sample_msgs if cs.is_human_seller_reply(m)]
        self.assertEqual(human, ["有货的"])

    def test_check_wangwang_stateful_delta_only(self) -> None:
        mock_convs = [
            {
                "rank": 1,
                "offer_id": "622316377581",
                "supplier": "视力童",
                "seller_login_id": "视力童",
                "all_messages": [
                    {"sender": "视力童", "content": "单色logo", "isMine": False, "kind": "text", "id": "m1"},
                    {"sender": "视力童", "content": "可以", "isMine": False, "kind": "text", "id": "m2"},
                ],
            }
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "08_wangwang_state.json"
            first_poll = cs.check_wangwang_replies(
                state_file_path=str(state_file),
                only_new=True,
                mock_conversations=mock_convs,
            )
            self.assertTrue(first_poll["has_new_human_replies"])
            self.assertEqual(first_poll["total_new_human_replies"], 2)
            self.assertEqual(len(first_poll["conversations"][0]["seller_replies"]), 2)

            # Second poll with identical messages should yield 0 new replies
            second_poll = cs.check_wangwang_replies(
                state_file_path=str(state_file),
                only_new=True,
                mock_conversations=mock_convs,
            )
            self.assertFalse(second_poll["has_new_human_replies"])
            self.assertEqual(second_poll["total_new_human_replies"], 0)
            self.assertEqual(len(second_poll["conversations"][0]["seller_replies"]), 0)
            self.assertEqual(second_poll["conversations"][0]["human_replies_count"], 2)

    def test_inquire_wangwang_idempotency_blocks_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            receipt_file = Path(tmpdir) / "07_inquiry_receipt.json"
            offer_id = "648543252855"
            msg = "老板你好，请问这款有现货吗？"
            key = cs.compute_inquiry_idempotency_key("run-001", offer_id, msg)
            receipt_file.write_text(
                json.dumps(
                    {
                        "run_id": "run-001",
                        "receipts": [
                            {
                                "rank": 1,
                                "offer_id": offer_id,
                                "supplier": "深圳恒视亮",
                                "idempotency_key": key,
                                "ok": True,
                                "status": "sent",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            res = cs.inquire_wangwang(
                offer_id=offer_id,
                message=msg,
                run_id="run-001",
                receipt_json_path=str(receipt_file),
            )
            self.assertTrue(res["ok"])
            self.assertEqual(res["status"], "skipped_duplicate")
            self.assertTrue(res["skipped_duplicate"])
            self.assertEqual(res["idempotency_key"], key)

    def test_parse_short_link_redirect_resolution_mocked(self) -> None:
        share = "【淘宝】假一赔四 https://e.tb.cn/h.StvCjJlWxkNatsx?tk=abc MF937 「UBV美式休闲卫衣」"
        with patch.object(
            cs,
            "resolve_short_url",
            return_value=("https://item.taobao.com/item.htm?id=748291038471&spm=a21", None),
        ):
            res = cs.parse_share_link(share, resolve_redirects=True)
            self.assertEqual(res["platform"], "taobao")
            self.assertEqual(res["item_id"], "748291038471")
            self.assertEqual(
                res["resolved_url"],
                "https://item.taobao.com/item.htm?id=748291038471&spm=a21",
            )

    def test_doctor_detects_and_fixes_1688_cli_patch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_dist = Path(tmpdir) / "dist"
            fake_cmds = fake_dist / "commands"
            fake_cmds.mkdir(parents=True)
            for fname in ("seller-chat.js", "seller-inquire.js", "seller-messages.js"):
                (fake_cmds / fname).write_text("// unpatched upstream file\n", encoding="utf-8")

            check_before = cs.verify_and_patch_1688_cli(apply_patch=False, dist_dir=fake_dist)
            self.assertFalse(check_before["patched"])

            check_after = cs.verify_and_patch_1688_cli(apply_patch=True, dist_dir=fake_dist)
            self.assertTrue(check_after["patched"])
            self.assertEqual(len(check_after["applied_files"]), 3)

    def test_alibaba_subcommand_output(self) -> None:
        res = cs.run_alibaba_search(query="eye protection desk lamp", max_results=5)
        self.assertTrue(res["ok"])
        self.assertEqual(res["platform"], "alibaba")
        self.assertIn("SearchText=eye+protection+desk+lamp", res["search_url"])
        self.assertIn("verifiedManufactory=true", res["verified_manufacturer_url"])


if __name__ == "__main__":
    unittest.main()
