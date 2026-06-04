# Phase 4 - Kế hoạch Xử lý Mất kết nối Backend (Offline Fallback)

Tài liệu này chi tiết hóa giải pháp phát hiện mất kết nối API với máy chủ Backend, tự động chuyển sang chế độ phản hồi ngoại tuyến (Offline Fallback) và hiển thị thông báo trực quan cho người dùng.

---

Để tự động chuyển sang chế độ Offline Fallback, client sẽ kiểm tra các lỗi kết nối khi gọi API `/api/diagnose` (Khuyến nghị đổi tên chuẩn hóa thành `/api/chat` hoặc `/api/tutor` để khớp với quy chuẩn sản phẩm AI thực tế):

> [!NOTE]
> ### 🔍 Khảo sát chuẩn API của các sản phẩm AI Production:
> 
> 1. **Vercel AI SDK Standard (Next.js)**:
>    * **API Path**: `POST /api/chat`
>    * **Chi tiết**: Đây là chuẩn mặc định phổ biến nhất trong thế giới Next.js. Hook `useChat` của Vercel SDK mặc định tìm kiếm endpoint này để thực hiện stream tokens.
> 2. **OpenAI Compatibility Standard (vLLM, Ollama, LiteLLM)**:
>    * **API Path**: `POST /v1/chat/completions`
>    * **Chi tiết**: Chuẩn hóa REST API của OpenAI được áp dụng rộng rãi cho tất cả các proxy server để đảm bảo tương thích ngược với các thư viện client SDK (như thư viện `openai` trên Python/JS).
> 3. **LangChain & LangGraph (LangServe / LangGraph Cloud)**:
>    * **API Path**: `POST /threads/{thread_id}/runs` hoặc `POST /invoke` hoặc `POST /stream`
>    * **Chi tiết**: Thiết kế hướng hành động (Action-oriented) của LangGraph biểu thị việc chạy (run) một đồ thị (graph) trên một luồng (thread) hội thoại cố định.
> 
> **=> Đánh giá dự án hiện tại**: Tên hiện tại `/api/diagnose` mang tính chất phân tích lỗi/khảo sát hệ thống (từ codebase cũ). Để chuẩn hóa theo chuẩn **Vercel AI SDK**, chúng ta đề xuất lộ trình refactor đổi tên endpoint này thành **`/api/chat`** ở cả Next.js Route Handler và FastAPI Backend.


*   **Thời gian chờ (Timeout)**: 
    *   Sử dụng `AbortController` để thiết lập thời gian chờ tối đa là **5.000ms (5 giây)** cho các yêu cầu API.
    *   Nếu sau 5 giây không nhận được phản hồi từ server, tự động kích hoạt tiến trình `abort()` và chuyển sang Offline mode.
*   **Lỗi mạng (Network Error / CORS / DNS Failure)**:
    *   Bọc cuộc gọi `fetch()` trong một khối `try-catch`.
    *   Nếu `fetch` ném ra ngoại lệ (do mất mạng internet, server sập, hoặc lỗi DNS), tiến hành bắt lỗi và tự động kích hoạt Offline mode.
*   **Lỗi HTTP Status Code (Server Errors)**:
    *   If API trả về mã trạng thái `5xx` (Internal Server Error, Gateway Timeout, Bad Gateway), client sẽ coi đó là mất kết nối và kích hoạt chế độ dự phòng thay vì báo lỗi đỏ.

---

## 2. Kịch bản các Câu hỏi Phổ biến trong Fallback Mode (Offline Knowledge Base)

Khi hoạt động ngoại tuyến, AI Tutor không thể gọi LLM để suy luận tự do. Hệ thống sẽ sử dụng công cụ khớp chuỗi (Substring/Keyword Matching) từ file dữ liệu [day05_ai_tutor_slide_sources.json](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/codebase/frontend/data/day05_ai_tutor_slide_sources.json) để phục vụ các nhóm câu hỏi phổ biến sau:

### Nhóm A: Sự khác biệt sản phẩm phần mềm truyền thống vs AI Product
*   **Câu hỏi mẫu**: *"AI product khác gì phần mềm thường?"*, *"uncertainty là gì?"*, *"ba lớp bất định"*.
*   **Xử lý offline**: Trả về định nghĩa chi tiết của 3 lớp bất định (Input, Output, Process) và phương sai sản phẩm, trích dẫn **Slide 9 & 8**.

### Nhóm B: Thiết kế sản phẩm và đường dẫn dự phòng (Fallback / UX Recovery)
*   **Câu hỏi mẫu**: *"thiết kế sản phẩm AI cần lưu ý gì?"*, *"fallback là gì?"*, *"graceful failure"*, *"ngăn ngừa thiệt hại"*.
*   **Xử lý offline**: Trả về 3 trụ cột thiết kế (Outcome, Threshold, Fallback) và nguyên tắc thiết kế khi AI sai (Graceful Failure), trích dẫn **Slide 20 & 30**.

### Nhóm C: Phân tách Task học máy (Task Splitting / Boundary)
*   **Câu hỏi mẫu**: *"tách task thế nào?"*, *"automation và augmentation"*, *"tăng năng lực hay tự động hóa"*.
*   **Xử lý offline**: Giải thích quy trình đánh giá các task nhỏ để tự động hóa hoặc tăng năng lực con người, trích dẫn **Slide 15 & 14**.

### Nhóm D: Lập trình bằng đặc tả (Vibe Coding / Specification)
*   **Câu hỏi mẫu**: *"vibe coding là gì?"*, *"code bằng spec"*, *"lập trình bằng tiếng anh"*.
*   **Xử lý offline**: Giải thích khái niệm lập trình bằng việc đặc tả yêu cầu thay vì viết code tay, trích dẫn **Slide 45**.

### Nhóm E: Định tuyến lỗi (Error Routing)
*   **Câu hỏi mẫu**: *"error routing là gì?"*, *"định tuyến lỗi"*.
*   **Xử lý offline**: Giải thích cách phân phối và chuyển tiếp các trường hợp lỗi mô hình sang luồng phần mềm truyền thống, trích dẫn **Slide 12**.

---

## 3. Thiết kế Thông báo Giao diện (Offline UI Notification)

Học hỏi từ các sản phẩm AI hàng đầu (Gemini, ChatGPT, Perplexity):

*   **Gemini/ChatGPT**: Khi mất kết nối mạng, các nút gửi tin nhắn bị vô hiệu hóa hoặc có một thanh banner cam trên đầu trang: *"You are offline. Reconnecting..."*.
*   **Perplexity/DeepSeek**: Hiển thị dòng trạng thái nhỏ bên dưới khung nhập liệu báo hiệu đang sử dụng cơ sở tri thức cục bộ.

### Đề xuất UI thiết kế cho GapTutor:

1.  **Thanh Trạng thái Kết nối (Header Connection Status)**:
    *   Nếu máy chủ backend mất kết nối, nút `Live API` trên thanh Header của Khung Chat sẽ tự động đổi màu sang viền đỏ và nhấp nháy chữ `[⚠️ Mất kết nối - Đang tự động dự phòng]`.
2.  **Thông báo Dòng tin nhắn (Message Inline Alert)**:
    *   Mỗi tin nhắn phản hồi được tạo ra trong chế độ Offline Fallback sẽ có thêm một dòng ghi chú nhỏ, màu xám nhạt nằm dưới nội dung text câu trả lời chính:
        `ℹ️ Câu trả lời này được truy xuất ngoại tuyến từ Slide bài học do mất kết nối tới AI Engine.`
3.  **Dòng gợi ý câu hỏi khi mất kết nối (Offline Query Hints)**:
    *   Hiển thị một thanh banner nhỏ màu vàng nhạt phía trên khung Input:
        `⚠️ Đang hoạt động ngoại tuyến. Bạn có thể hỏi về: Ba lớp bất định, Trụ cột thiết kế, Error routing, Vibe coding...`

---

## 4. Kế hoạch thay đổi mã nguồn (Proposed Code Changes)

### [MODIFY] [chat-panel-interactive.tsx](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/codebase/frontend/components/chat-panel-interactive.tsx)
*   **Quản lý State**:
    *   Thêm state `isBackendConnected` (boolean, mặc định `true`).
    *   Thêm state `isFallbackModeActive` (boolean, mặc định `false`).
*   **Cải tiến Hàm `handleSend`**:
    *   Bọc cuộc gọi fetch `/api/diagnose` với một `AbortController` có timeout `5000ms`.
    *   Trong khối `catch (error)` hoặc khi timeout xảy ra, gọi hàm `switchToOfflineFallback(userText)` để kích hoạt dự phòng.
    *   Cập nhật `isBackendConnected = false` and `isFallbackModeActive = true`.
*   **Giao diện Chat**:
    *   Nếu `isFallbackModeActive` là `true`, thêm banner cảnh báo màu vàng nhạt phía dưới Header.
    *   Thêm dòng ghi chú `ℹ️ Phản hồi ngoại tuyến từ tri thức Slide Day 5` cho các tin nhắn được tạo ra trong thời gian này.

---

## 5. Kế hoạch xác minh (Verification Plan)

### Kiểm thử Tự động & Giả lập lỗi
1.  **Giả lập mất mạng**: Tắt server backend (hoặc sửa đổi đường dẫn API `/api/diagnose` thành một url không tồn tại `/api/diagnose-broken`).
2.  **Xác minh chuyển đổi**: Gửi câu hỏi bất kỳ, kiểm tra xem sau 5 giây (hoặc ngay lập tức nếu lỗi mạng) hệ thống có tự động chuyển đổi sang phản hồi Slide RAG cục bộ hay không.
3.  **Kiểm tra UI**: Xác nhận banner màu vàng xuất hiện và có ghi chú ngoại tuyến dưới bong bóng chat.
4.  **Kiểm tra build**: Đảm bảo dự án Next.js vẫn build thành công không lỗi cú pháp.
