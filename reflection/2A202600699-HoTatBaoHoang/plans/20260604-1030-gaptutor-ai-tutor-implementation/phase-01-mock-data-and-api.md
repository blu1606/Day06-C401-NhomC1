# Phase 1: Chuẩn bị Mock Data & Cấu trúc Traces

## Context Links
- [day05_ai_tutor_slide_sources.json](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/codebase/frontend/data/day05_ai_tutor_slide_sources.json)
- [mock-traces.ts](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/codebase/frontend/lib/mock-traces.ts)

## Overview
- **Priority:** High
- **Status:** Pending
- **Description:** Sử dụng dữ liệu slide Day 05 có sẵn, chuẩn bị file PDF bài giảng và định nghĩa cấu trúc traces mới mô phỏng quá trình tìm kiếm ngữ cảnh, tính toán độ chính xác và đưa ra câu trả lời cho học viên.

## Requirements
- Sử dụng trực tiếp file dữ liệu slide [day05_ai_tutor_slide_sources.json](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/codebase/frontend/data/day05_ai_tutor_slide_sources.json) đã được chuẩn bị sẵn.
- Copy file [day05-lecture-slides-batch02.pdf](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/codebase/frontend/day05-lecture-slides-batch02.pdf) vào thư mục `public/` của Next.js để có thể hiển thị.
- Cập nhật file `mock-traces.ts` chứa các trace mô phỏng khớp với các câu hỏi học sinh về kiến thức Day 05 (ví dụ: uncertainty, error routing, automation/augmentation, failure modes, etc.).

## Related Files
- [NEW] [day05-lecture-slides-batch02.pdf](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/codebase/frontend/public/day05-lecture-slides-batch02.pdf)
- [MODIFY] [mock-traces.ts](file:///d:/CODE/AITHUCCHIEN/LABS/Batch02-Day06-AI-Product-Hackathon/codebase/frontend/lib/mock-traces.ts)

## Implementation Steps
1. Xác minh file `day05_ai_tutor_slide_sources.json` tồn tại đầy đủ trong `codebase/frontend/data/`.
2. Sao chép file PDF slide bài giảng `codebase/frontend/day05-lecture-slides-batch02.pdf` vào thư mục `codebase/frontend/public/day05-lecture-slides-batch02.pdf`.
3. Chỉnh sửa `mock-traces.ts` để thay thế các kịch bản cũ thành kịch bản chẩn đoán hỏi đáp kiến thức bài học Day 5:
   - Trace 1: `success-uncertainty` - Trả lời câu hỏi về sự bất định trong AI product, dẫn nguồn slide 9.
   - Trace 2: `success-error-routing` - Trả lời câu hỏi về Error Routing, dẫn nguồn slide 12.
   - Trace 3: `low-confidence-out-of-bounds` - Xử lý câu hỏi ngoài lề (ví dụ: xin đáp án lab hoặc code hộ), trả về thông báo từ chối lịch sự và gợi ý hint (theo slide 30 Graceful Failure).
   - Trace 4: `security-blocked` - Giữ nguyên cảnh báo Prompt Injection.

## Todo List
- [ ] Xác minh file `day05_ai_tutor_slide_sources.json` khả dụng trong data
- [ ] Sao chép file `day05-lecture-slides-batch02.pdf` sang thư mục `public/`
- [ ] Cập nhật `mock-traces.ts` với các kịch bản traces Day 5 thực tế

## Success Criteria
- File PDF có thể truy cập qua URL `/day05-lecture-slides-batch02.pdf`.
- Mã nguồn frontend biên dịch thành công không lỗi type do thay đổi trace structure.
