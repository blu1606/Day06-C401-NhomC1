# Journal - Nhật ký Phát triển Dự án GapTutor AI Tutor
**Học viên**: Hồ Tất Bảo Hoàng (2A202600699)
**Ngày ghi nhận**: 04/06/2026

---

## Các công việc đã hoàn thành gần đây

### 1. Cải tiến giao diện LMS 3 cột & Tối ưu Không gian
- Loại bỏ hoàn toàn thanh Header màu đen chiếm diện tích ở cả trang Chat và Quản trị học sinh để tối đa hóa không gian đọc.
- Tái cấu trúc giao diện thành **3 cột ngang chuẩn LMS**:
  1. **Cột trái**: Sidebar Lộ trình học Cohort (Day 1 - Day 9), khóa các ngày khác và chỉ mở truy cập cho **Day 5 (AI Product Thinking)**.
  2. **Cột giữa**: Trình hiển thị slide PDF bài giảng làm trung tâm.
  3. **Cột phải**: Khung chat hỏi đáp AI Assistant.

### 2. Trình đọc PDF.js tùy biến & Đồng bộ Nhảy trang
- Thay thế thẻ iframe mặc định (dễ bị reset zoom/vị trí khi tải lại) bằng bộ render **PDF.js Canvas** mượt mà.
- Thiết lập cơ chế **Lazy loading** cho các trang slide và tích hợp bộ giám sát cuộn trang (`IntersectionObserver`) để tự động cập nhật số trang hiện tại.
- Đồng bộ hóa hai chiều: Người dùng click vào nguồn Citation trong tin nhắn chat $\rightarrow$ PDF tự động cuộn mượt đến slide tương ứng.
- Tích hợp nút **Checkpoint (Undo)** siêu gọn trên PDF Toolbar để người dùng dễ dàng bấm quay lại trang đang đọc dở trước đó.

### 3. Đồng bộ Citation đa nguồn (Multi-Source Citation Chips)
- Thiết kế lại các trích dẫn cồng kềnh thành các **Horizontal Chips** (nút nhỏ xếp hàng ngang) cao chưa đầy 28px sát dưới tin nhắn Bot.
- Tự động thay đổi màu sắc: Chip của slide đang xem sẽ sáng lên với màu tối (`bg-[#3c3a39] text-[#fefcf5]`), các slide khác hiển thị màu xanh liên kết.
- Hỗ trợ hiển thị và nhảy slide đồng thời cho **nhiều citation cùng lúc** (Multi-Source) từ kết quả RAG (ví dụ: khớp cùng lúc `Slide 9` và `Slide 8`).

### 4. Tối ưu Padding & Mật độ Thông tin (Information Density)
- Xóa bỏ cấu trúc card có viền lồng nhau (nested borders) giữa khung suy nghĩ và câu trả lời chính, phẳng hóa toàn bộ bong bóng chat trợ lý trên một nền màu phẳng duy nhất.
- Đưa khối suy nghĩ `/reasoning-trail` và chi tiết gọi tool về dạng **accordion tối giản không viền, mặc định ẩn (collapse)**, thụt lề bằng viền trái mỏng.
- Thu nhỏ các khối tham số JSON gọi Tool (`JsonBlock`) xuống cỡ chữ `text-[9px]` và giới hạn chiều cao tối đa.

### 5. Thiết lập giải pháp Mất kết nối (Offline Fallback & Local Backend)
- **Đã triển khai thực tế và kiểm thử thành công**:
  - **Lớp 1 (Frontend to Backend)**: Tích hợp `AbortController` tự động phát hiện mất mạng, timeout API sau 5 giây hoặc lỗi server (`5xx`), tự động chuyển đổi sang bộ máy RAG cục bộ (Offline RAG KB) trên Client dựa trên file [day05_ai_tutor_slide_sources.json](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/codebase/frontend/data/day05_ai_tutor_slide_sources.json) và hiển thị banner ngoại tuyến màu vàng cùng chỉ báo kết nối trên Header.
  - **Lớp 2 (Backend to External AI API)**: Tối ưu hóa backend FastAPI chạy **100% offline/local** sử dụng thuật toán so khớp từ khóa và ngữ cảnh tối giản (Lexical Search) trực tiếp trên file cơ sở tri thức JSON thay vì gọi API của bên thứ ba (như OpenAI/Gemini). Thiết kế này giúp triệt tiêu hoàn toàn rủi ro nghẽn mạng hoặc lỗi kết nối với API ngoài của mô hình ngôn ngữ lớn khi thuyết trình demo trực tiếp.
