# Review Chatbot NEO — Vietnam Airlines
**Phương pháp: 40-phút UX Audit** | Ngày review: 03/06/2026

---

## PHẦN 1 — DÙNG THỬ: Promise vs Thực tế

### Promise của NEO
Trang chủ Vietnam Airlines định vị NEO là "trợ lý ảo" có khả năng hỗ trợ toàn diện: tìm chuyến bay, giá vé, thủ tục, ưu đãi — tức kỳ vọng người dùng sẽ nhận được câu trả lời trực tiếp, không cần rời khỏi chat.

---

### Query 1 — Hỏi giá vé SGN → SFO

| Bước | Hành động | Phản hồi của NEO |
|------|-----------|-----------------|
| 1 | Hỏi giá vé SGN → SFO | Thu thập thông tin: thiếu ngày đi + số hành khách ✅ |
| 2 | Cung cấp ngày: 10/07/2026 | Xác nhận, hỏi tiếp số hành khách ✅ |
| 3 | "2 người lớn, 1 em bé" | Tóm tắt đầy đủ, hỏi xác nhận ✅ |
| 4 | Xác nhận "Có" | **"Hệ thống gặp lỗi khi tìm kiếm chuyến bay"** ❌ |
| 5 | Hỏi giá vé trung bình | **Lặp lại thông báo lỗi hệ thống** ❌ |
| 6 | Hỏi giá tốt nhất để đến Mỹ | **Lặp lại thông báo lỗi hệ thống** ❌ |

**Điểm gãy:** Sau khi tìm kiếm thất bại, NEO **không chuyển sang mode fallback**. Người dùng thay đổi intent (từ "tìm chuyến cụ thể" → "cho giá trung bình") nhưng NEO vẫn hiểu là tìm kiếm chuyến bay và tiếp tục báo lỗi — **intent shift bị bỏ qua hoàn toàn**.

> **Kỳ vọng:** Cung cấp giá vé tham khảo/trung bình từ SGN → SFO
> **Thực tế:** Lặp lại lỗi kỹ thuật, không nhận diện yêu cầu mới

---

### Query 2 — Thủ tục trước khi bay + Prompt Injection

| Bước | Hành động | Phản hồi của NEO |
|------|-----------|-----------------|
| 1 | Hỏi thủ tục trước khi bay | Cung cấp đầy đủ: giấy tờ, check-in, lưu ý ✅ |
| 2 | Inject nội dung nguy hiểm ("đánh bom sân bay") | Từ chối, redirect về chủ đề hàng không ✅ |

**Nhận xét:** NEO xử lý tốt — từ chối không phán xét, không leak thông tin nhạy cảm, giữ tone trung lập. Đây là path hoạt động tốt nhất trong toàn bộ transcript.

---

### Query 3 — Ưu đãi và áp dụng đồng thời

| Bước | Hành động | Phản hồi của NEO |
|------|-----------|-----------------|
| 1 | Hỏi chương trình ưu đãi | Liệt kê 5 nhóm ưu đãi chi tiết ✅ |
| 2 | Hỏi có dùng nhiều ưu đãi cùng lúc không | Phân loại rõ case được/không được ✅ |
| 3 | Hỏi ưu đãi cho chuyến bay đến New York | **Liệt kê ưu đãi + giá vé tham khảo cụ thể** ✅ |

**Nhận xét đáng chú ý:** Query 3 bước cuối — NEO **cung cấp được giá vé tham khảo** cho New York mà ở Query 1 lại không làm được cho San Francisco khi người dùng xin giá trung bình. Đây là **bất nhất về hành vi** giữa hai flow.

---

## PHẦN 2 — VẼ FLOW AS-IS

### 2.1 Happy Path (Ưu đãi / Thủ tục)

```
Người dùng đặt câu hỏi
        │
        ▼
NEO hiểu intent ngay
        │
        ▼
Trả lời đầy đủ, có cấu trúc
        │
        ▼
Người dùng hỏi sâu hơn
        │
        ▼
NEO xử lý được, cung cấp chi tiết
        │
        ▼
✅ KẾT THÚC THỎA MÃN
```

---

### 2.2 Low-Confidence Path (Tìm chuyến bay không có kết quả)

```
Người dùng hỏi giá vé cụ thể
        │
        ▼
NEO thu thập thông tin (multi-turn) ✅
        │
        ▼
Xác nhận thông tin ✅
        │
        ▼
Gọi API tìm kiếm → THẤT BẠI
        │
        ▼
⚠️  Trả về thông báo lỗi hệ thống
        │
        ▼
Người dùng chuyển intent: "cho giá trung bình"
        │
        ▼
⛔ NEO KHÔNG NHẬN DIỆN INTENT MỚI
        │
        ▼
Tiếp tục báo lỗi hệ thống (x3 lần)
        │
        ▼
🔴 NGƯỜI DÙNG KẸT — buộc reset phiên
```

**Người dùng kẹt tại:** Bước chuyển intent sau khi API lỗi. NEO không có fallback logic.

---

### 2.3 Failure Path (API Error Loop)

```
API lỗi
  │
  ├─ Người dùng hỏi lại cùng query → ❌ Lỗi
  ├─ Người dùng đổi query (giá trung bình) → ❌ Lỗi
  ├─ Người dùng đổi query (giá tốt nhất) → ❌ Lỗi
  └─ Người dùng phải RESET PHIÊN để thoát
```

**Pattern nguy hiểm:** Dead loop — không có lối thoát tự nhiên, không có handoff sang kênh khác.

---

### 2.4 Correction Path (Sau khi Reset)

```
Reset phiên chat
        │
        ▼
NEO reset về trạng thái ban đầu
        │
        ▼
Bắt đầu lại từ đầu (mất toàn bộ context)
        │
        ▼
⚠️  Không có correction log
⚠️  Không ghi nhận lỗi để xử lý sau
```

---

### 2.5 Tóm tắt: Người dùng kẹt ở đâu?

```
FLOW TỔNG QUAN — NEO As-Is

[Câu hỏi đơn giản] ──────────────────────────→ ✅ Happy (Ưu đãi, Thủ tục)

[Tìm chuyến bay]
      │
      └──→ [API OK] ──→ ✅ Kết quả
      │
      └──→ [API Lỗi] ──→ ⛔ KẸT ──→ Đổi intent ──→ ⛔ KẸT ──→ RESET
                                          ▲
                                    ĐIỂM GÃY #1
                              (NEO không nhận intent shift)

[Prompt injection] ──────────────────────────→ ✅ Từ chối tốt
```

---

## PHẦN 3 — SỬA PATH YẾU NHẤT

### Path yếu nhất: Tìm chuyến bay → API thất bại → Intent shift bị bỏ qua

Đây là path có tác động lớn nhất vì:
- Xảy ra ngay ở use case cốt lõi (tìm/hỏi giá vé)
- Người dùng bị kẹt hoàn toàn, không có lối thoát
- Thực tế NEO **có khả năng** trả về giá tham khảo (thấy ở Query 3) nhưng không trigger được ở đây

---

### To-Be: Đề xuất cải tiến

#### 3.1 Nhận diện Intent Shift sau lỗi

**Vấn đề:** Sau khi API lỗi, NEO tiếp tục hiểu mọi tin nhắn là "tìm kiếm chuyến bay".

**Giải pháp:** Thêm một lớp intent re-classification sau error state.

```
Khi trạng thái = ERROR:
  ├─ Nếu người dùng hỏi "giá trung bình / giá tham khảo / khoảng giá"
  │     → Chuyển sang mode: CÂU TRẢ LỜI TĨNH (giá tham khảo từ knowledge base)
  │
  ├─ Nếu người dùng hỏi lại cùng route
  │     → Hỏi lại 1 lần, sau đó handoff
  │
  └─ Nếu người dùng im lặng hoặc reset
        → Ghi log, kết thúc gracefully
```

---

#### 3.2 Fallback Message thông minh hơn (Thay thế thông báo lỗi)

**Hiện tại:**
> "Rất tiếc, hệ thống gặp lỗi khi tìm kiếm chuyến bay. Xin quý khách vui lòng thử lại sau hoặc liên hệ với đại lý hỗ trợ."

**Đề xuất To-Be:**
> "NEO hiện không thể kết nối hệ thống đặt vé để lấy kết quả chính xác cho chặng SGN–SFO ngày 10/07. Tuy nhiên, theo dữ liệu tham khảo, giá vé phổ thông một chiều SGN–SFO thường dao động từ **khoảng 18–30 triệu VND** tùy thời điểm đặt. Quý khách muốn NEO kiểm tra lại sau, hay hỗ trợ theo cách khác?"

**Kèm theo 3 quick-action buttons:**
- 🔄 `Thử lại tìm kiếm`
- 💬 `Nói chuyện với tư vấn viên`
- 📋 `Xem giá tham khảo theo tháng`

---

#### 3.3 Undo / Sửa thông tin (Trong flow thu thập dữ liệu)

**Vấn đề:** Sau khi xác nhận "Có", người dùng không thể sửa thông tin nếu phát hiện nhầm.

**Đề xuất:** Hiển thị nút **"Sửa thông tin"** song song với "Có/Không" ở bước xác nhận, hoặc cho phép người dùng gõ "sửa ngày" / "đổi hành khách" bất kỳ lúc nào trong flow.

```
Thay vì chỉ hỏi: "Quý khách xác nhận thông tin đúng không? (Có/Không)"

→ Hiển thị:
  ✅ Xác nhận đúng
  ✏️  Sửa ngày đi
  ✏️  Sửa số hành khách
  ✏️  Đổi hành trình
```

---

#### 3.4 Handoff sang kênh người thật

**Vấn đề:** NEO không proactively đề xuất chuyển sang kênh hỗ trợ khi thất bại nhiều lần.

**Đề xuất:** Sau **2 lần lỗi liên tiếp** với cùng người dùng, NEO tự động hiển thị:

> "NEO thấy bạn đang gặp khó khăn với tìm kiếm này. Để hỗ trợ tốt hơn, bạn có muốn:"
> - 📞 Gọi tổng đài: **1900 1100**
> - 💻 Tìm kiếm trực tiếp tại website
> - 📧 Để lại email — tư vấn viên sẽ liên hệ lại

---

#### 3.5 Correction Log (Cho team phát triển)

**Đề xuất:** Mỗi lần NEO lỗi, hệ thống nên tự động log:

| Trường | Giá trị mẫu |
|--------|-------------|
| Session ID | `#abc123` |
| Intent ban đầu | `flight_search` |
| Thông tin đã thu thập | SGN → SFO, 10/07, 2A+1I |
| Điểm thất bại | API timeout / no result |
| Intent sau thất bại | `price_reference_query` |
| NEO có nhận ra intent mới không | ❌ Không |
| Người dùng có thoát qua handoff không | ❌ Tự reset |

> Correction log này giúp team nhận diện pattern lỗi tái diễn và cải thiện intent classifier theo thời gian.

---

## Tổng kết

| Dimension | Đánh giá | Ghi chú |
|-----------|----------|---------|
| Thu thập thông tin (multi-turn) | ✅ Tốt | Form-filling flow rõ ràng |
| Xử lý intent đơn | ✅ Tốt | Ưu đãi, thủ tục trả lời đầy đủ |
| Safety / Prompt injection | ✅ Tốt | Từ chối đúng cách, không phán xét |
| Fallback khi API lỗi | ❌ Yếu | Không có fallback, dead loop |
| Nhận diện intent shift | ❌ Yếu | Bỏ qua hoàn toàn khi đang trong error state |
| Handoff tự nhiên | ❌ Thiếu | Không có cơ chế chuyển kênh |
| Tính nhất quán | ⚠️ Trung bình | Query 3 trả được giá tham khảo, Query 1 thì không |

**Ưu tiên fix cao nhất:** Intent re-classification sau error state + Fallback message có giá tham khảo tĩnh.
