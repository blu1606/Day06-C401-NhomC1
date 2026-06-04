# AI Product Flow Report

## Case Study: Vietnam Airlines NEO Chatbot

---

# 1. Chọn một app để dùng thử

## Ứng dụng được chọn

### Vietnam Airlines NEO

Link:
https://www.vietnamairlines.com/sg/en/support/chatbot

## Mô tả sản phẩm

NEO là chatbot AI của Vietnam Airlines hỗ trợ:

* đổi vé
* hành lý
* refund
* booking
* hỗ trợ FAQ chuyến bay

AI hoạt động như một virtual assistant hỗ trợ khách hàng 24/7.

---

# 2. Dùng thử sản phẩm thật

## Query 1

> “I want to change my flight”

### Kỳ vọng của user

User muốn:

* đổi vé nhanh
* được hướng dẫn step-by-step
* biết ngay cần làm gì tiếp theo

---

### Kết quả thực tế

NEO:

* phân biệt voluntary / involuntary change
* hiển thị nhiều rule
* đưa policy dài
* giải thích nhiều điều kiện

---

## Query 2

> “How many kg baggage can I bring?”

### Kỳ vọng của user

User muốn:

* biết số kg được mang
* có câu trả lời nhanh

---

### Kết quả thực tế

NEO:

* hỏi thêm route và fare type
* sau đó hiển thị nhiều policy:

  * domestic
  * international
  * infant
  * membership benefits

---

## Query 3

> “I missed my flight, what should I do?”

### Kỳ vọng của user

User đang:

* stress
* cần xử lý nhanh
* muốn biết action tiếp theo

---

### Kết quả thực tế

NEO:

* trả về no-show policy
* refund conditions
* nhiều timing rules

---

# 3. Vẽ flow hiện tại (As-Is)

# Flow hiện tại

## Step 1

User nhập câu hỏi

↓

## Step 2

AI detect intent

Ví dụ:

* đổi vé
* baggage
* missed flight

↓

## Step 3

AI trả lời bằng:

* FAQ
* policy
* rules
* exception

↓

## Step 4

User tự:

* đọc
* suy luận
* tìm next action

---

# 4. Đánh dấu path yếu nhất

# Path yếu nhất:

## “Information overload”

---

## Vấn đề

Khi user hỏi:

> “I want to change my flight”

AI trả lời:

* quá dài
* quá nhiều policy
* nhiều exception
* nhiều legal condition

---

## User bị kẹt ở đâu?

User bị kẹt ở:

* xác định bước tiếp theo
* tìm action cần làm
* hiểu policy dài

Thay vì:

> được dẫn flow từng bước.

---

# 5. Failure Mode

## Failure Statement

Nếu user hỏi một task cần xử lý nhanh,
AI có thể:

* dump quá nhiều policy
* trả lời như FAQ engine
* không ưu tiên action flow

Hậu quả là:

* tăng cognitive load
* user khó hoàn thành task
* giảm trust
* tăng abandon rate

---

# 6. Sửa một path yếu nhất (To-Be)

# Product Decision

## “AI phải ưu tiên action flow trước policy explanation.”

---

# Flow mới đề xuất

## Current Flow (As-Is)

User:

> “I want to change my flight”

↓

AI:

* hiển thị nhiều policy
* giải thích điều kiện
* hiển thị exception

↓

User tự đọc và tự xử lý

---

## Improved Flow (To-Be)

User:

> “I want to change my flight”

↓

AI:

> “Please provide your booking code.”

↓

AI:

> “Do you want to change date, time, or destination?”

↓

AI:

* hiển thị đúng action
* chỉ hiện policy liên quan

↓

Nếu cần:

* show detailed policy
* handoff sang human support

---

# 7. Cách prototype xử lý

Prototype sẽ xử lý bằng:

## 1. Ask Again

AI hỏi thêm thông tin thay vì dump policy.

---

## 2. Progressive Disclosure

Chỉ hiển thị information cần thiết ở từng step.

---

## 3. Action-Oriented UX

Ưu tiên:

* next action
* CTA
* task completion

---

## 4. Human Handoff

Nếu:

* urgency cao
* user stress
* flow fail

→ chuyển sang support agent.

---

# 8. Kết luận

Vietnam Airlines NEO có:

* intent detection khá tốt
* coverage nghiệp vụ rộng
* clarification cơ bản

Tuy nhiên,
path yếu lớn nhất hiện tại là:

## phản hồi quá dài và thiên về policy.

AI hoạt động giống:

* FAQ system
  hơn là:
* conversational assistant.

Giải pháp đề xuất:

* chuyển sang step-by-step conversational flow
* ưu tiên action trước
* chỉ hiển thị policy khi cần

Điều này giúp:

* giảm friction
* tăng completion rate
* tăng trust
* cải thiện trải nghiệm AI product tổng thể.

---

# 9. Một câu Product Decision

> “Một AI assistant tốt không phải AI trả lời nhiều nhất, mà là AI giúp user hoàn thành task nhanh nhất.”
