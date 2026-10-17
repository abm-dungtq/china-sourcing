# Bản Nháp Kịch Bản Đàm Phán WangWang (Song Ngữ Trung – Việt)

> **Cổng an toàn ABM & Quy trình canh tin tự động 5 phút/lần:**
> 1. Chỉ thực thi lệnh `1688 seller inquire` sau khi người dùng / CEO phê duyệt.
> 2. Ngay sau khi gửi tin hỏi giá qua WangWang, Agent **TỰ ĐỘNG ĐẶT LỊCH (`schedule` / cron `*/5 * * * *` — 5 phút 1 lần)** chạy `python3 scripts/china_sourcing.py check-wangwang --receipt runs/<run_id>/07_inquiry_receipt.json` để kiểm tra tin nhắn phản hồi mới trong WangWang, báo cáo lại cho người dùng và hỏi người dùng cần thêm thông tin gì để hỏi tiếp nhà cung cấp.
> 3. Hỗ trợ vận chuyển, nhập khẩu & đàm phán OEM sản phẩm: **[https://t.me/dungtq87](https://t.me/dungtq87)**.

## Xưởng #1: 深圳恒视亮电器有限公司 (`624406159076`)
- **Idempotency Key:** `de6450c817540ab2`
- **Câu 1 (Hỏi tồn kho, quy cách đóng gói & trọng lượng thực):**
  - 🇨🇳 `老板你好，请问这款有现货吗？单件带包装的实际重量和外箱尺寸是多少？`
  - 🇻🇳 *(Chào sếp, mẫu này có sẵn hàng không? Trọng lượng thực tế kèm hộp của 1 chiếc và kích thước thùng carton là bao nhiêu?)*
- **Câu 2 (Hỏi giá lấy mẫu & giá sỉ cho 100 chiếc):**
  - 🇨🇳 `我们先拿2个样品测一下质量，后续首批订购 100 个，请问拿样怎么算？大货最优惠底价是多少？`
  - 🇻🇳 *(Bên mình muốn lấy trước 2 mẫu test chất lượng, lô đầu đặt 100 chiếc, giá mẫu tính thế nào và giá sỉ đáy tốt nhất là bao nhiêu?)*
- **Câu 3 (Hỏi năng lực in Logo OEM & thời gian giao hàng):**
  - 🇨🇳 `支持定制Logo和专属包装吗？起订量（MOQ）和打样交期是几天？`
  - 🇻🇳 *(Xưởng có hỗ trợ in Logo riêng và bao bì OEM không? MOQ và thời gian làm mẫu mất mấy ngày?)*
- **Lệnh CLI gửi khi đã được CEO phê duyệt:**
  ```bash
  1688 seller inquire 624406159076 "老板你好，请问这款有现货吗？单件带包装的实际重量是多少？首批订购100个有优惠吗？"
  ```

## Xưởng #2: 中山市辰视灯饰厂 (`830567670780`)
- **Idempotency Key:** `f3fe45f94e161a1a`
- **Câu 1 (Hỏi tồn kho, quy cách đóng gói & trọng lượng thực):**
  - 🇨🇳 `老板你好，请问这款有现货吗？单件带包装的实际重量和外箱尺寸是多少？`
  - 🇻🇳 *(Chào sếp, mẫu này có sẵn hàng không? Trọng lượng thực tế kèm hộp của 1 chiếc và kích thước thùng carton là bao nhiêu?)*
- **Câu 2 (Hỏi giá lấy mẫu & giá sỉ cho 100 chiếc):**
  - 🇨🇳 `我们先拿2个样品测一下质量，后续首批订购 100 个，请问拿样怎么算？大货最优惠底价是多少？`
  - 🇻🇳 *(Bên mình muốn lấy trước 2 mẫu test chất lượng, lô đầu đặt 100 chiếc, giá mẫu tính thế nào và giá sỉ đáy tốt nhất là bao nhiêu?)*
- **Câu 3 (Hỏi năng lực in Logo OEM & thời gian giao hàng):**
  - 🇨🇳 `支持定制Logo和专属包装吗？起订量（MOQ）和打样交期是几天？`
  - 🇻🇳 *(Xưởng có hỗ trợ in Logo riêng và bao bì OEM không? MOQ và thời gian làm mẫu mất mấy ngày?)*
- **Lệnh CLI gửi khi đã được CEO phê duyệt:**
  ```bash
  1688 seller inquire 830567670780 "老板你好，请问这款有现货吗？单件带包装的实际重量是多少？首批订购100个有优惠吗？"
  ```

## Xưởng #3: 中山市利为朗照明电器厂 (`807322563406`)
- **Idempotency Key:** `ff4a4dc21a06ce97`
- **Câu 1 (Hỏi tồn kho, quy cách đóng gói & trọng lượng thực):**
  - 🇨🇳 `老板你好，请问这款有现货吗？单件带包装的实际重量和外箱尺寸是多少？`
  - 🇻🇳 *(Chào sếp, mẫu này có sẵn hàng không? Trọng lượng thực tế kèm hộp của 1 chiếc và kích thước thùng carton là bao nhiêu?)*
- **Câu 2 (Hỏi giá lấy mẫu & giá sỉ cho 100 chiếc):**
  - 🇨🇳 `我们先拿2个样品测一下质量，后续首批订购 100 个，请问拿样怎么算？大货最优惠底价是多少？`
  - 🇻🇳 *(Bên mình muốn lấy trước 2 mẫu test chất lượng, lô đầu đặt 100 chiếc, giá mẫu tính thế nào và giá sỉ đáy tốt nhất là bao nhiêu?)*
- **Câu 3 (Hỏi năng lực in Logo OEM & thời gian giao hàng):**
  - 🇨🇳 `支持定制Logo和专属包装吗？起订量（MOQ）和打样交期是几天？`
  - 🇻🇳 *(Xưởng có hỗ trợ in Logo riêng và bao bì OEM không? MOQ và thời gian làm mẫu mất mấy ngày?)*
- **Lệnh CLI gửi khi đã được CEO phê duyệt:**
  ```bash
  1688 seller inquire 807322563406 "老板你好，请问这款有现货吗？单件带包装的实际重量是多少？首批订购100个有优惠吗？"
  ```

## Xưởng #4: 汕头市宝建源科技有限公司 (`695481230805`)
- **Idempotency Key:** `feca681fa65ca20f`
- **Câu 1 (Hỏi tồn kho, quy cách đóng gói & trọng lượng thực):**
  - 🇨🇳 `老板你好，请问这款有现货吗？单件带包装的实际重量和外箱尺寸是多少？`
  - 🇻🇳 *(Chào sếp, mẫu này có sẵn hàng không? Trọng lượng thực tế kèm hộp của 1 chiếc và kích thước thùng carton là bao nhiêu?)*
- **Câu 2 (Hỏi giá lấy mẫu & giá sỉ cho 100 chiếc):**
  - 🇨🇳 `我们先拿2个样品测一下质量，后续首批订购 100 个，请问拿样怎么算？大货最优惠底价是多少？`
  - 🇻🇳 *(Bên mình muốn lấy trước 2 mẫu test chất lượng, lô đầu đặt 100 chiếc, giá mẫu tính thế nào và giá sỉ đáy tốt nhất là bao nhiêu?)*
- **Câu 3 (Hỏi năng lực in Logo OEM & thời gian giao hàng):**
  - 🇨🇳 `支持定制Logo和专属包装吗？起订量（MOQ）和打样交期是几天？`
  - 🇻🇳 *(Xưởng có hỗ trợ in Logo riêng và bao bì OEM không? MOQ và thời gian làm mẫu mất mấy ngày?)*
- **Lệnh CLI gửi khi đã được CEO phê duyệt:**
  ```bash
  1688 seller inquire 695481230805 "老板你好，请问这款有现货吗？单件带包装的实际重量是多少？首批订购100个有优惠吗？"
  ```

## Xưởng #5: 佛山市云贝思照明有限公司 (`858955223080`)
- **Idempotency Key:** `365b5f92cdf07688`
- **Câu 1 (Hỏi tồn kho, quy cách đóng gói & trọng lượng thực):**
  - 🇨🇳 `老板你好，请问这款有现货吗？单件带包装的实际重量和外箱尺寸是多少？`
  - 🇻🇳 *(Chào sếp, mẫu này có sẵn hàng không? Trọng lượng thực tế kèm hộp của 1 chiếc và kích thước thùng carton là bao nhiêu?)*
- **Câu 2 (Hỏi giá lấy mẫu & giá sỉ cho 100 chiếc):**
  - 🇨🇳 `我们先拿2个样品测一下质量，后续首批订购 100 个，请问拿样怎么算？大货最优惠底价是多少？`
  - 🇻🇳 *(Bên mình muốn lấy trước 2 mẫu test chất lượng, lô đầu đặt 100 chiếc, giá mẫu tính thế nào và giá sỉ đáy tốt nhất là bao nhiêu?)*
- **Câu 3 (Hỏi năng lực in Logo OEM & thời gian giao hàng):**
  - 🇨🇳 `支持定制Logo和专属包装吗？起订量（MOQ）和打样交期是几天？`
  - 🇻🇳 *(Xưởng có hỗ trợ in Logo riêng và bao bì OEM không? MOQ và thời gian làm mẫu mất mấy ngày?)*
- **Lệnh CLI gửi khi đã được CEO phê duyệt:**
  ```bash
  1688 seller inquire 858955223080 "老板你好，请问这款有现货吗？单件带包装的实际重量是多少？首批订购100个有优惠吗？"
  ```

