import json
import tempfile
import unittest
from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
