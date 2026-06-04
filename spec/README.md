# AI Tutor for LMS — Product SPEC

## Team Information
* **Team:** C1
* **Track:** Learning Web
* **Product:** AI Tutor for LMS
* **Members:** Hồ Tất Bảo Hoàng, Lê Đức Việt, Nguyễn Vũ Trọng, Nguyễn Phương Nam

---

## 1. Bằng chứng (Evidence)

### 1.1 Trải nghiệm trực tiếp (Self-use Evidence)
Nhóm tự sử dụng các workshop AI và LMS hiện tại để ghi lại các điểm gãy trong quá trình học.

* **Observation 1 — Người học bị kẹt vì quá nhiều thuật ngữ mới:** Trong workshop về RAG pipeline và AI Agent, nhóm gặp khó khăn khi gặp các khái niệm như *embedding, vector database, retrieval, agent loop, tool calling*. Người học thường phải tự Google từng khái niệm, mất flow học, chuyển tab liên tục và quên kiến thức cũ sau vài phút.
* **Observation 2 — LMS hiện tại chỉ lưu tài liệu, không hỗ trợ hiểu bài:** Các LMS phổ biến chỉ hiển thị PDF/video, không giải thích theo ngữ cảnh bài học và không biết học viên đang kẹt ở đâu. Chatbot chung chung thường trả lời quá rộng hoặc lệch nội dung workshop.
* **Observation 3 — Người học mới ngại đặt câu hỏi:** Trong workshop thật, nhiều người không muốn ngắt lời mentor hoặc sợ hỏi “câu cơ bản”, dẫn tới bị tụt khỏi flow bài học. AI tutor có thể đóng vai trò “mentor phụ” để hỏi nhanh ngay trong lúc học.

### 1.2 Nguồn bên ngoài (External Evidence)
Nhiều review của người học trên các nền tảng LMS và course AI phản ánh:
> “The content is good but difficult to follow without guidance.”
> “I keep getting lost between concepts.”
> “I spend more time searching terms than actually learning.”

Các discussion trên Reddit và Discord học AI cũng cho thấy beginner bị overwhelm bởi thuật ngữ, learning flow bị đứt đoạn và chatbot hiện tại trả lời thiếu context khóa học.

### 1.3 Giả định (Assumptions)
Các giả định nhóm CHƯA xác minh đầy đủ:
* Người học sẽ sử dụng AI tutor liên tục trong suốt bài học thay vì chỉ vài lần.
* Người học tin AI đủ để hỏi các câu “ngớ ngẩn”.
* Việc contextualize bằng tài liệu khóa học sẽ giúp câu trả lời tốt hơn chatbot chung.

---

## 2. Lát cắt để build (Thin Slice)

**Một câu mô tả lát cắt:** "Một học viên đang xem bài học AI trong LMS, highlight một thuật ngữ khó hiểu, AI giải thích theo đúng context bài học và đưa ví dụ đơn giản để người học tiếp tục flow học."

* **User:** Người mới học AI / workshop AI.
* **Job to be done:** Hiểu nhanh khái niệm đang học mà không phải rời khỏi LMS.
* **AI Decision:** AI quyết định khái niệm nào cần giải thích, giải thích ở mức beginner và ví dụ nào phù hợp context bài học.
* **Output:** Giải thích ngắn gọn, ví dụ dễ hiểu, related concepts và suggested next step.

---

## 3. AI Product Canvas

| Ô | Chi tiết quyết định của nhóm |
|---|-----------------------------|
| **Value** (Giá trị) | **Dành cho ai:** Beginner học AI, sinh viên workshop, người self-learning.<br>**Họ đau ở đâu:** Quá tải thuật ngữ mới, mất flow khi search ngoài, thiếu mentor hỗ trợ liên tục.<br>**AI giải quyết:** Giải thích theo ngữ cảnh bài học ngay trong LMS, cá nhân hóa mức độ, giảm cognitive load. |
| **Trust** (Niềm tin) | **Cách nhận biết sai:** Giải thích chung chung, không liên quan bài học, ví dụ vô lý.<br>**Xử lý/Hoàn tác:** Xem source context AI đã dùng, chỉnh sửa prompt hỏi lại, chọn “Không đúng” (dislike), hoặc chuyển sang hỏi mentor thật. |
| **Feasibility** (Khả thi)| **Đáng build:** Dùng OpenAI API, RAG đơn giản với context retrieval từ tài liệu khóa học.<br>**Rủi ro lớn nhất:** Hallucination, sai context retrieval, tốn token.<br>**Ngưỡng dừng (Stop condition):** Nếu retrieval không cải thiện được chất lượng, latency quá cao hoặc tốn kém chi phí $\rightarrow$ Fallback sang context injection đơn giản. |
| **Tín hiệu học** | Khi user chỉnh sửa câu hỏi, dislike answer, chọn câu trả lời khác $\rightarrow$ Hệ thống log lại prompt, retrieved chunks, final response. Dữ liệu này giúp cải thiện retrieval, tạo eval set và tinh chỉnh prompt. |

---

## 4. Tăng năng lực hay tự động hóa (Augment hay Automate)

**Quyết định: AUGMENT (Tăng năng lực)**

* **AI làm gì:** AI chỉ gợi ý, giải thích và đóng vai trò trợ giảng. KHÔNG tự quyết định thay người học.
* **Con người làm gì:** Vẫn tự học, tự phán đoán kiến thức đúng/sai, tự quyết định học tiếp hay hỏi lại mentor.
* **Lý do:** Học tập (learning) là hoạt động cần hiểu bản chất, rất khó hoàn tác nếu hình thành tư duy (mental model) sai lệch từ đầu. Việc sai kiến thức ảnh hưởng lớn đến các concept phía sau. Vì vậy AI chỉ dừng ở mức "learning assistant" hỗ trợ, con người giữ quyền quyết định tuyệt đối.

---

## 5. Bốn đường đi của trải nghiệm (Four Paths)

| Đường đi | Câu hỏi | Trải nghiệm / Cách xử lý của Prototype |
|----------|---------|------------------|
| **Đường thuận** (Happy Path) | AI đúng và tự tin — người dùng thấy gì? | User highlight term $\rightarrow$ AI hiện explanation card $\rightarrow$ User hiểu ngay và tiếp tục learning flow. |
| **Khi AI không chắc** (Uncertain)| AI lưỡng lự — có hỏi lại không? | AI thiếu context hoặc query mơ hồ $\rightarrow$ Hệ thống đưa ra 2-3 ý nghĩa có thể có (possible meanings) và yêu cầu user chọn thêm context. |
| **Khi AI sai** (AI Wrong) | Kết quả sai — người dùng gỡ ra thế nào? | User ấn dislike, edit lại prompt, regenerate câu trả lời, hoặc mở original source để tự đọc. Có thể fallback sang mentor/manual docs. |
| **Khi người dùng sửa** (Correction)| Người dùng chỉnh lại — dữ liệu đi về đâu? | Lưu lại correction log, đánh dấu bản retrieval bị fail và đưa vào tập dữ liệu đánh giá (eval dataset). |

---

## 6. Những kiểu lỗi đáng lo nhất (Most Dangerous Failure Modes)

1. **Failure 1 — Hallucinated Explanation:** 
   * *Khi nào:* AI thiếu context hoặc retrieval lấy sai tài liệu.
   * *Hậu quả:* Người học tiếp thu sai kiến thức.
   * *Cách xử lý:* Luôn show source chunk kèm theo (Citation), thêm hint cảnh báo confidence, cho phép regenerate hoặc fallback hỏi mentor.
2. **Failure 2 — Over-simplification:**
   * *Khi nào:* AI cố gắng giải thích quá căn bản (beginner).
   * *Hậu quả:* Mất đi độ chính xác kỹ thuật (technical accuracy).
   * *Cách xử lý:* Cung cấp nút switch level: Beginner / Intermediate / Technical mode.
3. **Failure 3 — Wrong Context Retrieval:**
   * *Khi nào:* Retriever lấy nhầm đoạn văn bản.
   * *Hậu quả:* AI trả lời hoàn toàn lệch bài học.
   * *Cách xử lý:* Hiển thị minh bạch "retrieved context", áp dụng semantic chunking tốt hơn, và tuning thông số top-k retrieval.

---

## 7. Kế hoạch kiểm thử và bằng chứng Demo

* **Demo Case 1 — Happy Path:** 
  * *Input:* “What is embedding in this RAG lesson?”
  * *Output kỳ vọng:* AI đưa ra lời giải thích đơn giản, ví dụ cụ thể về AI và liệt kê các related concepts đúng ngữ cảnh.
* **Demo Case 2 — Hard Case:** 
  * *Output kỳ vọng:* AI tự tin đưa ra lời giải thích đơn giản, kèm ví dụ cụ thể về AI và liệt kê các related concepts đúng ngữ cảnh bài học.
* **Demo Case 2 — AI Uncertain (Khi AI không chắc chắn):** 
  * *Input:* “What is memory?” (Từ có nhiều nghĩa: AI memory, RAM, conversation memory).
  * *Output kỳ vọng:* AI nhận diện sự mơ hồ $\rightarrow$ Không tự đoán mà hỏi lại clarify hoặc liệt kê các cách hiểu khác nhau để user tự chọn ngữ cảnh.
* **Demo Case 3 — AI Wrong (Khi AI sai / Trả lời lệch nguồn):** 
  * *Input:* User hỏi một khái niệm khó, AI trả lời nhưng trích dẫn sai slide hoặc giải thích lạc đề.
  * *Output kỳ vọng:* User phát hiện sai sót nhờ xem Citation bị lệch. User ấn "Dislike" (Không đúng). Hệ thống ghi nhận phản hồi lỗi, dừng luồng AI và gợi ý Fallback sang hỏi Mentor thật.
* **Demo Case 4 — User Correction (Khi người dùng sửa):** 
  * *Input:* User nhận được câu trả lời giải thích "Agent loop" nhưng thấy quá sơ sài.
  * *Output kỳ vọng:* User chủ động edit lại prompt (Ví dụ: "Hãy giải thích chi tiết hơn bằng code Python trong slide 15") và regenerate answer. Hành vi sửa prompt + dislike log được hệ thống tự động lưu lại vào file để bổ sung cho tập Golden Test sau này.
---

## 8. Phân công (Team Responsibilities)

* **Hồ Tất Bảo Hoàng:** Frontend UI, LMS integration.
* **Lê Đức Việt:** Prompt engineering,promp testing, Evaluation cases.
* **Nguyễn Vũ Trọng:** Backend API, Retrieval pipeline.
* **Nguyễn Phương Nam:** Demo script, Product canvas, Evidence collection.
* **Đào Tất Thắng:** 
