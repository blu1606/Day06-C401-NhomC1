# Plan: GapTutor AI Tutor Frontend Adjustments

Dự án AI Product Hackathon - Cải tiến giao diện frontend thành mô phỏng hệ thống học tập LMS tích hợp AI Tutor:
- **Cột trái**: Lộ trình bài học (chỉ cho phép truy cập Day 5 để đọc slide PDF).
- **Cột giữa**: Trình hiển thị slide PDF bài giảng Day 5 kèm nút điều khiển trang.
- **Cột phải**: Khung chat hỏi đáp AI Tutor và Telemetry (click citation nhảy trang slide ở cột giữa, tra cứu từ `day05_ai_tutor_slide_sources.json`).

## Đường dẫn các file Phase chi tiết

- [Phase 1: Chuẩn bị Mock Data & Cấu trúc Traces](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/plans/20260604-1030-gaptutor-ai-tutor-implementation/phase-01-mock-data-and-api.md)
- [Phase 2: Tùy biến LMS Sidebar, Bỏ Header & Di chuyển Chat sang Cột phải](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/plans/20260604-1030-gaptutor-ai-tutor-implementation/phase-02-ui-adaption.md)
- [Phase 3: Trình xem PDF ở giữa & Nhảy trang](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/plans/20260604-1030-gaptutor-ai-tutor-implementation/phase-03-telemetry-and-feedback.md)
- [Phase 4: Xử lý Mất kết nối Backend (Offline Fallback)](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/plans/20260604-1030-gaptutor-ai-tutor-implementation/phase-04-backend-disconnect-fallback.md)

## Danh sách công việc chính

- [ ] **Phase 1: Mock Data & Traces**
  - [ ] Sử dụng trực tiếp `day05_ai_tutor_slide_sources.json` làm nguồn tri thức trong `codebase/frontend/data/`
  - [ ] Copy `day05-lecture-slides-batch02.pdf` vào `public/`
  - [ ] Định nghĩa các kịch bản traces RAG mới trong `mock-traces.ts`
- [ ] **Phase 2: Giao diện LMS Sidebar & Chat Cột phải**
  - [ ] Loại bỏ Header panel phía trên ở trang Chat và Admin
  - [ ] Thiết kế lại `SidebarUnified` thành Lộ trình học LMS (chỉ active Day 5)
  - [ ] Di chuyển `ChatPanelInteractive` thành cột bên phải
- [ ] **Phase 3: Trình xem PDF ở giữa & Nhảy trang**
  - [ ] Tạo mới component `pdf-viewer-central.tsx` hiển thị ở giữa màn hình
  - [ ] Liên kết sự kiện click citation ở chat để tự động cập nhật trang slide PDF
  - [ ] Tích hợp `StudentDashboard` vào trang quản lý của Mentor
- [ ] **Phase 4: Xử lý Mất kết nối Backend (Offline Fallback)**
  - [ ] Tích hợp `AbortController` có timeout `5000ms` và bắt lỗi kết nối khi fetch API `/api/diagnose`
  - [ ] Ánh xạ các câu hỏi thường gặp sang slide Day 5 offline trong hàm `switchToOfflineFallback`
  - [ ] Hiển thị thông báo trạng thái ngoại tuyến `ℹ️ Phản hồi ngoại tuyến` dưới tin nhắn chat và banner màu vàng gợi ý câu hỏi khi mất kết nối

## Key Dependencies

- Dữ liệu slide chính thức làm RAG KB: `day05_ai_tutor_slide_sources.json`
- File slide bài giảng: `day05-lecture-slides-batch02.pdf`
- Mẫu component dashboard học viên có sẵn: `student-dashboard.tsx`
