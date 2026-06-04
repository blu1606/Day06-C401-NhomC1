# AI Tutor ReAct Agent

Codebase này chứa phần lõi agent để trả lời câu hỏi kiến thức của sinh viên dựa trên mock slide data Day 05, có citation theo nguồn trong `02-group-spec/data/day05_ai_tutor_slide_sources.json`.

## Thành phần chính

- `agent.py`
  - `LLMProvider`: interface tối thiểu, nhận `prompt` và trả về text model sinh ra.
  - `Tool`: khai báo `name`, `description`, `input_format`, `func`.
  - `parse_react_response(...)`: đọc `Thought`, `Action`, `Action Input`, `Final Answer`.
  - `ToolExecutor`: tìm tool theo tên, gọi function thật, trả lỗi an toàn khi tool thiếu/sai.
  - `ReActAgent`: vòng lặp Thought -> Action -> Observation thật -> Final Answer.
  - `AgentTraceLogger`: ghi toàn bộ quá trình chạy agent ra file JSONL.
  - `make_slide_search_tool(...)`: tool mock tìm nguồn slide và trả `source_id`, `citation_label`.

- `backend/main.py`
  - `create_agent(...)`: factory đăng ký slide search tool mặc định.
  - `main()`: demo chạy bằng `ScriptedLLMProvider`, không cần API key.

## Guardrail quan trọng

Model không được tự tạo `Observation`. Nếu output của LLM có dòng `Observation:`, runtime sẽ cắt bỏ phần đó và chỉ đưa Observation thật từ tool vào vòng lặp tiếp theo.

## Lưu trace/log

Mỗi lần gọi `agent.answer(...)`, kết quả trả về là `AgentResult`. Có thể đọc log trong RAM qua:

```python
payload = result.to_dict()
```

Nếu muốn tự động lưu ra file JSONL sau mỗi lượt hỏi:

```python
from backend.main import create_agent

agent = create_agent(
    llm=llm_provider,
    trace_log_path="logs/agent_trace.jsonl",
    trace_metadata={"session_id": "demo-session"},
)

result = agent.answer("Vì sao AI đúng gần đủ vẫn có thể làm product thất bại?")
```

Mỗi dòng JSONL có:

- `run_id`
- `created_at`
- `user_input`
- `final_answer`
- `completed`
- `metadata`
- `trace[]`: gồm `prompt`, `llm_response`, `sanitized_response`, `thought`, `tool_name`, `tool_args`, `observation`, `elapsed_ms`, `usage`, `error`

## Format ReAct

Khi cần gọi tool:

```text
Thought: Cần tìm nguồn trong slide.
Action: search_slide_sources
Action Input: {"query": "AI failure path", "limit": 3}
```

Khi đã đủ bằng chứng:

```text
Thought: Đã có nguồn phù hợp.
Final Answer: Trả lời: ...

Nguồn:
- [DAY05-S005] Day 05 Batch 02, slide 5
```

## Chạy test

```powershell
cd "D:\AI Vin\LAB\DAY06\codebase\ai"
python -m unittest discover -s tests
```

## Chạy demo local

```powershell
cd "D:\AI Vin\LAB\DAY06\codebase\ai"
python backend\main.py
```

## Chạy để tự nhập prompt trong terminal

Lệnh này mở vòng lặp hỏi đáp. Gõ `exit` để thoát.

```powershell
cd "D:\AI Vin\LAB\DAY06\codebase\ai"
python backend\main.py --interactive
```

Vừa test vừa lưu toàn bộ trace/log:

```powershell
python backend\main.py --interactive --trace-log logs\agent_trace.jsonl
```

Chạy một câu hỏi rồi thoát:

```powershell
python backend\main.py --question "Bai hoc tu Air Canada chatbot la gi?"
```

Lưu ý: chế độ terminal hiện dùng `DemoSlideTutorLLMProvider`, một provider rule-based để test ReAct loop mà chưa cần API key. Nó vẫn gọi tool `search_slide_sources` thật và vẫn lưu trace đầy đủ. Khi có LLM thật, chỉ cần thay provider.

## Merge tools từ nhánh khác

Nhánh tools chỉ cần tạo thêm `Tool(...)` và truyền vào `create_agent(..., extra_tools=[...])`, hoặc thay thế tool mock `search_slide_sources` bằng function thật có cùng contract input/output.
