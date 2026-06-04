Presentation Flow — AI Tutor LMS (Learning Assistant)
Slide 1 — Title / Team Intro
Nội dung
Team name: C1
Track: Learning Web
Product: AI Tutor for LMS
Members: Hồ Tất Bảo Hoàng - 2A202600699
         Le Duc Viet-2A202600959
         Nguyễn Vũ Trọng - 2A202600960
         Nguyễn Phương Nam - 2A202600962
         Bùi Văn Tuân - 2A202601006
         Đào Tất Thắng - 2A202600540
Message chính

“Chúng em build một AI Tutor giúp học viên AI20K hỏi lại nội dung workshop/lab dựa trên slide có citation.”

Slide 2 — Problem / Pain Point
Pain thực tế
Nội dung
Khóa học AI thực chiến có:
~500 học viên
~167 teams
nhiều workshop/lab/gate
mentor không thể support liên tục
Quote evidence
“Em không biết bắt đầu debug RAG pipeline từ đâu.”
“Team bị kẹt gate nhưng mentor chưa kịp xem.”
“Nhiều bạn hỏi lại cùng một lỗi về chunking/tool calling/deploy.”
Message chính

“Người học thường bị mất context sau workshop và không biết hỏi lại ở đâu.”

Slide 3 — Evidence
Self-use evidence
Nội dung
Team tự thử học lại workshop RAG
Khi quên:
chunking
retrieval
tool calling
Phải:
search nhiều nơi
đọc lại slide thủ công
hỏi mentor
Screenshot gợi ý
LMS
slide workshop
Discord/chat mentor
Google Form survey
Message chính

“Pain xảy ra ngay cả với chính team build.”

Slide 4 — Insight
Surface problem vs deeper need
Surface problem

“Người học quên kiến thức.”

Deeper need

“Người học cần:

recall nhanh
grounded answer
citation để trust
xác định mình đang học ở slide nào”
Message chính

“User không chỉ cần chatbot trả lời — họ cần AI có căn cứ và giúp recover context.”

Slide 5 — Opportunity Statement
Opportunity
Nội dung

AI có thể:

retrieve đúng slide
summarize lời giảng
giải thích lại dễ hiểu
đưa citation để verify
Format

“For students learning AI workshops,
AI augments knowledge recall and workshop navigation,
by retrieving grounded answers from workshop slides.”

Message chính

“Đây là bài toán augmentation, không phải fully autonomous AI.”

Slide 6 — Build Slice
Build slice
User

Sinh viên đang học workshop RAG Pipeline.

Task

Hỏi:
“Chunking ảnh hưởng thế nào đến retrieval quality?”

AI Decision
detect knowledge question
retrieve relevant slide
grounded explanation mode
Output
câu trả lời ngắn
ví dụ nhỏ
citation:
workshop
slide
source excerpt
Message chính

“Chúng em không build cả LMS assistant — chỉ build một workflow AI hẹp nhưng measurable.”

Slide 7 — Product Flow
Demo flow
Flow
User hỏi câu hỏi workshop
AI retrieve source liên quan
AI generate grounded answer
Citation hiển thị slide/source
User verify lại kiến thức
Có thể show
architecture đơn giản
RAG flow diagram
Message chính

“Trust đến từ retrieval + citation.”

Slide 8 — Auto vs Aug
Decision boundary
AI làm
retrieve
summarize
explain
cite source
Human giữ quyền
quyết định final understanding
verify source
tự làm lab/gate
Message chính

“AI hỗ trợ học, không làm hộ bài.”

Slide 9 — Failure Mode
Most dangerous failure
Failure

AI hallucinate hoặc cite sai slide.

Mitigation
only answer from dataset
refusal nếu không có source
show citation
low-confidence clarification
Example

“Không tìm thấy thông tin này trong workshop.”

Message chính

“Trust quan trọng hơn trả lời mọi thứ.”


Slide 10 — Closing
Final message

“AI Tutor không thay mentor.
Nó giúp học viên recover context nhanh hơn,
giảm mentor overload,
và học có grounded citation thay vì hallucination.”