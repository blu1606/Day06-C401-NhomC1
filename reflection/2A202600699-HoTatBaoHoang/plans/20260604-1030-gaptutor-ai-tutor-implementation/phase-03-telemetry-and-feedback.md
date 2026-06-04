# Phase 3: Tạo Trình Xem PDF Cột Giữa & Liên kết Nhảy Trang

## Context Links
- [pdf-viewer-central.tsx](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/codebase/frontend/components/pdf-viewer-central.tsx)
- [agent-trace-viewer.tsx](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/codebase/frontend/components/agent-trace-viewer.tsx)
- [chat-panel-interactive.tsx](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/codebase/frontend/components/chat-panel-interactive.tsx)
- [page.tsx](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/codebase/frontend/app/u/0/students/page.tsx)

## Overview
- **Priority:** High
- **Status:** Pending
- **Description:** Tạo mới trình hiển thị PDF ở cột giữa màn hình thay cho panel telemetry cũ. Đồng bộ hóa sự kiện click citation từ chat để tự động cập nhật trang của tài liệu PDF. Tích hợp StudentDashboard vào trang quản lý học viên của Mentor.

## Requirements
- Xóa Header trên trang quản lý `/u/0/students` (`page.tsx`) để đồng bộ không gian hiển thị rộng rãi.
- Tạo mới component `pdf-viewer-central.tsx` nhúng file `/day05-lecture-slides-batch02.pdf` ở cột giữa:
  - Có thanh bar điều khiển trang ở trên cùng chứa: `< previous` (quay lại trang trước) và `next >` (sang trang tiếp theo) kèm thông số trang hiện tại.
  - Sử dụng thẻ `<iframe>` hoặc `<object>` để load file PDF tĩnh từ `/public/day05-lecture-slides-batch02.pdf#page=N`.
- Liên kết sự kiện click citation từ `ChatPanelInteractive`:
  - Khi học viên click nhãn trích dẫn (ví dụ: *slide 5*), state `activeSlidePage` ở component cha `AgentTraceViewer` sẽ cập nhật thành `5`.
  - Cột ở giữa nhận state mới và reload lại iframe PDF nhảy tới trang 5.
- Cập nhật trang quản lý `/u/0/students` để khi click tab `student-analytics` sẽ hiển thị component `StudentDashboard`.

## Related Files
- [NEW] [pdf-viewer-central.tsx](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/codebase/frontend/components/pdf-viewer-central.tsx)
- [MODIFY] [agent-trace-viewer.tsx](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/codebase/frontend/components/agent-trace-viewer.tsx)
- [MODIFY] [page.tsx](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/codebase/frontend/app/u/0/students/page.tsx)

## Implementation Steps
1. **Tạo `pdf-viewer-central.tsx`**:
   - Sử dụng React state để quản lý số trang và cho phép tăng/giảm qua nút chuyển trang.
   - Trả về thẻ iframe load file `/day05-lecture-slides-batch02.pdf#page=N` có style width/height 100%.
2. **Cập nhật `agent-trace-viewer.tsx`**:
   - Khai báo state `activeSlidePage` và truyền hàm callback `setActiveSlidePage` sang `ChatPanelInteractive`.
   - Render `<PdfViewerCentral activePage={activeSlidePage} onChangePage={setActiveSlidePage} />` ở cột chính giữa.
3. **Cập nhật `page.tsx`**:
   - Xóa bỏ thẻ `<header>` và responsive padding.
   - Thêm tab `student-analytics` hiển thị biểu đồ cohort và các nhóm học sinh yếu.

## Todo List
- [ ] Tạo mới component `pdf-viewer-central.tsx` hiển thị ở cột giữa
- [ ] Tích hợp trình xem PDF vào layout của `agent-trace-viewer.tsx`
- [ ] Liên kết sự kiện click citation để cập nhật trang slide PDF
- [ ] Đồng bộ hóa hiển thị StudentDashboard ở trang quản trị học sinh

## Success Criteria
- Slide PDF bài giảng được hiển thị trực tiếp ở giữa màn hình.
- Nút bấm `< previous` và `next >` chuyển slide bình thường.
- Click citation trong khung chat cột phải khiến PDF cột giữa tự động nhảy trang chính xác.
