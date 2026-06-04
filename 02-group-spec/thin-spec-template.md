# Template — Thin SPEC Cuối Day 05

Thin SPEC không phải PRD đầy đủ. Đây là bản cam kết đủ rõ để sáng Day 06 nhóm build ngay.

## 1. Track, product/app và user

**Track:** Learning OS(Vin AI thực chiến)
**Product/app thật:**  LMS hiện tại
**User cụ thể:** Học viên khóa học AI thực chiến
**Nhóm có phải user thật không? Nếu không, khác ở đâu?**  

## 2. Evidence summary

| Evidence | Nguồn | User/pain nói lên điều gì? | SPEC phải đổi gì? | 
|---|---|---|---|
|File mp3 phỏng vấn được summary bằng NoteBookLLM|https://notebooklm.google.com/notebook/f131229a-bf22-4f17-a679-0ea7e931380a  |  |  |
|Form phỏng vấn |https://docs.google.com/spreadsheets/d/1flzTMQbGz8KqoA-KAIFcDhrn3QQ-wwffaYcW9MV02AY/edit?usp=sharing  |  |  |
|  |  |  |  |

## 3. Pain statement
Học viên trong lúc nghe giảng viên giảng có chỗ nào muôn giải đáp nhanh cần một AI tutor có thể giải thích thắc mắc bằng ngôn ngữ dễ hiểu, đúng trình độ, và chỉ dựa trên tài liệu chính thức. Điểm đáng sửa là hiện tại sinh viên có thể hỏi rời rạc trên group, tự search nguồn ngoài hoặc dùng AI chung không kiểm chứng, dễ nhận câu trả lời sai hoặc không bám nội dung khóa học.


## 4. Build slice

```text
Một user: sinh viên đang học Workshop RAG Pipeline. 
Một task: hỏi “chunking ảnh hưởng thế nào đến retrieval quality?” 
Một AI decision: xác định đây là câu hỏi kiến thức trong phạm vi tài liệu, chọn mode Giải thích. 
Một output: câu trả lời ngắn, dễ hiểu, có ví dụ nhỏ, kèm citation tên tài liệu + slide/section + đoạn trích nguồn ngắn.
```

## 5. Auto/Aug decision

Chọn một:

- [ ] **Augmentation:** AI gợi ý/draft/phân loại, user quyết cuối.
- [ ] **Conditional automation:** AI tự làm trong case hẹp; case mơ hồ/rủi ro chuyển người.
- [X] **Automation:** AI tự quyết và tự hành động.

AI tự động tìm tài liệu liên quan, tóm tắt và giải thích theo ngôn ngữ của sinh viên, kèm citation. AI không tự bịa khi không có nguồn, không trả lời ngoài phạm vi tài liệu chính thức. Human giữ quyền ở phần quản trị: BTC/Admin upload/publish tài liệu, mentor/BTC review feedback nếu sinh viên báo citation sai hoặc câu trả lời chưa rõ.

**Lý do chọn:**  
**Human role:** reviewer / decider / trainer / rescuer / none  

## 6. Four paths

Happy: AI tìm được nguồn đúng, giải thích rõ, có citation và sinh viên hiểu tiếp bài. 
Low-confidence: AI không đủ tự tin về nguồn nên nói chưa tìm thấy trong tài liệu chính thức và gợi ý sinh viên hỏi lại cụ thể hơn. Failure: AI trả lời sai nguồn hoặc citation lệch; sinh viên/mentor flag câu trả lời. 
Correction: hệ thống ghi feedback, đưa câu hỏi vào golden test, admin/mentor chỉnh tài liệu, chunking, prompt hoặc policy.

## 7. Failure mode nguy hiểm nhất

```text
Nếu user [hỏi kiến thức chưa nắm rõ],
AI có thể [giải thích sai nhưng trình bày tự tin, hoặc đưa citation không liên quan khiến sinh viên học sai],
hậu quả là [impact].
Prototype sẽ xử lý bằng [Prototype xử lý bằng citation bắt buộc, chỉ trả lời khi retrieval đủ tin cậy, hiển thị nguồn rõ, có nút feedback “citation sai/chưa rõ”,và golden test cho các câu hỏi trọng yếu của từng workshop.].
Owner kiểm thử path này là [Lê Đức Việt].
```

## 8. Owner plan cho sáng Day 06

| Thành viên | Việc phụ trách | Bằng chứng cần có trong repo |
|Nguyễn Phương Nam|Viết thin spec, chuẩn bị mock data, docs manager|commit ở file thin-spec|
|Lê Đức Việt | Research / evidence | Form thu nhập evidence |
|Nguyễn Phương Nam | SPEC |  |
|Bùi Văn Tuân, Nguyễn Vũ Trọng, Đào Tất Thắng, Hồ Tất Bảo Hoàng  | Prototype |Code AI tool, UI, BE  |
|Lê Đức Việt | Test / failure path |  |
|Hồ Tất Bảo Hoàng  | Demo script / repo |  |
