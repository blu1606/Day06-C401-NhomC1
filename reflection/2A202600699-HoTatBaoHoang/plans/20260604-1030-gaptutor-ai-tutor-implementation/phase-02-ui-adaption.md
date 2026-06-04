# Phase 2: Tùy biến LMS Sidebar, Bỏ Header & Di chuyển Chat sang Cột phải

## Context Links
- [sidebar-unified.tsx](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/codebase/frontend/components/sidebar-unified.tsx)
- [agent-trace-viewer.tsx](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/codebase/frontend/components/agent-trace-viewer.tsx)
- [chat-panel-interactive.tsx](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/codebase/frontend/components/chat-panel-interactive.tsx)

## Overview
- **Priority:** High
- **Status:** Pending
- **Description:** Chuyển đổi layout chính thành 3 cột. Cải tiến Sidebar thành lộ trình học LMS của Cohort 2 (chỉ active Day 5), xóa header chiếm chỗ, và di chuyển khung chat AI Tutor sang cột thứ 3 bên phải.

## Requirements
- Xóa bỏ component `Header` đen chiếm diện tích ở trên đầu của trang Chat và trang Admin.
- Tùy biến lại `SidebarUnified` thành menu dọc hiển thị Lộ trình học (Learning Path) giống hình chụp:
  - Header sidebar: **AI.20K - Cohort 2**
  - Thanh tiến trình hiển thị: **11%** (có thanh bar fill màu trắng hoặc xanh da trời nhạt tương ứng).
  - Ba tab điều hướng: **Path** (Active/Gạch chân trắng), **Learners**, **Discuss**.
  - Danh sách bài học gồm các Day học tập chính xác theo ảnh chụp màn hình:
    - `1. Attendance` (Chốt điểm danh)
    - `2. Day 1 (28/05): AI & LLM Foundation` (Đã khóa)
    - `3. Day 2 (29/05): Xác định Bài toán cho AI` (Đã khóa)
    - `4. Day 3 (01/06): Design Pattern ReAct (Kiến thức nền tảng)` (Đã khóa)
    - `5. Day 4 (02/06): Prompt Engineering & Tool Calling` (Đã khóa)
    - `6. Day 5 (03/06): AI Product Thinking & Requirements` (**Active** - Cho phép click để load file slide PDF `day05-lecture-slides-batch02.pdf` ở cột giữa)
    - `7. Day 6 (04/06): AI Product Prototype & Demo` (Đã khóa)
    - `8. Day 7: Data Foundations (Embedding, Vector DB)` (Hiển thị nhãn `soon` màu xám)
    - `9. Day 8: RAG Pipeline - Truy xuất & Sinh câu trả lời` (Hiển thị nhãn `soon` màu xám)
  - Phía dưới cùng tích hợp liên kết ẩn truy cập nhanh trang Admin `/u/0/students` cho mentor.
- Di chuyển `ChatPanelInteractive` sang làm cột bên phải ngoài cùng (chiều rộng cố định hoặc có thanh resize từ 390px - 450px).

## Related Files
- [MODIFY] [agent-trace-viewer.tsx](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/codebase/frontend/components/agent-trace-viewer.tsx)
- [MODIFY] [sidebar-unified.tsx](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/codebase/frontend/components/sidebar-unified.tsx)
- [MODIFY] [chat-panel-interactive.tsx](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/codebase/frontend/components/chat-panel-interactive.tsx)

## Implementation Steps
1. **Sửa `agent-trace-viewer.tsx`**:
   - Loại bỏ `Header` component.
   - Định nghĩa layout flex ngang chứa 3 cột: Cột 1 (Sidebar), Cột 2 (PDF Viewer), Cột 3 (Chat Panel).
2. **Sửa `sidebar-unified.tsx`**:
   - Thay đổi giao diện visual: Background xanh đậm/xanh dương (ví dụ `#1e40af` hoặc `#172554`), thanh tiến trình `11%`, list các Day từ 1 đến 9 bám theo UI mẫu.
   - Khóa các Day khác bằng cách kiểm tra index và set opacity, vô hiệu hóa pointer-events. Chỉ Day 5 (index = 5) cho phép click để load slide.
3. **Sửa `chat-panel-interactive.tsx`**:
   - Chỉnh lại CSS khung chat chạy dọc để hoạt động mượt mà trong cột hẹp bên phải (~390px).
   - Thay đổi các placeholder và tiêu đề sang Student AI Tutor.

## Todo List
- [ ] Xóa Header chiếm chỗ trong `agent-trace-viewer.tsx`
- [ ] Thiết kế lại `SidebarUnified` thành Lộ trình học LMS theo nhãn ảnh chụp (chỉ active Day 5)
- [ ] Cấu hình ChatPanelInteractive hiển thị dọc cột bên phải

## Success Criteria
- Sidebar cột trái khớp 90% giao diện LMS thật trong ảnh mẫu (Đúng màu, tiêu đề, tiến trình, 3 tab và danh sách Day).
- Khung chat hiển thị thẳng đứng bên phải màn hình không bị tràn.
- Không còn Header đen phía trên cùng.
