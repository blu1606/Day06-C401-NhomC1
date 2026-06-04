# GapTutor AI Engine & Giao Diện Giám Sát Agent Trace

Chào mừng bạn đến với **GapTutor**, giải pháp Trợ lý Học tập AI thông minh hỗ trợ sinh viên lớp AI Thực Chiến tra cứu slides bài học thông qua mô hình **ReAct Agent**. Hệ thống cho phép sinh viên hỏi đáp bằng ngôn ngữ tự nhiên và hiển thị trực quan các bước suy nghĩ (Thought), gọi công cụ (Action), nhận kết quả (Observation) và định vị chính xác trang Slide bài học liên quan.

---

## 🏗️ Kiến Trúc & Công Nghệ Sử Dụng

Dự án được phát triển theo mô hình Client-Server chia tách rõ ràng:

### 1. Backend (AI Engine & API Server) - Thư mục `/codebase/ai`
- **Framework:** `FastAPI` (Python) cung cấp API hiệu năng cao với CORS được cấu hình đầy đủ.
- **AI Agent Core:** Tự xây dựng **ReAct Agent** (vòng lặp *Thought -> Action -> Observation -> Final Answer*).
- **LLM Providers:** Hỗ trợ linh hoạt thông qua `OpenRouter`, `OpenAI` (GPT-4o-mini), `Anthropic` (Claude 3.5 Haiku) và `Gemini 2.5 Flash`. Hỗ trợ chế độ **Mock LLM Provider** để chạy thử nghiệm terminal mà không cần API key.
- **Công cụ bổ trợ (Tools):**
  - `search_slide_sources`: Tìm kiếm tài liệu slide học tập từ cơ sở dữ liệu `day05_ai_tutor_slide_sources.json`.
  - `verify_academic_integrity`: Công cụ Guardrail tự động phát hiện và từ chối cung cấp lời giải trực tiếp để bảo vệ tính liêm chính học thuật.
  - `list_tools`: Liệt kê các công cụ khả dụng của hệ thống.
- **Evaluation Runner:** Script `run_eval.py` tự động đo đạc độ chính xác gọi tool, độ chính xác tham số và phát hiện hallucination dựa trên bộ test case trong `/codebase/eval`.

### 2. Frontend (Trace UI Dashboard) - Thư mục `/codebase/frontend`
- **Framework:** `Next.js 16` (React 19) sử dụng App Router & TypeScript.
- **Thiết kế giao diện (UI/UX):** Phong cách thiết kế lấy cảm hứng từ **Tavily.com** mang âm hưởng tạp chí biên tập (editorial magazine) cao cấp:
  - Tông màu chủ đạo là màu kem giấy ấm (`#fefcf5`), chữ màu đen ấm (`#3c3a39`) mang lại cảm giác dễ đọc.
  - Accent palette nổi bật với màu cam năng động (`#ff7300`).
  - Font chữ hiện đại: `Suisse Int'l` cho nội dung chính và `Suisse Int'l Mono` cho các nhãn hệ thống.
- **Các thành phần giao diện chính:**
  - **AI Tutor Chat:** Khung chat tương tác với mô hình học tập thời gian thực.
  - **PDF Central Viewer:** Trình xem slide PDF trực quan, tự động nhảy đến slide tương ứng dựa trên trích dẫn của AI.
  - **Trace Telemetry:** Bảng điều khiển chi tiết giám sát các bước chạy của ReAct Agent (Token sử dụng, Chi phí ước tính, Thời gian thực thi, chi tiết từng bước suy nghĩ).
  - **Student Analytics & Test Runs:** Tab theo dõi các lượt chạy kiểm thử tự động, danh sách ca đánh giá (Evaluation cases), Prompt và phiên bản prompt của hệ thống.

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Thử (Setup & Run Guide)

### 📋 Yêu cầu hệ thống
- **Python:** Phiên bản 3.10 trở lên (Khuyên dùng công cụ quản lý package [**uv**](https://github.com/astral-sh/uv) để tối ưu thời gian cài đặt).
- **Node.js:** Phiên bản 18 trở lên (Khuyên dùng [**pnpm**](https://pnpm.io/) hoặc `npm`).

---

### Bước 1: Khởi chạy Backend (FastAPI API)

1. Di chuyển vào thư mục chứa code AI backend:
   ```bash
   cd codebase/ai
   ```

2. Cài đặt các thư viện Python:
   *Nếu sử dụng `uv` (Khuyên dùng):*
   ```bash
   uv sync
   ```
   *Nếu sử dụng `pip` thông thường:*
   ```bash
   pip install -r requirements.txt
   ```

3. Thiết lập biến môi trường (Environment Variables):
   - Tạo file `.env` từ file mẫu `.env.example`:
     ```bash
     cp .env.example .env
     ```
   - Mở file `.env` vừa tạo và điền API key bạn muốn dùng (Ví dụ: `GEMINI_API_KEY`, `OPENAI_API_KEY`, hoặc `OPENROUTER_API_KEY`).
   - *Lưu ý:* Nếu không cấu hình API key, hệ thống sẽ tự động sử dụng chế độ **Mock LLM Provider** hỗ trợ chạy thử nghiệm nhanh.

4. Chạy Backend server thông qua Uvicorn:
   ```bash
   uv run uvicorn backend.main:app --port 8000 --reload
   ```
   *Server backend sẽ chạy tại địa chỉ:* `http://localhost:8000`

5. (Tùy chọn) Chạy bộ test kiểm thử tự động & Đánh giá Agent:
   - Chạy test unit:
     ```bash
     python -m unittest discover -s tests
     ```
   - Chạy bộ đánh giá chất lượng Agent:
     ```bash
     python run_eval.py
     ```

---

### Bước 2: Khởi chạy Frontend (Next.js Application)

1. Mở một terminal mới và di chuyển vào thư mục frontend:
   ```bash
   cd codebase/frontend
   ```

2. Cài đặt các gói phụ thuộc (dependencies):
   *Nếu dùng `pnpm` (Khuyên dùng):*
   ```bash
   pnpm install
   ```
   *Nếu dùng `npm`:*
   ```bash
   npm install
   ```

3. Khởi chạy ứng dụng ở chế độ phát triển (Development Mode):
   *Nếu dùng `pnpm`:*
   ```bash
   pnpm run dev
   ```
   *Nếu dùng `npm`:*
   ```bash
   npm run dev
   ```

4. Truy cập giao diện:
   - Mở trình duyệt web và truy cập địa chỉ: `http://localhost:3000`
   - Giao diện chính sẽ tự động điều hướng bạn đến trang chat `/u/0/app`.

---

### Bước 3: Cấu hình cổng kết nối mạng (Tùy chọn - Ngrok)
Nếu muốn expose API cục bộ ra Internet để chạy thử nghiệm từ các thiết bị khác hoặc tích hợp các webhook bên ngoài:
```bash
ngrok http 8000
```
