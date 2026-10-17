<div align="center">

# 🇨🇳 CHINA SOURCING SUITE (`china-sourcing` v2.1.0)

### Biến AI Agent thành giám đốc thu mua hàng Trung Quốc đa sàn 24/7
*(Quét trend hàng mới & tốc độ bán 1688 ➔ Lọc xưởng sản xuất gốc ➔ Tính chuẩn chi phí về tay bằng VNĐ ➔ Tự đàm phán WangWang & canh phản hồi 5 phút/lần)*

[![Version](https://img.shields.io/badge/Phi%C3%AAn%20b%E1%BA%A3n-v2.1.0-success.svg)](https://github.com/abm-dungtq/china-sourcing)
[![Tests](https://img.shields.io/badge/Ki%E1%BB%83m%20th%E1%BB%AD-24%2F24%20Pass-brightgreen.svg)](https://github.com/abm-dungtq/china-sourcing/blob/main/scripts/tests/test_china_sourcing.py)
[![License: MIT](https://img.shields.io/badge/Gi%E1%BA%A5y%20ph%C3%A9p-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platforms](https://img.shields.io/badge/S%C3%A0n-1688%20%E2%80%A2%20Taobao%20%E2%80%A2%20Pinduoduo%20%E2%80%A2%20Douyin%20%E2%80%A2%20Alibaba-crimson)](https://github.com/abm-dungtq/china-sourcing)
[![Agents](https://img.shields.io/badge/AI%20Agents-Claude%20Code%20%E2%80%A2%20Antigravity%20%E2%80%A2%20Codex%20%E2%80%A2%20Cursor-blue)](https://github.com/abm-dungtq/china-sourcing)
[![Support](https://img.shields.io/badge/H%E1%BB%97%20tr%E1%BB%A3%20V%E1%BA%ADn%20chuy%E1%BB%83n%20%26%20OEM-Telegram%20%40dungtq87-2CA5E0?logo=telegram)](https://t.me/dungtq87)

*Bạn chỉ cần giao việc bằng tiếng Việt. AI tự dịch từ khóa chuyên ngành của xưởng, quét mặt hàng mới lên kệ đang tăng tốc đơn sỉ, bóc tách cân nặng kèm thể tích hộp thực tế, tính sẵn chi phí về Việt Nam và trực tiếp mở 1688 WangWang thương lượng với chủ nhà máy.*

---

[Vì sao cần cài ngay?](#vi-sao-can-cai) • [6 vũ khí săn hàng](#6-vu-khi) • [Radar bắt trend v2.1.0](#radar-bat-trend) • [Bằng chứng thực chiến](#bang-chung-thuc-chien) • [Cài đặt 1 chạm](#cai-dat) • [Câu lệnh mẫu](#cau-lenh-mau) • [Lệnh CLI](#lenh-cli) • [Biểu phí & OEM](#bieu-phi-oem)

---

</div>

<a id="vi-sao-can-cai"></a>
## 🔥 1. Chấm dứt cảnh "mò kim đáy bể" khi nhập hàng Trung Quốc

Phần lớn người kinh doanh khi tự tìm nguồn hàng Trung Quốc thường mất tiền oan ở bốn khâu. Họ dễ đặt nhầm shop thương mại đội lốt nhà máy trên 1688 với giá chênh từ 25% đến 40%, nhập phải mẫu đã bão hòa vì không nhìn thấy dữ liệu tăng trưởng đơn sỉ theo thời gian thực, ước lượng sai cân nặng hoặc thể tích đóng gói khiến tiền cước ăn mòn hết lãi và tốn hàng giờ dùng công cụ dịch máy ngô nghê để nhắn hỏi từng xưởng trên WangWang.

**`china-sourcing`** giải quyết trọn vẹn chuỗi vấn đề đó bằng cách tích hợp thẳng quy trình thu mua xuyên biên giới vào các AI Agent phổ biến nhất hiện nay (Claude Code, Google Antigravity, OpenAI Codex, Cursor, OpenCode). Bạn chỉ cần mô tả nhu cầu bằng tiếng Việt tự nhiên, toàn bộ thao tác kỹ thuật phức tạp ở hậu trường sẽ do hệ thống tự động thực thi và kiểm chứng.

|Cách làm thủ công truyền thống|Khi trang bị `china-sourcing v2.1.0` cho AI Agent|
|:---|:---|
|Dùng Google Dịch mò từ khóa cảm tính, kết quả trả về toàn đại lý bán buôn trung gian.|AI tự lập ma trận **từ khóa tiếng Trung chuyên ngành của xưởng** và bật bộ lọc cứng chỉ lấy **Nhà máy sản xuất (`生产厂家` / `超级工厂`)**.|
|Chỉ nhìn được tổng lượt bán tích lũy nhiều năm nên dễ ôm phải mẫu cũ đã qua thời kỳ đỉnh cao.|Radar **`trends`** bóc tách riêng **sản phẩm mới lên kệ (`上新`)**, chấm điểm **tốc độ bứt tốc đơn hàng 30 ngày (`飙升 VelocityIndex`)** và gom **cụm xu hướng ngách (`商机组货`)**.|
|Không rõ kích thước hộp hay bậc giá sỉ, hàng về đến biên giới mới ngã ngửa vì cước thể tích.|Tự động khớp **bậc giá theo số lượng đặt (`priceTiers`)**, đổi thể tích hộp $\text{cm}^3 \to \text{m}^3$, khử sai số đơn vị gram/kg và tính sẵn **chi phí nhập về Việt Nam (VNĐ)**.|
|Phải tự mở từng cửa sổ WangWang, dán câu hỏi lặp đi lặp lại và trực màn hình chờ xưởng phản hồi.|Tự động mở **1688 WangWang gửi tin hỏi giá** (có khóa chống gửi trùng `SHA-256`), **chụp ảnh màn hình chứng minh** rồi **cứ 5 phút quét hộp thư 1 lần** để lọc phản hồi của người thật.|

---

<a id="6-vu-khi"></a>
## ⚡ 2. Sáu vũ khí săn hàng xuyên biên giới trong một bộ kỹ năng

$$\mathbf{[1688\ Trend\ Radar]} \longrightarrow \mathbf{[Factory\ Filter]} \longrightarrow \mathbf{[Tier\ \&\ CBM\ Cost]} \longrightarrow \mathbf{[WangWang\ Auto\ Chat]} \longrightarrow \mathbf{[5\text{-}Min\ Delta\ Poll]}$$

Bộ kỹ năng kết nối trực tiếp 5 nền tảng thương mại điện tử lớn nhất Trung Quốc vào một luồng vận hành khép kín:

1. **Radar quét sản phẩm mới đang hot, lượt bán tăng nhanh & bắt trend ngách 1688 (`trends` - Mới trên `v2.1.0`):** Khai thác trực tiếp gói dữ liệu ẩn trong phiên đăng nhập 1688 để phát hiện mặt hàng vừa ra mắt có cải tiến kỹ thuật (`上新`), đo tốc độ tăng trưởng đơn sỉ 30 ngày (`VelocityIndex` + chênh lệch `Δ đơn/ngày`), gom nhóm chủ đề ngách (`1688 商机组货`) và trích xuất bộ 3 bảng xếp hạng chính thức (`热销榜`, `飙升榜`, `新品榜`).
2. **Lọc xưởng sản xuất tận gốc trên 1688 (`--factory-only`):** Loại bỏ các công ty thương mại mua đi bán lại. Hệ thống trích xuất đầy đủ khung giá EXW theo sản lượng, tỷ lệ khách quay lại mua (`回头率`), số năm hoạt động và thông số đóng gói của từng mã hàng.
3. **Tính toán chi phí nhập hàng chuẩn xác theo bậc giá và thể tích thực tế (`v2.0.0+`):** Tự động chọn đúng đơn giá EXW theo số lượng mục tiêu, quy đổi kích thước kiện hàng sang mét khối ($\text{m}^3$) và đối chiếu trọng lượng quy đổi để so sánh song song hai phương án vận chuyển TMĐT (`30.000đ/kg`) và Chính ngạch (`>1m³`).
4. **Đàm phán WangWang tự động kèm cơ chế chống gửi trùng và lọc tin nhắn rác:** Tự động gửi thẻ sản phẩm kèm câu hỏi ép giá mẫu, hỏi MOQ in Logo OEM trên **1688 WangWang (`旺旺`)**, chụp ảnh màn hình làm bằng chứng và chỉ báo cáo khi có phản hồi mới từ nhân viên thật (tự động loại bỏ tin nhắn tự động `autoReply` và thông báo hệ thống).
5. **Tìm nguồn hàng bằng hình ảnh và giải mã link rút gọn đa sàn:** Hỗ trợ tìm xưởng 1688 bằng ảnh sản phẩm có sẵn, đồng thời tự động lần theo liên kết chuyển hướng (`HTTP Redirect`) để bóc tách mã sản phẩm gốc từ các đoạn mã chia sẻ điện thoại trên Taobao (`e.tb.cn`), Pinduoduo, Tmall và Alibaba.
6. **Bóc kịch bản video bán hàng triệu view trên Douyin:** Tải video Douyin không dính logo mờ (watermark) và chuyển toàn bộ lời thoại bán hàng tiếng Trung thành văn bản để bạn phân tích luận điểm bán hàng (USP) khi triển khai nội dung trên TikTok hoặc Reels.

---

<a id="radar-bat-trend"></a>
## 📈 3. Điểm mới nổi bật trên `v2.1.0` - Radar bắt trend và tốc độ bán 1688

Khi bạn đã đăng nhập tài khoản 1688 thông qua trình duyệt của skill, lệnh `trends` kết hợp cùng bản vá tự động [`patches/1688-cli/search-mtop.js`](patches/1688-cli/search-mtop.js) sẽ mở khóa toàn bộ tầng dữ liệu xu hướng mà giao diện tìm kiếm cơ bản thường che khuất.

### Bốn tầng dữ liệu xu hướng được bóc tách tự động

- **Tín hiệu hàng mới lên kệ (`上新热销 / Hot New Arrivals`):** Nhận diện các mã hàng vừa đăng bán hoặc vừa nâng cấp tính năng (ví dụ nhãn `功能上新 三档调光无频闪`, `7天内新发`, `今年3月上新`) và chấm điểm `HotNewScore` trên thang từ 0 đến 100.
- **Chỉ số tốc độ bứt tốc đơn hàng (`飙升 / Log-Damped VelocityIndex`):** Kết hợp doanh số 30 ngày gần nhất với tổng sản lượng lũy kế theo hàm logarit giảm chấn:
  $$\text{VelocityIndex} = \log_{10}(\text{orders}_{30\text{d}} + 1) \times (0.5 + 0.5 \times \text{recency\_share})$$
  Công thức này giúp phát hiện ngay những mặt hàng đang bùng nổ đơn đặt sỉ trong tháng gần nhất mà không bị đánh lừa bởi các mẫu mới chỉ bán được vài chiếc (`5/5 = 100%`). Khi chạy định kỳ cùng tham số `--state-file`, hệ thống còn tính chính xác **tốc độ tăng đơn mỗi ngày (`Δ đơn/ngày`)** giữa hai lần quét.
- **Cụm xu hướng ngách đang lên (`1688 商机组货 / Emerging Niche Clusters`):** Gom nhóm các chủ đề ngách do hệ thống dữ liệu 1688 gắn nhãn kèm ngày phát hiện `topicDate`. Trong phiên quét thực tế mặt hàng đèn bàn (`护眼台灯`), hệ thống lập tức phát hiện các cụm ngách mới như `护眼学习阅读台灯` (`189.736` đơn/30 ngày), `灯宿舍床上用` (`280.421` đơn/30 ngày) và `全光谱护眼学习灯` để bạn đào sâu vào thị trường ngách ít cạnh tranh.
- **Bộ ba bảng xếp hạng chính thức (`1688 排行榜`):** Từ mỗi huy hiệu xếp hạng tìm được, skill tự động sinh đủ 3 đường dẫn trực tiếp gồm **Bảng bán chạy (`热销榜` - `rankType=1`)**, **Bảng tăng tốc (`飙升榜` - `rankType=2`)** và **Bảng hàng mới (`新品榜` - `rankType=3`)** kèm tỷ lệ khách mua lại (`回头率`).

---

<a id="bang-chung-thuc-chien"></a>
## 📸 4. Bằng chứng thực chiến tìm 5 xưởng đèn bàn chống cận và đàm phán WangWang

Chỉ với 2 câu lệnh tiếng Việt ngắn gọn trong khung chat:
- **Câu 1:** *"Tìm giúp tôi 5 xưởng sản xuất đèn bàn học chống cận trên 1688, giá tại xưởng dưới 35 tệ, tính chi phí về Việt Nam cho lô 100 chiếc."*
- **Câu 2:** *"Gửi tin hỏi giá đi, chụp ảnh chứng minh bạn đã hỏi."*

Trong chưa đầy 3 phút, `china-sourcing` đã lọc ra 5 nhà máy sản xuất trực tiếp tại Thâm Quyến, Trung Sơn, Phật Sơn và Sán Đầu. Hệ thống tính chi tiết chi phí nhập về Việt Nam cho lô 100 chiếc rồi trực tiếp mở **1688 WangWang** nhắn tin đàm phán với cả 5 chủ xưởng.

<div align="center">
  <img src="assets/wangwang-proof-demo.png" alt="Bằng chứng AI tự động gửi tin hỏi giá trên 1688 WangWang và nhận phản hồi từ chủ xưởng" width="92%" />
  <p><em>Ảnh chụp màn hình thực tế do AI tự động xuất ra sau khi gửi tin nhắn hỏi giá lô 100 chiếc và điều kiện in Logo OEM cho 5 xưởng trên 1688 WangWang.</em></p>
</div>

Ngay ở chu kỳ quét tự động 5 phút đầu tiên, hệ thống đã thu về phản hồi trực tiếp của các chủ xưởng và dịch sang tiếng Việt cho người dùng:
- **Xưởng #2 (`中山市辰视灯饰厂` - Giá EXW `¥16.50`, Giá về tay `81.240đ/chiếc`):** Chủ xưởng xác nhận *"In Logo 1 màu làm được luôn cho đơn 100 chiếc (`单色logo 可以`), hàng đang có sẵn trong kho (`有货的`)!"*
- **Xưởng #4 (`汕头市宝建源科技有限公司` - Giá EXW `¥17.96`):** Báo rõ *"In màu cần 1.000 chiếc, còn khắc Laser màu xám nhận làm ngay cho lô 100 chiếc (`镭雕需要排单`)."*
- **Xưởng #5 (`佛山市云贝思照明有限公司` - Giá EXW `¥11.90`, Giá về tay `67.340đ/chiếc`):** Xác nhận nhận đơn lấy 2 mẫu test và đặt 100 chiếc kèm in Logo (`可以的`).

---

<a id="cai-dat"></a>
## 🚀 5. Hướng dẫn cài đặt 1 chạm (Hỗ trợ mọi AI Agent)

### Cách 1 - Cài đặt tự động bằng 1 dòng lệnh (Khuyên dùng)
Mở Terminal và dán lệnh dưới đây. Script sẽ tự động đồng bộ `china-sourcing v2.1.0` vào **Claude Code, Google Antigravity, OpenAI Codex, Cursor, OpenCode**, cài đặt `1688-cli@0.1.47` + `douyin-mcp-server`, đồng thời chạy `doctor --fix` để nạp sẵn 4 bản vá mở rộng (`search-mtop.js`, `seller-chat.js`, `seller-inquire.js`, `seller-messages.js`).

```bash
curl -fsSL https://raw.githubusercontent.com/abm-dungtq/china-sourcing/main/scripts/install.sh | bash
```

### Cách 2 - Clone kho mã nguồn và cài đặt thủ công
Nếu bạn muốn lưu mã nguồn về máy để nghiên cứu hoặc tùy chỉnh thêm, hãy chạy 3 lệnh sau:

```bash
git clone https://github.com/abm-dungtq/china-sourcing.git
cd china-sourcing
bash scripts/install.sh
```

> 💡 **Trải nghiệm đăng nhập Zero-Terminal:** Sau khi cài xong, bạn **không cần** gõ bất kỳ lệnh đăng nhập nào trong Terminal. Khi bạn giao việc lần đầu trên 1688, AI Agent sẽ tự động bật cửa sổ trình duyệt Chrome thật trên màn hình để bạn quét mã QR (hoặc nhập mật khẩu/SMS), tự xác nhận khi bạn đăng nhập thành công và lưu phiên cố định tại `~/.1688/profiles/default` cho mọi lần sau.

---

<a id="cau-lenh-mau"></a>
## 💬 6. Sáu câu lệnh mẫu copy-chạy-ngay trong khung chat AI

Sau khi cài đặt, hãy mở khung chat của Claude Code, Antigravity, Codex hoặc Cursor và thử ngay một trong các câu lệnh dưới đây:

1. **Quét sản phẩm mới đang hot, lượt bán tăng nhanh & bắt trend ngách 1688 (`trends`):**
   ```text
   Quét giúp tôi các mẫu đèn bàn chống cận mới lên kệ đang hot, lượt bán tăng nhanh nhất trên 1688 và các cụm xu hướng ngách đang lên kèm chi phí nhập về Việt Nam cho lô 100 chiếc.
   ```
2. **Săn xưởng sản xuất gốc 1688 & lập bảng so sánh chi phí nhập sỉ:**
   ```text
   Tìm giúp tôi 5 xưởng sản xuất quạt cầm tay mini tích điện trên 1688, giá tại xưởng dưới 25 tệ, tính chi phí về tay tại Việt Nam cho lô 200 chiếc.
   ```
3. **Ủy quyền cho AI đi chat WangWang ép giá & canh tin 5 phút/lần:**
   ```text
   Gửi tin hỏi giá sỉ lô 200 chiếc, lấy 2 mẫu test và hỏi điều kiện in Logo OEM cho 5 xưởng trên qua WangWang, chụp ảnh màn hình chứng minh bạn đã hỏi.
   ```
4. **Tìm xưởng 1688 bằng hình ảnh sản phẩm có sẵn:**
   ```text
   Tìm các xưởng 1688 đang sản xuất mẫu sản phẩm giống hệt bức ảnh /đường/dẫn/anh-san-pham.jpg và so sánh 5 xưởng có tỷ lệ khách mua lại cao nhất.
   ```
5. **Dò giá sỉ 1688 từ link chia sẻ điện thoại Taobao / Pinduoduo:**
   ```text
   Giải mã link chia sẻ Taobao này, bóc tách thông số sản phẩm và tìm xem các xưởng gốc trên 1688 đang bỏ sỉ mặt hàng này giá bao nhiêu.
   ```
6. **Bóc tách kịch bản video bán hàng hot trend trên Douyin:**
   ```text
   Tải video Douyin không logo từ link này và trích xuất toàn bộ kịch bản lời thoại bán hàng để tôi phân tích USP làm video TikTok.
   ```

---

<a id="lenh-cli"></a>
## 🛠️ 7. Bảng tra cứu nhanh các lệnh CLI cho người dùng chuyên sâu

Bên cạnh việc ra lệnh bằng tiếng Việt trong khung chat, bạn có thể gọi trực tiếp CLI [`scripts/china_sourcing.py`](scripts/china_sourcing.py) (Python 3.9+ thuần chuẩn, không phụ thuộc thư viện ngoài) để tích hợp vào script tự động hóa riêng:

```bash
# 1. Kiểm tra sức khỏe hệ thống & tự động nạp 4 bản vá 1688-cli (kèm reload daemon)
python3 scripts/china_sourcing.py doctor --fix

# 2. Quét sản phẩm mới đang hot (new-hot), bán tăng nhanh (fast-rising) & trend ngách (niche-trends)
python3 scripts/china_sourcing.py trends \
  --keyword "护眼台灯" \
  --mode all \
  --max 20 \
  --qty 100 \
  --state-file runs/den-ban/09_trends_state.json \
  --output-json runs/den-ban/09_trends_report.json \
  --output-md runs/den-ban/09_trends_report.md

# 3. Xuất báo cáo so sánh nhà máy 1688 (tự động khớp bậc giá priceTiers & thể tích CBM)
python3 scripts/china_sourcing.py report \
  --offers-json runs/den-ban/03_raw_offers.json \
  --output-md runs/den-ban/04_sourcing_report.md \
  --output-csv runs/den-ban/05_landed_cost.csv \
  --output-wangwang runs/den-ban/06_wangwang_inquiries.md \
  --qty 100

# 4. Gửi tin hỏi giá WangWang có khóa chống gửi trùng (Idempotency SHA-256) & chụp ảnh bằng chứng
python3 scripts/china_sourcing.py inquire-wangwang \
  --offer-id 624406159076 \
  --message "老板你好，请问这款拿样2个多少钱？100个起订支持单色丝印Logo吗？" \
  --run-id run-20261017 \
  --screenshot runs/den-ban/07_proof_1.png \
  --receipt-json runs/den-ban/07_inquiry_receipt.json

# 5. Quét hộp thư WangWang (chỉ lấy phản hồi mới từ người thật, lọc bỏ auto-reply)
python3 scripts/china_sourcing.py check-wangwang \
  --state-file runs/den-ban/08_wangwang_state.json \
  --only-new

# 6. Chạy bộ 24 bài kiểm thử tự động (Unit Tests)
python3 -m unittest discover -s scripts/tests -v
```

> 📖 Xem hướng dẫn chi tiết từng bước tại file [`HUONG_DAN_SU_DUNG_CHINA_SOURCING.md`](HUONG_DAN_SU_DUNG_CHINA_SOURCING.md).

---

<a id="bieu-phi-oem"></a>
## 📦 8. Biểu phí vận chuyển Trung - Việt chuẩn & hỗ trợ nhập khẩu / OEM

Công cụ tính toán của `china-sourcing` được tích hợp sẵn biểu phí vận chuyển thực tế về Việt Nam. Nhờ đó, bạn ước tính được chính xác biên lợi nhuận ròng trên từng mặt hàng trước khi xuống tiền đặt cọc:

|Hạng mục|Đơn giá áp dụng trong Skill|Ghi chú chi tiết|
|:---|:---|:---|
|**Tỷ giá Nhân dân tệ (CNY)**|**`4.000đ / 1 CNY`**|Liên hệ **[https://t.me/dungtq87](https://t.me/dungtq87)** nếu cần hỗ trợ đổi tệ hoặc thanh toán hộ 1688/Taobao/Alipay.|
|**Hàng đi tuyến TMĐT**|**`30.000đ / 1 kg`**|Phù hợp đi hàng mẫu, đơn test thị trường, lô hàng nhỏ cần về nhanh.|
|**Hàng đi tuyến Chính ngạch (Đơn hàng trên $1\text{ m}^3$)**|**`1.600.000đ / 1 m³`** hoặc **`6.000đ / 1 kg`** + **Thuế VAT** + **Phí dịch vụ**|Đầy đủ hóa đơn VAT, tờ khai hải quan và chứng từ nhập khẩu chính ngạch cho doanh nghiệp.|
|**Đặt xưởng OEM & Nhập khẩu trọn gói**|[https://t.me/dungtq87](https://t.me/dungtq87)|Hỗ trợ đàm phán nhà máy, kiểm hàng tại xưởng, in thương hiệu OEM riêng và vận chuyển về tận kho Việt Nam.|

---

<div align="center">

### 🤝 Cần hỗ trợ vận chuyển, nhập khẩu chính ngạch hoặc làm hàng OEM?
Liên hệ trực tiếp qua Telegram: **[https://t.me/dungtq87](https://t.me/dungtq87)**

*Phát triển bởi **ABM.DungTQ** • Tuân thủ chuẩn **Khung Prompt 06 Thành Phần** & **Chuẩn thiết kế Workflow ABM v1.0**.*

</div>
