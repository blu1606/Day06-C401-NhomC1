# Tổng quan công cụ LMS AI Learning Assistant

Tài liệu này mô tả các tool trong `codebase/ai/tools` cho prototype LMS AI
Learning Assistant. Mục tiêu của nhóm tool là giúp AI Tutor trả lời câu hỏi học
tập dựa trên slide/tài liệu chính thức, có citation, có fallback khi không đủ
tự tin, và có feedback loop để ghi nhận lỗi trả lời hoặc citation.

Luồng sử dụng chính:

```text
Student question
-> retrieve_slide_sources
-> classify_question_scope
-> generate_grounded_answer hoặc handle_low_confidence_answer
-> submit_answer_feedback
```

## Nguồn dữ liệu

Nhóm tool LMS assistant đọc mock source từ các file JSON local:

- `02-group-spec/data/mock_ai_tutor_slide_sources.json`
- `02-group-spec/data/day05_ai_tutor_slide_sources.json`
- `codebase/data/day05_ai_tutor_slide_sources.json`
- `codebase/frontend/data/slide_sources.json`
- `codebase/frontend/data/day05_ai_tutor_slide_sources.json`

Quy tắc quan trọng:

- Tool student-facing `retrieve_slide_sources` chỉ dùng source có
  `status = "published"`.
- Source `draft` không được dùng để trả lời học viên.
- Source `draft` vẫn có thể xem qua `list_workshop_sources(status="draft")`
  để mentor/admin review.
- Các source trùng `source_id` được dedupe, giữ record đầu tiên đọc được.

## Registry

Các tool đã được đăng ký trong `codebase/ai/tools/__init__.py`:

- `explain`
- `summarize`
- `retrieve_slide_sources`
- `classify_question_scope`
- `generate_grounded_answer`
- `handle_low_confidence_answer`
- `submit_answer_feedback`
- `list_workshop_sources`
- `list_tools`

`lookup_tool_template` là template dùng Tavily live API. Tool này có file
`TOOL.md` riêng nhưng hiện chưa được đăng ký vào `TOOL_FUNCTIONS`.

## 1. retrieve_slide_sources

**Mục đích:** Tìm các slide hoặc tài liệu published liên quan nhất với câu hỏi
của học viên.

**Vị trí:**

- `codebase/ai/tools/retrieve_slide_sources/tool.py`
- `codebase/ai/tools/retrieve_slide_sources/TOOL.md`

**Input:**

```python
{
    "question": str,
    "cohort": str | None,
    "workshopNo": int | None,
    "topK": int,
}
```

Tool cũng hỗ trợ alias Python nội bộ:

```python
{
    "workshop_no": int | None,
    "top_k": int | None,
}
```

**Output:**

```python
{
    "tool": "retrieve_slide_sources",
    "question": str,
    "matches": [
        {
            "sourceId": str,
            "score": float,
            "citationLabel": str,
            "sourceExcerpt": str,
            "summary": str,
            "slideNo": int | None,
            "sectionTitle": str,
        }
    ],
}
```

**Cách hoạt động:**

- Search theo token overlap trên các field:
  `skill_tags`, `section_title`, `example_student_questions`, `summary`,
  `source_excerpt`, `learning_objective`, `content`, `full_text`, `raw_text`.
- Field có trọng số cao nhất là `skill_tags`, `section_title`,
  `example_student_questions`, `summary`, `source_excerpt`.
- Tăng điểm nếu câu hỏi match chính xác với example question hoặc nằm trong
  section title.
- Sort bằng raw score để tránh việc nhiều source bị cap score `1.0` rồi đứng sai
  thứ tự.
- Output `score` được normalize trong khoảng `0.0` đến `1.0`.
- `workshopNo` filter theo `workshop_no`; với dữ liệu Day 05 thì fallback theo
  field `day`.
- `topK` giới hạn số match trả về, tối thiểu là 1.

**Ví dụ:**

```python
retrieve_slide_sources(
    question="Chunking ảnh hưởng thế nào đến retrieval quality?",
    topK=2,
)
```

Kỳ vọng source đứng đầu:

```text
SRC-W08-S005 - Workshop 8 - RAG Pipeline, slide 5, Chunking va retrieval quality
```

## 2. classify_question_scope

**Mục đích:** Phân loại câu hỏi có nên được trả lời bằng học liệu chính thức hay
không.

**Vị trí:**

- `codebase/ai/tools/classify_question_scope/tool.py`
- `codebase/ai/tools/classify_question_scope/TOOL.md`

**Input:**

```python
{
    "question": str,
    "retrievedMatches": list[dict],
}
```

Tool cũng hỗ trợ alias:

```python
{
    "retrieved_matches": list[dict],
}
```

**Output:**

```python
{
    "tool": "classify_question_scope",
    "scope": "in_scope" | "low_confidence" | "out_of_scope",
    "reason": str,
    "confidence": float,
}
```

**Ngưỡng hiện tại:**

- `score >= 0.55`: `in_scope`
- `0.25 <= score < 0.55`: `low_confidence`
- `< 0.25` hoặc không có match: `out_of_scope`

**Guardrail ngoài phạm vi:**

Một số câu hỏi xin tư vấn ngoài phạm vi workshop sẽ bị ép về
`out_of_scope`, dù có match keyword với tài liệu:

- tài chính/chứng khoán/cổ phiếu/đầu tư
- bitcoin/crypto/forex
- y tế/bệnh/thuốc
- pháp lý

Guardrail này giúp tránh việc AI trả lời tự tin cho câu hỏi không thuộc học liệu
chính thức.

**Ví dụ:**

```python
classify_question_scope(
    question="Cách đầu tư chứng khoán bằng RAG?",
    retrievedMatches=[{"sourceId": "SRC-W08-S002", "score": 0.83}],
)
```

Kỳ vọng:

```python
{
    "scope": "out_of_scope",
    "confidence": 0.0,
}
```

## 3. generate_grounded_answer

**Mục đích:** Sinh câu trả lời ngắn, dễ hiểu, có ví dụ và citations, chỉ dựa
trên source đã retrieve.

**Vị trí:**

- `codebase/ai/tools/generate_grounded_answer/tool.py`
- `codebase/ai/tools/generate_grounded_answer/TOOL.md`

**Input:**

```python
{
    "question": str,
    "sources": list[dict],
    "studentLevel": "beginner" | "intermediate",
    "language": "vi" | "en",
}
```

Tool cũng hỗ trợ alias:

```python
{
    "student_level": "beginner" | "intermediate",
}
```

**Output:**

```python
{
    "tool": "generate_grounded_answer",
    "answer": str,
    "example": str,
    "citations": [
        {
            "sourceId": str,
            "citationLabel": str,
            "excerpt": str,
        }
    ],
}
```

Nếu không truyền source:

```python
{
    "tool": "generate_grounded_answer",
    "answer": "",
    "example": "",
    "citations": [],
    "error": "No sources provided. Use handle_low_confidence_answer instead.",
}
```

**Cách hoạt động:**

- Nên chỉ gọi khi `classify_question_scope` trả `in_scope`.
- Source đầu tiên trong `sources` là source chính để tạo `answer` và `example`.
- Tất cả source truyền vào đều được đưa vào `citations`.
- `language="vi"` dùng template tiếng Việt không dấu trong output hiện tại.
- `language="en"` dùng template tiếng Anh.
- Tool không gọi LLM; câu trả lời được dựng bằng template từ `summary`,
  `sectionTitle` và `sourceExcerpt`.

**Ví dụ:**

```python
retrieved = retrieve_slide_sources(question="Tool calling là gì?", topK=1)
generate_grounded_answer(
    question="Tool calling là gì?",
    sources=retrieved["matches"],
)
```

Kỳ vọng citation:

```text
SRC-W07-S004 - Workshop 7 - First Working Agent, slide 4, LLM va tool calling
```

## 4. handle_low_confidence_answer

**Mục đích:** Trả lời an toàn khi không đủ nguồn, score thấp, hoặc câu hỏi ngoài
phạm vi.

**Vị trí:**

- `codebase/ai/tools/handle_low_confidence_answer/tool.py`
- `codebase/ai/tools/handle_low_confidence_answer/TOOL.md`

**Input:**

```python
{
    "question": str,
    "reason": str,
    "closestSources": list[dict] | None,
}
```

Tool cũng hỗ trợ alias:

```python
{
    "closest_sources": list[dict] | None,
}
```

**Output:**

```python
{
    "tool": "handle_low_confidence_answer",
    "message": str,
    "suggestedQuestions": list[str],
}
```

**Cách hoạt động:**

- Không trả lời trực tiếp nội dung ngoài phạm vi.
- Với câu hỏi tài chính/y tế/pháp lý/crypto, tool dùng suggested questions mặc
  định trong phạm vi workshop, thay vì gợi ý theo closest source có thể bị lệch.
- Với low-confidence bình thường, tool có thể tạo suggested questions từ
  `sectionTitle` hoặc `citationLabel` của closest sources.
- Nếu không có closest source, tool dùng suggested questions mặc định.

**Suggested questions mặc định:**

```text
- Chunking trong RAG la gi?
- Chunk qua dai anh huong retrieval the nao?
- Metadata giup retrieval tot hon ra sao?
```

## 5. submit_answer_feedback

**Mục đích:** Ghi feedback của học viên, mentor hoặc admin về chất lượng câu trả
lời/citation.

**Vị trí:**

- `codebase/ai/tools/submit_answer_feedback/tool.py`
- `codebase/ai/tools/submit_answer_feedback/TOOL.md`

**Input:**

```python
{
    "question": str,
    "answerId": str | None,
    "sourceIds": list[str],
    "feedbackType": "wrong_citation" | "unclear_answer" | "wrong_answer" | "helpful",
    "note": str | None,
    "userRole": "student" | "mentor" | "admin",
}
```

Tool cũng hỗ trợ alias:

```python
{
    "answer_id": str | None,
    "source_ids": list[str],
    "feedback_type": str,
    "user_role": str,
    "storage_path": str | None,
}
```

**Output:**

```python
{
    "tool": "submit_answer_feedback",
    "saved": bool,
    "feedbackId": str,
    "nextAction": "add_to_golden_test" | "mentor_review" | "no_action",
}
```

**Cách hoạt động:**

- Mặc định ghi log vào temp file `gaptutor_answer_feedback.jsonl`.
- Test hoặc caller nội bộ có thể override bằng `storage_path`.
- `feedbackId` là hash ổn định từ `question`, `sourceIds`, `feedbackType`,
  `note`.
- Record log có thêm `createdAt` theo UTC ISO timestamp.

**Routing `nextAction`:**

- `feedbackType="helpful"` -> `no_action`
- `feedbackType="wrong_citation"` -> `add_to_golden_test`
- `feedbackType="wrong_answer"` -> `add_to_golden_test`
- Feedback lỗi từ `mentor` hoặc `admin` -> `add_to_golden_test`
- Student `unclear_answer` -> `mentor_review`

## 6. list_workshop_sources

**Mục đích:** Cho mentor/admin xem danh sách source AI Tutor đang dùng.

**Vị trí:**

- `codebase/ai/tools/list_workshop_sources/tool.py`
- `codebase/ai/tools/list_workshop_sources/TOOL.md`

**Input:**

```python
{
    "cohort": str | None,
    "workshopNo": int | None,
    "status": "draft" | "published" | None,
}
```

Tool cũng hỗ trợ alias:

```python
{
    "workshop_no": int | None,
}
```

**Output:**

```python
{
    "tool": "list_workshop_sources",
    "sources": [
        {
            "sourceId": str,
            "workshopTitle": str,
            "slideNo": int | None,
            "sectionTitle": str,
            "status": "draft" | "published",
            "citationLabel": str,
        }
    ],
}
```

**Cách hoạt động:**

- Filter theo `cohort`, `workshopNo`/`day`, và `status`.
- Nếu source không có `workshop_title`, tool dùng fallback `Day {day}`.
- Sort theo `(workshopTitle, slideNo)`.
- Dùng tốt cho UI admin/mentor kiểm tra source published/draft.

**Ví dụ:**

```python
list_workshop_sources(workshopNo=8, status="published")
```

Kỳ vọng gồm:

```text
SRC-W08-S002
SRC-W08-S005
```

## 7. list_tools

**Mục đích:** Liệt kê metadata của 7 LMS assistant tools trong prototype.

**Vị trí:**

- `codebase/ai/tools/list_tools/tool.py`
- `codebase/ai/tools/list_tools/TOOL.md`

**Input:**

```python
{}
```

**Output:**

```python
{
    "tool": "list_tools",
    "tools": [
        {
            "name": str,
            "purpose": str,
            "inputs": list[str],
            "outputs": list[str],
        }
    ],
}
```

**Lưu ý:** `list_tools` lấy metadata từ `TOOL_DESCRIPTIONS` trong
`_learning_assistant.py`. Danh sách này hiện chỉ gồm 7 LMS assistant tools,
không gồm `summarize` và không gồm `lookup_tool_template`.

## 8. explain

**Mục đích:** Giải thích một khái niệm/câu hỏi của học viên dựa trên source được
retrieval trả về, có citation theo contract `explain_and_summarize_tool_contract.yaml`.

**Vị trí:**

- `codebase/ai/tools/explain/tool.py`
- `codebase/ai/tools/explain/TOOL.md`

**Input chính:**

```python
{
    "content": str,
    "retrieval": callable | dict | Any,
}
```

**Output theo contract:**

```python
{
    "explanation": str,
    "citation": str,
}
```

**Lưu ý về output `example`:**

Contract YAML mô tả output có `explanation`, `example`, `citation`. Implementation
hiện tại không trả `example` thành field riêng. Thay vào đó, ví dụ minh họa được
ghép vào trong chuỗi `explanation` dưới heading:

```text
### Ví dụ minh họa
```

Vì vậy UI/caller hiện tại nên đọc ví dụ từ nội dung `explanation`, hoặc cần sửa
implementation nếu muốn field `example` riêng đúng 100% với contract.

**Cách nhận retrieval:**

Tool hỗ trợ 3 dạng `retrieval`:

1. Callable function:

```python
ret_result = retrieval(content)
```

2. Dict payload trực tiếp:

```python
{
    "data": ...,
    "citation": str,
}
```

3. Giá trị bất kỳ khác:

```python
{
    "data": retrieval,
    "citation": "",
}
```

**Dạng source mong đợi:**

`data` có thể là list source hoặc một payload bất kỳ. Với list source dạng dict,
tool format các field sau vào prompt:

```python
{
    "section_title": str,
    "summary": str,
    "source_excerpt": str,
    "citation_label": str,
}
```

Nếu `citation` không được truyền ở payload gốc, tool sẽ nối các
`citation_label` trong source list thành chuỗi citation.

**Cách hoạt động khi có API key:**

- Tool đọc `.env` từ repo root nếu file tồn tại.
- Nếu có `OPENROUTER_API_KEY` hợp lệ, tool gọi OpenRouter qua OpenAI client.
- Model hiện dùng: `google/gemma-4-31b-it:free`.
- Prompt yêu cầu model chỉ trả lời dựa trên slide sources và output JSON với:
  `explanation`, `simplified`, `example`.
- Sau đó tool ghép thành một chuỗi markdown:

```text
### Diễn giải
...

### Đơn giản hóa
...

### Ví dụ minh họa
...
```

**Fallback local/offline:**

Nếu không có API key, API key không hợp lệ, hoặc API call lỗi, tool dùng fallback
local:

- Nếu `content` chứa `rag` hoặc `retrieval`, trả giải thích RAG cố định.
- Nếu không, trả template chung:
  `Giải thích chi tiết dựa trên slide cho câu hỏi: '{content}'.`

**Trường hợp không có source:**

Nếu `data` rỗng hoặc falsy, tool trả:

```python
{
    "explanation": "Rất tiếc, câu hỏi của bạn nằm ngoài phạm vi tài liệu slides hiện có của workshop.",
    "citation": "",
}
```

**Ví dụ dùng với retrieval function:**

```python
def mock_retrieval(content: str) -> dict:
    return {
        "data": [
            {
                "source_id": "SRC-W08-S002",
                "slide_no": 2,
                "section_title": "RAG la gi",
                "summary": "RAG giup AI tra loi dua tren tai lieu duoc truy xuat.",
                "source_excerpt": "RAG = retrieve relevant context + generate grounded answer.",
                "citation_label": "Workshop 8 - RAG Pipeline, slide 2, RAG la gi",
            }
        ],
        "citation": "Workshop 8 - RAG Pipeline, slide 2, RAG la gi",
    }

explain("RAG là gì?", mock_retrieval)
```

Kỳ vọng:

```python
{
    "explanation": "### Diễn giải\n...\n\n### Đơn giản hóa\n...\n\n### Ví dụ minh họa\n...",
    "citation": "Workshop 8 - RAG Pipeline, slide 2, RAG la gi",
}
```

**Khác biệt với `generate_grounded_answer`:**

- `explain` tập trung giải thích sâu hơn, có phần đơn giản hóa và ví dụ trong
  markdown.
- `generate_grounded_answer` là template local ngắn hơn, output có field
  `answer`, `example`, `citations` riêng.
- `explain` có thể gọi LLM qua OpenRouter nếu có API key; `generate_grounded_answer`
  hiện không gọi LLM.

## 9. summarize

**Mục đích:** Tóm tắt nội dung học tập theo contract explain/summarize.

**Vị trí:**

- `codebase/ai/tools/summarize/tool.py`
- `codebase/ai/tools/summarize/TOOL.md`

**Input chính:**

```python
{
    "query": str,
    "content": str,
    "detail_level": "brief" | "detailed",
    "retrieval": callable | None,
    "mode": "auto" | "concept" | "workshop",
    "workshop_no": int | None,
    "max_sources": int,
}
```

**Output chính:**

```python
{
    "summary": str,
    "key_points": list[str],
    "keywords": list[str],
    "citation": str,
    "citations": list[dict],
    "confidence": "high" | "low",
}
```

**Cách hoạt động:**

- Nếu chỉ truyền `content` và không truyền `retrieval`, tool tóm tắt trực tiếp
  nội dung đó.
- Nếu truyền `retrieval` callable, tool gọi retrieval để lấy `{data, citation}`
  trước. Nếu retrieval không match hoặc báo lỗi dữ liệu, tool fallback về nguồn
  mock nội bộ.
- Nếu `mode="workshop"` hoặc query có pattern như `workshop 8`, tool tóm tắt
  nhiều source trong workshop.
- Có guardrail không làm hộ bài lab hoàn chỉnh.
- Nguồn mock nội bộ của `summarize` hiện trỏ tới
  `02-group-spec/data/mock_ai_tutor_slide_sources.json`. Day 05 được hỗ trợ khi
  truyền retrieval function.

## 10. lookup_tool_template

**Mục đích:** Template cho tool search web qua Tavily.

**Vị trí:**

- `codebase/ai/tools/lookup_tool_template/tool.py`
- `codebase/ai/tools/lookup_tool_template/TOOL.md`

**Input:**

```python
{
    "query": str,
    "topic": "general" | "news",
    "timeframe": str | None,
    "max_results": int,
}
```

**Output:**

```python
{
    "tool": "web_search",
    "query": str,
    "topic": str,
    "timeframe": str | None,
    "items": list[dict],
}
```

**Lưu ý:**

- Cần biến môi trường `TAVILY_API_KEY`.
- Đây là template live API, chưa được đăng ký trong `TOOL_FUNCTIONS`.

## Luồng sử dụng đề xuất

### Happy path

```python
question = "Chunking ảnh hưởng thế nào đến retrieval quality?"

retrieved = retrieve_slide_sources(question=question, topK=2)
scope = classify_question_scope(
    question=question,
    retrievedMatches=retrieved["matches"],
)

if scope["scope"] == "in_scope":
    result = generate_grounded_answer(
        question=question,
        sources=retrieved["matches"],
    )
else:
    result = handle_low_confidence_answer(
        question=question,
        reason=scope["reason"],
        closestSources=retrieved["matches"],
    )
```

Kỳ vọng:

```text
retrieve -> SRC-W08-S005
classify -> in_scope
answer -> có citation Workshop 8 - RAG Pipeline, slide 5
```

### Failure path

```python
question = "Cách đầu tư chứng khoán bằng RAG?"
```

Kỳ vọng:

```text
retrieve -> có thể match gần với RAG source
classify -> out_of_scope
answer -> gọi handle_low_confidence_answer, không gọi generate_grounded_answer
```

## Test coverage

Tests nằm tại:

- `codebase/ai/tests/test_learning_assistant_tools.py`
- `codebase/ai/tests/test_summarize_tool.py`
- `codebase/ai/tools/explain/test_explain_tool.py`

Lệnh chạy test:

```bash
cd codebase/ai
PYTHONDONTWRITEBYTECODE=1 /Users/tuan/.pyenv/versions/3.11.11/bin/python -m unittest discover -s tests
```

Các nhóm behavior đã được test:

- Retrieve đúng source chính, tôn trọng `topK`, và không dùng draft source cho
  student-facing answer.
- Filter source theo workshop/day và status.
- Scope classification cho `in_scope`, `low_confidence`, `out_of_scope`.
- Guardrail cho câu hỏi tài chính/y tế/pháp lý/crypto ngoài phạm vi.
- Grounded answer có `answer`, `example`, `citations`.
- Grounded answer trả lỗi sạch khi không có source.
- Low-confidence fallback có suggested questions phù hợp.
- Feedback routing sang `no_action`, `mentor_review`, `add_to_golden_test`.
- `list_workshop_sources` có đủ field để UI render.
- Registry có đủ tool đã đăng ký.
- `explain` có local test riêng để kiểm tra output có `explanation`,
  `citation`, các heading markdown, và citation khớp retrieval.
