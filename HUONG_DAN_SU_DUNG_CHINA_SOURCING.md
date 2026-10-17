# Tài liệu hướng dẫn sử dụng toàn tập skill China Sourcing (`china-sourcing`)

`china-sourcing` là bộ kỹ năng (skill) tìm kiếm nguồn hàng, thẩm định nhà máy sản xuất, tra cứu bằng hình ảnh, phân tích kịch bản video bán hàng và tính giá vốn nhập khẩu về kho Việt Nam trên năm nền tảng thương mại điện tử lớn nhất Trung Quốc: **1688.com, Taobao/Tmall, Alibaba.com, Pinduoduo và Douyin**. Kỹ năng này được đóng gói độc lập bằng thư viện chuẩn Python 3.9+ kết hợp với `1688-cli` và `douyin-mcp-server`, vận hành đồng nhất trên Google Antigravity (AGY), Claude Code, OpenAI Codex, OpenCode và Cursor.

Toàn bộ luồng công việc tuân thủ kỷ luật vận hành của hệ thống **ABM.DungTQ**: mọi câu lệnh chuyên sâu đều áp dụng **Khung Prompt 06 Thành Phần** và toàn bộ quy trình tự hành được đóng gói theo chuẩn **`TIEU-CHUAN-THIET-KE-WORKFLOW-ABM v1.0`** (`WF-SOURCING-CN-001`).

---

## 1. Kiến trúc đa sàn và nguyên tắc vận hành cốt lõi

Mỗi sàn thương mại điện tử tại Trung Quốc phục vụ một mắt xích khác nhau trong chuỗi cung ứng. Thay vì dùng một công cụ cào dữ liệu chung chung dễ bị chặn bởi hệ thống chống bot, `china-sourcing` điều phối từng nền tảng qua công cụ chuyên biệt tương ứng với mục đích thương mại của sàn đó.

Trên **1688.com**, kỹ năng sử dụng `1688-cli` chạy trên hồ sơ trình duyệt Chrome cô lập (`~/.1688/profiles/default`) kèm tiến trình chạy ngầm (Background Daemon) để lọc trực tiếp các nhà máy sản xuất (`--factory-only`), lấy bảng giá sỉ theo bậc số lượng, trọng lượng đóng gói và giao tiếp trực tiếp qua **1688 WangWang (`旺旺`)**. Với **Douyin**, kỹ năng kết nối `douyin-mcp-server` để tải video không dính logo (watermark-free) và bóc tách toàn bộ lời thoại bán hàng sang văn bản tiếng Trung/Việt nhằm phân tích điểm bán hàng độc nhất (USP). Đối với **Taobao/Tmall** và **Pinduoduo**, kỹ năng hỗ trợ giải mã chuỗi chia sẻ từ ứng dụng di động (`e.tb.cn`, `yangkeduo.com`), kết hợp MCP (`taoke-mcp`, `taobao_mcp`) để khảo sát giá bán lẻ và đọc đánh giá thực tế của người mua trước khi tìm xưởng gốc trên 1688. Riêng **Alibaba.com** đóng vai trò nguồn đối chiếu giá xuất khẩu FOB bằng USD và tiêu chuẩn chứng chỉ quốc tế.

### Ba kỷ luật tự động hóa bắt buộc

Quy trình của `china-sourcing` được thiết kế để người dùng chỉ cần ra lệnh bằng ngôn ngữ tự nhiên trong khung chat của Agent mà không phải thao tác kỹ thuật thủ công:

1. **Cấm yêu cầu người dùng chạy lệnh Terminal khi đăng nhập:** Khi phát hiện phiên 1688 hoặc các sàn chưa đăng nhập (`logged_in: false`), Agent tự động kích hoạt cửa sổ trình duyệt Chrome thật trên màn hình (`china_sourcing.py login --platform 1688`). Hệ thống giữ luồng chờ xác nhận cho đến khi người dùng quét mã QR hoặc nhập mật khẩu/SMS xong, tự động kiểm tra tệp định danh `~/.1688/state.json` (`confirmed: true`) rồi gửi ngay bản hướng dẫn 5 kịch bản khai thác hiệu quả.
2. **Chụp ảnh bằng chứng và tự động canh tin nhắn WangWang 5 phút/lần (`*/5 * * * *`):** Khi người dùng yêu cầu gửi tin nhắn hỏi giá nhà cung cấp qua WangWang (`1688 seller inquire`), hệ thống tự động chụp ảnh màn hình giao diện chat làm bằng chứng vật lý (`.png`), lưu biên lai `07_inquiry_receipt.json`, đồng thời **tự động đặt lịch định kỳ 5 phút 1 lần** kiểm tra tin nhắn phản hồi trong WangWang (`check-wangwang`). Ở mỗi chu kỳ quét, Agent dịch câu trả lời của chủ xưởng sang tiếng Việt, báo cáo lại cho người dùng và hỏi người dùng cần bổ sung thông tin gì để hỏi tiếp nhà cung cấp.
3. **Bằng chứng vật lý và cổng an toàn tài chính:** Mọi dữ liệu từ bước kiểm tra môi trường (`01_doctor.json`), ma trận từ khóa (`02_keywords.json`), dữ liệu thô (`03_raw_offers.json`), báo cáo giá vốn (`04_sourcing_report.md`/`.csv`) đến biên lai chat (`07_inquiry_receipt.json`) đều được ghi thành tệp vật lý theo từng mã phiên chạy (`runs/<run_id>/`). Lệnh xác nhận thanh toán đơn hàng (`1688 checkout confirm`) bị khóa cứng khỏi luồng tự động.

---

## 2. Biểu phí vận chuyển, tỷ giá CNY và đầu mối hỗ trợ nhập khẩu / OEM

Mọi báo cáo tính giá vốn về kho Việt Nam (Landed Cost) trong `china-sourcing` đều áp dụng bộ tham số tài chính và vận chuyển chuẩn hóa dưới đây. Người dùng có thể giữ nguyên mức mặc định hoặc truyền tham số tùy chỉnh theo từng lô hàng.

|Hạng mục chi phí / Dịch vụ|Mức áp dụng chuẩn trong Skill|Ghi chú & Điều kiện áp dụng|
|:---|:---|:---|
|**Tỷ giá Nhân dân tệ (CNY)**|**`4.000 VNĐ / 1 CNY`**|Áp dụng mặc định khi quy đổi giá EXW và phí ship nội địa TQ. Liên hệ **[https://t.me/dungtq87](https://t.me/dungtq87)** nếu cần hỗ trợ đổi tệ hoặc thanh toán hộ.|
|**Cước vận chuyển hàng đi TMĐT**|**`30.000 VNĐ / 1 kg`**|Áp dụng cho đơn hàng lẻ, hàng lấy mẫu (Sample) hoặc lô hàng vừa và nhỏ đi tuyến Thương mại điện tử nhanh.|
|**Cước vận chuyển hàng đi Chính ngạch**|**`1.600.000 VNĐ / 1 m³`** hoặc **`6.000 VNĐ / 1 kg`** + **Thuế VAT** + **Phí dịch vụ**|Áp dụng cho **đơn hàng trên $1\text{ m}^3$** đi chính ngạch có đầy đủ hóa đơn, chứng từ nhập khẩu.|
|**Phí ship nội địa Trung Quốc**|`6 CNY / lô` *(mặc định)*|Chia đều trên tổng số lượng sản phẩm của lô hàng từ xưởng về kho tập kết Trung Quốc.|
|**Hỗ trợ Vận chuyển, Nhập khẩu & OEM**|**[https://t.me/dungtq87](https://t.me/dungtq87)**|Tư vấn trực tiếp về tuyến vận chuyển tối ưu, thủ tục hải quan nhập khẩu, đổi tệ CNY và đặt xưởng **OEM sản phẩm** riêng.|

### Công thức tính giá vốn về kho Việt Nam (Landed Cost)

Đối với **hàng đi tuyến TMĐT (`30.000đ / 1 kg`)**, giá vốn dự kiến trên từng đơn vị sản phẩm được tính theo công thức:

$$\text{Giá vốn 1 SP (TMĐT)} = \left(\text{Giá EXW} + \frac{\text{Ship nội địa TQ}}{\text{Số lượng lô}}\right) \times 4.000 + \left(\text{Trọng lượng 1 SP (kg)} \times 30.000\right)$$

Đối với **hàng đi tuyến Chính ngạch (đơn hàng trên $1\text{ m}^3$)**, giá cơ sở trước thuế VAT và phí dịch vụ trên từng đơn vị sản phẩm được xác định theo mức cước lớn hơn giữa trọng lượng ($6.000\text{đ/kg}$) và thể tích ($1.600.000\text{đ/m}^3$):

$$\text{Giá cơ sở 1 SP (Chính ngạch)} = \left(\text{Giá EXW} + \frac{\text{Ship nội địa TQ}}{\text{Số lượng lô}}\right) \times 4.000 + \max\left(\text{Trọng lượng (kg)} \times 6.000,\ \text{Thể tích (m}^3\text{)} \times 1.600.000\right) + \text{Thuế VAT} + \text{Phí dịch vụ}$$

---

## 3. Năm kịch bản giao việc bằng ngôn ngữ tự nhiên cho Người vận hành / CEO

Sau khi cài đặt skill, bạn không cần nhớ cú pháp dòng lệnh. Hãy giao việc trực tiếp cho Agent trong cửa sổ chat theo 5 mẫu yêu cầu thực chiến dưới đây.

### Kịch bản 1 tìm xưởng sản xuất tận gốc trên 1688 và tính giá vốn về Việt Nam
Dùng khi bạn có tên sản phẩm, mức giá trần tại xưởng (CNY) và quy mô lô hàng dự kiến.
- **Câu lệnh mẫu:**
  > *"Tìm giúp tôi 5 xưởng sản xuất đèn bàn học chống cận trên 1688, giá tại xưởng dưới 35 tệ, tính giá vốn về kho Việt Nam cho lô 100 chiếc."*
- **Kết quả nhận được:** Bảng xếp hạng 5 nhà máy sản xuất trực tiếp (`生产厂家`), link sản phẩm gốc, MOQ, trọng lượng thực tế từ trang chi tiết 1688, giá vốn về Việt Nam theo cả 2 phương án (TMĐT `30.000đ/kg` và Chính ngạch `>1m³`) cùng kịch bản đàm phán WangWang song ngữ Trung và Việt.

### Kịch bản 2 gửi tin hỏi giá qua 1688 WangWang, chụp ảnh bằng chứng và canh phản hồi 5 phút/lần
Dùng ngay sau khi bạn duyệt danh sách xưởng ở Kịch bản 1 và muốn Agent trực tiếp đi hỏi giá sỉ, tồn kho, trọng lượng thực tế hoặc điều kiện in Logo OEM.
- **Câu lệnh mẫu:**
  > *"Gửi tin hỏi giá đi, chụp ảnh chứng minh bạn đã hỏi."*
- **Kết quả nhận được:**
  1. Agent tự động mở phiên chat `1688 WangWang` gửi link thẻ sản phẩm kèm câu hỏi bằng tiếng Trung đến từng xưởng.
  2. Chụp ảnh màn hình giao diện chat thực tế (`.png`) của từng xưởng làm bằng chứng.
  3. Tự động đặt lịch **5 phút 1 lần (`*/5 * * * *`)** kiểm tra tin nhắn phản hồi mới trong WangWang, dịch câu trả lời của chủ xưởng sang tiếng Việt và hỏi bạn cần bổ sung thông tin gì để hỏi tiếp nhà cung cấp.

### Kịch bản 3 tìm nguồn hàng tận gốc bằng hình ảnh (Reverse Image Search)
Dùng khi bạn bắt gặp một mẫu sản phẩm bán chạy trên mạng xã hội hoặc sàn bán lẻ và muốn tìm đúng nhà máy đang gia công mẫu đó trên 1688.
- **Câu lệnh mẫu:**
  > *"Tìm các xưởng 1688 bán sản phẩm giống hệt bức ảnh `/đường/dẫn/anh-mau.jpg` và lập bảng so sánh 5 xưởng có doanh số cao nhất kèm giá vốn về Việt Nam."*

### Kịch bản 4 giải mã link chia sẻ di động Taobao, Pinduoduo, Douyin sang giá sỉ 1688
Dùng khi bạn sao chép chuỗi chia sẻ từ ứng dụng Taobao, Pinduoduo hoặc Douyin trên điện thoại và muốn đối chiếu xem xưởng 1688 đang bỏ sỉ mặt hàng đó ở mức giá nào.
- **Câu lệnh mẫu:**
  > *"Phân tích link chia sẻ Taobao này `【淘宝】https://e.tb.cn/h.StvCjJlWxkNatsx?tk=abc 「Tên sản phẩm」`, bóc tách thông số và tìm xem trên 1688 xưởng gốc đang chào giá sỉ bao nhiêu."*

### Kịch bản 5 tải video Douyin không logo và bóc tách kịch bản bán hàng
Dùng khi bạn muốn nghiên cứu video bán hàng triệu view trên Douyin để lấy tư liệu làm nội dung marketing hoặc tìm nguồn hàng hot trend.
- **Câu lệnh mẫu:**
  > *"Tải video không logo và trích xuất toàn bộ kịch bản lời thoại bán hàng từ link Douyin này để phân tích USP sản phẩm."*

### Kịch bản 6 quét sản phẩm mới đang hot, lượt bán tăng nhanh và bắt trend ngách trên 1688 (`trends`)
Dùng khi bạn đã đăng nhập 1688 và muốn săn các mã hàng mới lên kệ nhưng đã nổ đơn (`上新热销`), các sản phẩm có tốc độ bán 30 ngày tăng vọt (`飙升`), hoặc khám phá các cụm từ khóa ngách (`商机组货`) và bảng xếp hạng chính thức (`1688 排行榜`) mà đối thủ chưa kịp nhập về Việt Nam.
- **Câu lệnh mẫu trong khung chat AI:**
  - **Quét tổng hợp 4 chiều (`mode=all`):**
    > *"Quét giúp tôi các mẫu đèn bàn chống cận mới ra đang hot, lượt bán tăng nhanh nhất trên 1688 và các ngách xu hướng đang lên, tính sẵn giá vốn về Việt Nam cho lô 100 chiếc."*
  - **Chỉ lọc mẫu mới lên kệ có cải tiến tính năng/chất liệu (`mode=new-hot`):**
    > *"Tìm trên 1688 các mẫu quạt cầm tay mini mới ra mắt (có nhãn cải tiến tính năng/thiết kế mới) đang có đơn đặt sỉ cao và báo giá về kho Việt Nam."*
  - **Theo dõi tốc độ nổ đơn theo ngày (`--state-file`):**
    > *"Quét lại tốc độ tăng đơn của ngách đèn bàn chống cận so với lần kiểm tra trước xem mã nào đang tăng đơn/ngày mạnh nhất."*
- **Cơ chế phân tích 4 lớp tín hiệu thực tế từ gói tin `mtop` 1688:**
  1. **Sản phẩm mới đang Hot (`上新热销` — `HotNewScore 0-100`):** Bóc tách trực tiếp nhãn điểm bán hàng mới `newProductSellPoint` (ví dụ: `功能上新 三档调光无频闪`, `材质上新 铝合金灯罩耐用`, `设计上新 双笔筒可拆设计`) và cờ hàng phân phối mới `fenxiaoNewOffer`.
  2. **Lượt bán tăng nhanh (`飙升` — `VelocityIndex` & `FastRisingScore 0-100`):** Áp dụng công thức giảm chấn logarit giữa lượng đơn 30 ngày (`bookedCount`) và tổng doanh số lũy kế (`afterPrice`), kết hợp tỷ lệ khách sỉ quay lại (`turnHead.percent` — `回头率`) và nhãn giá thấp nhất 30–90 ngày (`近N天低价`). Khi dùng kèm `--state-file`, hệ thống tự động tính chênh lệch tuyệt đối **`Δ đơn/ngày`** giữa các lần quét.
  3. **Cụm xu hướng ngách đang lên (`1688 商机组货`):** Tự động gom nhóm các ngách con đang được 1688 đẩy lưu lượng (ví dụ: `全光谱护眼学习灯`, `宿舍磁吸护眼酷毙灯`) kèm ngày phát hiện `topicDate`.
  4. **Bảng xếp hạng ngành hàng 1688 (`1688 排行榜`):** Trích xuất trực tiếp bộ 3 đường dẫn Bảng Bán Chạy (`热销榜` — `rankType=1`), Bảng Tăng Tốc (`飙升榜` — `rankType=2`) và Bảng Hàng Mới (`新品榜` — `rankType=3`).

---

## 4. Cẩm nang tham chiếu CLI dành cho Agent (`scripts/china_sourcing.py`)

Phần này dành cho các AI Agent (hoặc kỹ thuật viên) khi điều phối trực tiếp script lõi `scripts/china_sourcing.py`.

```bash
# 1. Kiểm tra trạng thái công cụ, phiên đăng nhập 1688 và tự động vá 4 file 1688-cli (--fix)
python3 scripts/china_sourcing.py doctor --fix --output runs/<run_id>/01_doctor.json

# 2. Tự động bật trình duyệt Chrome cho người dùng đăng nhập và chờ xác nhận hoàn tất
python3 scripts/china_sourcing.py login --platform 1688

# 3. Quét sản phẩm mới đang hot, lượt bán tăng nhanh & trend ngách 1688 (kèm giá vốn VNĐ & theo dõi Δ đơn/ngày)
python3 scripts/china_sourcing.py trends \
  --keyword "护眼台灯" "国AA级护眼灯" \
  --mode all \
  --max 40 \
  --qty 100 \
  --state-file runs/trends_state.json \
  --output-json runs/<run_id>/03_trends.json \
  --output-md runs/<run_id>/04_trends_report.md

# 4. Sinh ma trận từ khóa tiếng Trung giản thể & URL tra cứu đa sàn
python3 scripts/china_sourcing.py translate-keywords \
  --product "Đèn bàn học chống cận" \
  --zh "护眼台灯" "学生学习专用台灯" "国AA级护眼灯" \
  --en "eye protection desk lamp" \
  --max-price-cny 35 \
  --output runs/<run_id>/02_keywords.json

# 5. Giải mã chuỗi link chia sẻ từ ứng dụng Taobao, 1688, Pinduoduo, Douyin, Alibaba (kèm mở link rút gọn)
python3 scripts/china_sourcing.py parse-link --resolve "<chuỗi_chia_sẻ_hoặc_url>"

# 6. Tính nhanh giá vốn về kho Việt Nam (TMĐT 30.000đ/kg & Chính ngạch >1m³)
python3 scripts/china_sourcing.py landed-cost --price-cny 16.5 --qty 100 --weight-kg 0.5 --volume-cbm 0.003

# 7. Tổng hợp báo cáo Markdown, CSV và bản nháp câu hỏi WangWang
python3 scripts/china_sourcing.py report \
  --input runs/<run_id>/03_raw_offers.json \
  --output-md runs/<run_id>/04_sourcing_report.md \
  --output-csv runs/<run_id>/04_sourcing_report.csv \
  --output-wangwang runs/<run_id>/05_wangwang_draft.md \
  --qty 100

# 8. Gửi tin hỏi giá qua 1688 WangWang kèm khóa chống gửi trùng SHA-256 và chụp ảnh bằng chứng
python3 scripts/china_sourcing.py inquire-wangwang \
  --run-id "<run_id>" \
  --offer-id "<offerId>" \
  --message "老板你好，请问这款有现货吗？单件带包装的实际重量是多少？" \
  --receipt runs/<run_id>/07_inquiry_receipt.json \
  --screenshot runs/<run_id>/07_wangwang_proof_1_<offerId>.png

# 9. Quét tin nhắn phản hồi mới của người thật trên 1688 WangWang (chạy định kỳ 5 phút/lần)
python3 scripts/china_sourcing.py check-wangwang \
  --receipt runs/<run_id>/07_inquiry_receipt.json \
  --state-file runs/<run_id>/08_wangwang_state.json \
  --only-new \
  --output runs/<run_id>/08_wangwang_poll.json
```

---

## 5. Cấu trúc thư mục và vị trí cài đặt đa Agent

Gói kỹ năng `china-sourcing` giữ cấu trúc gọn nhẹ, không phụ thuộc thư viện ngoài của Python:

```text
china-sourcing/
├── SKILL.md                                 # Chỉ thị định tuyến & quy tắc vận hành cho AI Agent (v2.1.0)
├── README.md                                # Tài liệu giới thiệu & câu lệnh mẫu thực chiến
├── HUONG_DAN_SU_DUNG_CHINA_SOURCING.md      # Cẩm nang hướng dẫn sử dụng toàn tập
├── patches/
│   └── 1688-cli/                            # Bộ 4 bản vá 1688-cli (search-mtop, seller-chat/inquire/messages)
├── scripts/
│   ├── china_sourcing.py                    # CLI điều phối đa sàn, quét trend 1688, tính giá vốn & canh tin WangWang
│   └── tests/
│       └── test_china_sourcing.py           # Bộ kiểm thử đơn vị (24/24 unit tests)
└── references/
    ├── platform-playbooks.md                # Sổ tay lệnh chuyên sâu cho 1688, Taobao, Alibaba, PDD, Douyin
    └── abm-workflow-and-prompts.md          # Khung Prompt 06 Thành Phần & Workflow ABM v1.0 (WF-SOURCING-CN-001)
```

Để sử dụng trên mọi nền tảng Agent, thư mục `china-sourcing` được đồng bộ tại 5 đường dẫn chuẩn:
- **Workspace hiện tại:** `/Volumes/1/AGY/.agents/skills/china-sourcing`
- **Chuẩn `.agents` toàn cục:** `~/.agents/skills/china-sourcing`
- **Google Antigravity (AGY):** `~/.gemini/config/skills/china-sourcing`
- **Claude Code:** `~/.claude/skills/china-sourcing`
- **OpenAI Codex:** `~/.codex/skills/china-sourcing`

---

## 6. Thông tin liên hệ hỗ trợ

Mọi nhu cầu tư vấn về **vận chuyển hàng hóa từ Trung Quốc về Việt Nam** (tuyến TMĐT `30.000đ/kg` hoặc tuyến Chính ngạch cho đơn hàng trên $1\text{ m}^3$: `1.600.000đ/m³` · `6.000đ/kg` + thuế VAT + phí dịch vụ), **thủ tục nhập khẩu chính ngạch**, **đổi tệ CNY (`4.000đ/CNY`)**, thanh toán hộ 1688/Taobao và **đặt xưởng sản xuất OEM thương hiệu riêng**, vui lòng liên hệ trực tiếp qua Telegram:

👉 **[https://t.me/dungtq87](https://t.me/dungtq87)**
