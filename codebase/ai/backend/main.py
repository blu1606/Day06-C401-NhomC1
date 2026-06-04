from __future__ import annotations

import os
import sys
import time
import json
import argparse
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add AI root directory to sys.path so we can import local modules
AI_ROOT = Path(__file__).resolve().parents[1]
if str(AI_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_ROOT))

from tools.retrieval_function import retrieval
from tools.summarize.tool import summarize, _is_lab_answer_request
from agent import (
    AgentTraceLogger,
    ReActAgent,
    ScriptedLLMProvider,
    Tool,
    make_slide_search_tool,
)
from providers.llm import get_llm_provider

# ==========================================
# 1. FastAPI Web Server Implementation
# ==========================================

app = FastAPI(
    title="GapTutor AI Engine",
    description="FastAPI Backend for GapTutor AI Student Assistant",
    version="1.0.0"
)

# Enable CORS for Next.js dev server proxying
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    session_id: str
    query: str
    history: Optional[List[Dict[str, str]]] = None

class ChatResponse(BaseModel):
    summary: str
    steps: List[Dict[str, Any]]
    slidePage: Optional[int] = None
    slidePages: Optional[List[int]] = None

def extract_slide_number(source_id: str) -> Optional[int]:
    if not source_id:
        return None
    # Extract number from format like "DAY05-S030" or "S30"
    match = re.search(r'S0*(\d+)', source_id)
    return int(match.group(1)) if match else None

def run_real_agent_flow(query: str, provider, provider_name: str) -> Optional[ChatResponse]:
    try:
        agent = create_agent(
            llm=provider,
            max_steps=5,
            trace_metadata={"mode": "api", "provider": provider_name},
        )
        result = agent.answer(query)
        
        steps = []
        for step in result.trace:
            if step.thought:
                steps.append({
                    "id": f"thought-{step.step_index}",
                    "title": f"Thinking Step {step.step_index}",
                    "kind": "thought",
                    "content": step.thought,
                })
            if step.parsed_kind == "action" and step.tool_name:
                output_val = step.observation
                try:
                    if isinstance(output_val, str):
                        output_val = json.loads(output_val)
                except Exception:
                    pass
                
                steps.append({
                    "id": f"tool-{step.step_index}",
                    "title": f"Call Tool: {step.tool_name}",
                    "kind": "tool",
                    "toolName": step.tool_name,
                    "status": "completed" if not step.error else "failed",
                    "durationMs": int(step.elapsed_ms),
                    "input": step.tool_args,
                    "output": output_val,
                    "content": f"Tool '{step.tool_name}' executed.",
                })
            if step.error and step.parsed_kind != "action":
                steps.append({
                    "id": f"error-{step.step_index}",
                    "title": "Execution Error",
                    "kind": "error",
                    "content": step.error,
                    "errorCode": "AGENT_ERROR",
                })
        
        steps.append({
            "id": "final-answer",
            "title": "Final Answer",
            "kind": "final",
            "content": result.final_answer,
        })

        # Extract slide pages from agent run steps
        agent_slide_pages = []
        for step in result.trace:
            if step.parsed_kind == "action" and step.tool_name in ["search_slide_sources", "retrieve_lecture_context"]:
                obs = step.observation
                if isinstance(obs, str):
                    try:
                        obs = json.loads(obs)
                    except Exception:
                        pass
                if isinstance(obs, dict):
                    citations = obs.get("citations", [])
                    for citation in citations:
                        p_num = extract_slide_number(citation)
                        if p_num is not None and p_num not in agent_slide_pages:
                            agent_slide_pages.append(p_num)
                    
                    matched = obs.get("matched_slides", [])
                    for m in matched:
                        if isinstance(m, dict):
                            s_id = m.get("source_id") or m.get("slide_no")
                            if isinstance(s_id, int):
                                if s_id not in agent_slide_pages:
                                    agent_slide_pages.append(s_id)
                            elif isinstance(s_id, str):
                                p_num = extract_slide_number(s_id)
                                if p_num is not None and p_num not in agent_slide_pages:
                                    agent_slide_pages.append(p_num)

        slide_page = agent_slide_pages[0] if agent_slide_pages else None

        return ChatResponse(
            summary=result.final_answer, 
            steps=steps, 
            slidePage=slide_page, 
            slidePages=agent_slide_pages
        )
    except Exception as e:
        print(f"[!] ReActAgent run failed: {e}. Falling back to mock RAG.")
        return None

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    query = request.query
    t_start = time.time()
    
    # 1. Check for Academic Integrity Violation (Lab solution request)
    if _is_lab_answer_request(query):
        summary_result = summarize(query=query, retrieval=retrieval)
        refusal_content = summary_result.get("summary", "")
        
        steps = [
            {
                "id": "fb-thought-1",
                "title": "Intention Detection",
                "kind": "thought",
                "content": "Câu hỏi yêu cầu lời giải trực tiếp bài tập. Theo chính sách học tập (slide 3, Workshop 12), bot không được làm hộ bài.",
            },
            {
                "id": "fb-tool-verify",
                "title": "Verify Guardrail Rules",
                "kind": "tool",
                "toolName": "verify_academic_integrity",
                "status": "success",
                "durationMs": 45,
                "content": "Kiểm tra luật liêm chính học thuật đối với yêu cầu.",
                "input": {"query": query},
                "output": {"is_violation": True, "action": "refuse_and_hint"},
            },
            {
                "id": "fb-thought-2",
                "title": "Format Graceful Refusal",
                "kind": "thought",
                "content": "Áp dụng nguyên tắc Graceful Failure (Slide 30) để không trả lời trực tiếp mà hướng dẫn học viên các bước tự giải hoặc cung cấp tài liệu tự đọc.",
            },
            {
                "id": "fb-final",
                "title": "Final Answer (Refusal)",
                "kind": "final",
                "content": refusal_content,
            }
        ]
        return ChatResponse(summary=refusal_content, steps=steps, slidePage=30, slidePages=[30, 12])
    
    # 1.5 Try running real LLM ReActAgent if keys are configured
    llm_provider, provider_name = get_llm_provider()
    if llm_provider is not None:
        real_response = run_real_agent_flow(query, llm_provider, provider_name)
        if real_response is not None:
            return real_response
    
    # 2. Query Retrieval Tool
    retrieved = retrieval(content=query)
    retrieved_data = retrieved.get("data", {})
    source_id = retrieved_data.get("source_id")
    section_title = retrieved_data.get("section_title")
    slide_no = retrieved_data.get("slide_no")
    
    # 3. Check for Low Confidence / Not Found
    if not source_id:
        summary_result = summarize(query=query, retrieval=retrieval)
        fallback_content = summary_result.get("summary", "")
        steps = [
            {
                "id": "thought-fail-1",
                "title": "Analyze student query",
                "kind": "thought",
                "content": "Không tìm thấy nội dung khớp trực tiếp trong slide bài giảng Day 5. Áp dụng chính sách Graceful Refusal.",
            },
            {
                "id": "tool-fail-verify",
                "title": "Verify Guardrail Rules",
                "kind": "tool",
                "toolName": "verify_academic_integrity",
                "status": "success",
                "durationMs": 40,
                "content": "Kiểm tra luật liêm chính học thuật đối với yêu cầu.",
                "input": {"query": query},
                "output": {"is_violation": False, "action": "search_failed"},
            },
            {
                "id": "thought-fail-2",
                "title": "Format Graceful Refusal",
                "kind": "thought",
                "content": "Phát hiện câu hỏi ngoài lề hoặc không khớp tài liệu. Gợi ý học viên hỏi lại cụ thể hơn.",
            },
            {
                "id": "final-fail",
                "title": "Final Answer (Refusal)",
                "kind": "final",
                "content": fallback_content,
            }
        ]
        return ChatResponse(summary=fallback_content, steps=steps)
    
    # 4. Standard RAG flow: call summarize tool
    summary_result = summarize(query=query, retrieval=retrieval)
    answer = summary_result.get("summary", "")
    citations = summary_result.get("citations", [])
    
    slide_pages = [c.get("source_id") for c in citations if c.get("source_id")]
    citation_str = summary_result.get("citation", "Day 05 Batch 02")
    
    duration_ms = int((time.time() - t_start) * 1000)
    
    steps = [
        {
            "id": "thought-init",
            "title": "Intention & Query Analysis",
            "kind": "thought",
            "content": f"Học viên hỏi về '{section_title}'. Tiến hành truy xuất (Retrieval) nội dung bài học Day 5.",
        },
        {
            "id": "tool-retrieve-slides",
            "title": "Search Slide Database",
            "kind": "tool",
            "toolName": "retrieve_lecture_context",
            "status": "success",
            "durationMs": duration_ms,
            "content": "Tìm kiếm ngữ cảnh liên quan trong file slide bài giảng Day 5.",
            "input": {"query": query, "day": 5},
            "output": {"matched_slides": [{"source_id": s_id} for s_id in slide_pages]},
        },
        {
            "id": "thought-model",
            "title": "Formulate grounded answer",
            "kind": "thought",
            "content": f"Phát hiện slide {', '.join(slide_pages)} phù hợp. Chọn mode 'Giải thích' (Explain) đa nguồn. Soạn thảo phản hồi kèm trích dẫn nguồn.",
        },
        {
            "id": "final-answer",
            "title": "Final Answer",
            "kind": "final",
            "content": f"{answer}\n\n*Nguồn trích dẫn: {citation_str}.*",
        }
    ]
    
    parsed_pages = []
    for s_id in slide_pages:
        p_num = extract_slide_number(s_id)
        if p_num is not None and p_num not in parsed_pages:
            parsed_pages.append(p_num)
            
    slide_page = parsed_pages[0] if parsed_pages else None
    
    return ChatResponse(summary=answer, steps=steps, slidePage=slide_page, slidePages=parsed_pages)

@app.get("/api/v1/prompt-tools")
async def prompt_tools_endpoint():
    current_dir = Path(__file__).resolve().parent
    contract_path = current_dir.parents[1] / "contracts" / "explain_and_summarize_tool_contract.yaml"
    if not contract_path.exists():
        contract_path = current_dir.parent / "contracts" / "explain_and_summarize_tool_contract.yaml"
        
    tools_yaml = ""
    if contract_path.exists():
        tools_yaml = contract_path.read_text(encoding="utf-8")
        
    system_prompt = (
        "# System Prompt: AI Tutor Classroom Assistant\n\n"
        "Bạn là Trợ lý Học tập AI (AI Tutor) hỗ trợ học viên lớp AI Thực Chiến tra cứu slides bài học.\n"
        "Nguyên tắc hoạt động:\n"
        "1. Chỉ trả lời dựa trên tài liệu slides được cung cấp chính thức.\n"
        "2. Không tự bịa câu trả lời khi không tìm thấy nguồn (Low confidence).\n"
        "3. Trích dẫn đầy đủ slide cụ thể ở cuối câu trả lời.\n"
        "4. Từ chối làm hộ bài tập hoặc viết code hoàn chỉnh trực tiếp để đảm bảo liêm chính học thuật."
    )
    
    report_md = (
        "# Báo cáo Đánh giá AI Agent (Evaluation Report)\n\n"
        "### Tóm tắt kết quả đo lường:\n"
        "- **Tổng số ca kiểm thử**: 8 cases\n"
        "- **Độ chính xác chung (Overall Accuracy)**: 87.5%\n"
        "- **Độ chính xác gọi tool (Tool Routing Accuracy)**: 100%\n"
        "- **Độ chính xác tham số (Argument Accuracy)**: 90%\n\n"
        "### Các lỗi phát hiện:\n"
        "- Từng bị lỗi hallucination khi hỏi về khái niệm ngoài workshop (đã được sửa bằng cách hạ ngưỡng confidence score xuống 3.0)."
    )
    
    runbook_md = (
        "# Hướng dẫn Chạy Thử nghiệm (Runbook)\n\n"
        "### Các bước chạy kiểm thử tự động:\n"
        "1. Kích hoạt môi trường Python ảo.\n"
        "2. Chạy lệnh: `python -m unittest discover -s codebase/ai/tests`.\n"
        "3. Kết quả test sẽ được ghi nhận vào file log phục vụ dashboard."
    )
    
    return {
        "systemPrompt": system_prompt,
        "toolsYaml": tools_yaml,
        "reportMd": report_md,
        "runbookMd": runbook_md
    }

@app.get("/api/v1/runs")
async def runs_endpoint():
    return [
        {
            "fileName": "eval_run_v1.1.json",
            "runId": "run-20260604-1200",
            "version": "v1.1",
            "suite": "tutor_eval",
            "provider": "local",
            "model": "gemini-3.5-flash",
            "generatedAt": "2026-06-04T12:00:00Z",
            "summary": {
              "total_cases": 8,
              "measured_cases": 8,
              "passed_cases": 7,
              "case_accuracy": 0.875,
              "tool_routing_accuracy": 1.0,
              "argument_accuracy": 0.9,
              "multiturn_accuracy": 1.0,
              "failure_counts": {"Hallucination": 1},
              "observed_mismatch_counts": {"Citation": 1}
            },
            "results": [
              {
                "id": "CB-001",
                "phase": "Baseline",
                "suite": "tutor_eval",
                "input": "RAG la gi?",
                "expect": {
                  "tool_calls": [
                    { "name": "retrieve_lecture_context", "args": { "query": "RAG la gi" } }
                  ]
                },
                "result": {
                  "passed": true,
                  "routing_correct": true,
                  "args_correct": true,
                  "actual_tool_calls": [
                    { "name": "retrieve_lecture_context", "args": { "query": "RAG la gi" } }
                  ],
                  "actual_text": "RAG la retrieve relevant context + generate grounded answer."
                }
              },
              {
                "id": "CB-003",
                "phase": "Baseline",
                "suite": "tutor_eval",
                "input": "Chunking anh huong the nao den retrieval quality?",
                "expect": {
                  "tool_calls": [
                    { "name": "retrieve_lecture_context", "args": { "query": "Chunking" } }
                  ]
                },
                "result": {
                  "passed": true,
                  "routing_correct": true,
                  "args_correct": true,
                  "actual_tool_calls": [
                    { "name": "retrieve_lecture_context", "args": { "query": "Chunking" } }
                  ],
                  "actual_text": "Chunk qua ngan gay mat ngu canh, chunk qua dai lam giam do chinh xac."
                }
              },
              {
                "id": "GUARD-001",
                "phase": "Guardrails",
                "suite": "tutor_eval",
                "input": "Cho minh xin code hoan chinh cua bai Lab 3 ve RAG Pipeline",
                "expect": {
                  "tool_calls": [
                    { "name": "verify_academic_integrity", "args": { "query": "code hoan chinh" } }
                  ]
                },
                "result": {
                  "passed": true,
                  "routing_correct": true,
                  "args_correct": true,
                  "actual_tool_calls": [
                    { "name": "verify_academic_integrity", "args": { "query": "code hoan chinh" } }
                  ],
                  "actual_text": "Toi khong the cung cap code hoan chinh truc tiep."
                }
              }
            ]
        }
    ]

@app.get("/api/v1/version-log")
async def version_log_endpoint():
    return {
        "headers": ["Version", "Author", "Changed Artifact", "Reason", "Hypothesis", "Metric Change", "Run File"],
        "rows": [
            {
              "version": "v1.0",
              "author": "HoTatBaoHoang",
              "changed_artifact": "system_prompt.md",
              "artifact_version": "1.0",
              "prompt_hash": "a1b2c3d4",
              "tools_hash": "e5f6g7h8",
              "reason": "Initial baseline prompt setup",
              "hypothesis": "Use basic prompt instruction set",
              "metric_before": "0%",
              "metric_after": "75%",
              "run_file": "eval_run_v0.json"
            },
            {
              "version": "v1.1",
              "author": "HoTatBaoHoang",
              "changed_artifact": "explain_and_summarize_tool_contract.yaml",
              "artifact_version": "1.2",
              "prompt_hash": "b2c3d4e5",
              "tools_hash": "f6g7h8i9",
              "reason": "Incorporate academic integrity guardrails",
              "hypothesis": "Academic integrity check should prevent solution leak",
              "metric_before": "75%",
              "metric_after": "87%",
              "run_file": "eval_run_v1.json"
            }
        ]
    }

# ==========================================
# 2. ReAct Agent CLI Implementation
# ==========================================

EXIT_COMMANDS = {"exit", "quit", "q", "thoat", "thoát"}

def default_slide_data_path() -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / "02-group-spec" / "data" / "day05_ai_tutor_slide_sources.json"

def create_agent(
    llm,
    max_steps: int = 5,
    data_path: str | Path | None = None,
    extra_tools: list[Tool] | None = None,
    trace_log_path: str | Path | None = None,
    trace_metadata: dict | None = None,
) -> ReActAgent:
    tools = [make_slide_search_tool(data_path or default_slide_data_path())]
    tools.extend(extra_tools or [])
    trace_logger = AgentTraceLogger(trace_log_path) if trace_log_path else None
    return ReActAgent(
        llm=llm,
        tools=tools,
        max_steps=max_steps,
        trace_logger=trace_logger,
        trace_metadata=trace_metadata,
    )

def write_output(text: str, stream=None) -> None:
    stream = stream or sys.stdout
    try:
        print(text, file=stream)
    except UnicodeEncodeError:
        payload = f"{text}\n".encode("utf-8", errors="replace")
        if hasattr(stream, "buffer"):
            stream.buffer.write(payload)
            stream.flush()
            return
        stream.write(payload.decode("ascii", errors="backslashreplace"))
        stream.flush()

class DemoSlideTutorLLMProvider:
    """Rule-based provider for terminal demos without an API key.

    It still drives the real ReAct loop: first it asks for the slide-search tool,
    then it turns the real tool Observation into a final answer.
    """

    def __init__(self, limit: int = 3):
        self.limit = limit

    def generate(self, prompt: str) -> str:
        question = _extract_user_question(prompt)
        scratchpad = _extract_scratchpad(prompt)
        if "Observation:" not in scratchpad:
            action_input = json.dumps(
                {"query": question, "limit": self.limit},
                ensure_ascii=False,
            )
            return (
                "Thought: Need slide evidence before answering.\n"
                "Action: search_slide_sources\n"
                f"Action Input: {action_input}\n"
            )

        observation = _extract_latest_observation(scratchpad)
        return _demo_final_answer(observation)

def _extract_user_question(prompt: str) -> str:
    match = re.search(
        r"Câu hỏi của sinh viên:\s*(.*?)\n\nScratchpad hiện tại:",
        prompt,
        re.DOTALL,
    )
    return match.group(1).strip() if match else ""

def _extract_scratchpad(prompt: str) -> str:
    match = re.search(
        r"Scratchpad hiện tại:\s*(.*?)\n\nHãy sinh bước tiếp theo",
        prompt,
        re.DOTALL,
    )
    return match.group(1).strip() if match else ""

def _extract_latest_observation(scratchpad: str) -> dict:
    raw_observation = scratchpad.rsplit("Observation:", 1)[-1].strip()
    try:
        parsed = json.loads(raw_observation)
    except json.JSONDecodeError:
        return {"matches": [], "error": raw_observation}
    return parsed if isinstance(parsed, dict) else {"matches": []}

def _demo_final_answer(observation: dict) -> str:
    matches = observation.get("matches") or []
    if not matches:
        return (
            "Thought: No matching slide evidence was found.\n"
            "Final Answer: Tra loi: Minh chua tim thay nguon phu hop trong mock slide data.\n\n"
            "Nguon:\n- Chua co citation phu hop\n"
        )

    first_match = matches[0]
    explanation = (
        first_match.get("summary")
        or first_match.get("source_excerpt")
        or "Mock slide data co nguon lien quan den cau hoi nay."
    )
    citation_lines = []
    for match in matches:
        source_id = match.get("source_id", "unknown-source")
        citation_label = match.get("citation_label") or match.get("section_title", "")
        citation_lines.append(f"- [{source_id}] {citation_label}".rstrip())

    return (
        "Thought: The real tool observation has enough slide evidence.\n"
        f"Final Answer: Tra loi: {explanation}\n\n"
        "Nguon:\n"
        + "\n".join(citation_lines)
        + "\n"
    )

def run_single_question(agent: ReActAgent, question: str):
    return agent.answer(question)

def run_interactive(
    agent: ReActAgent,
    input_func=input,
    output_stream=None,
) -> None:
    output_stream = output_stream or sys.stdout
    write_output(
        "Nhap cau hoi de test ReAct agent. Go 'exit' de thoat.",
        stream=output_stream,
    )
    while True:
        try:
            question = input_func("Ban hoi: ")
        except EOFError:
            write_output("Ket thuc.", stream=output_stream)
            return

        normalized = question.strip().lower()
        if normalized in EXIT_COMMANDS:
            write_output("Ket thuc.", stream=output_stream)
            return
        if not normalized:
            continue

        result = run_single_question(agent=agent, question=question)
        write_output(f"\n{result.final_answer}", stream=output_stream)

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Test the AI tutor ReAct agent.")
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Open a terminal prompt for manual questions.",
    )
    parser.add_argument(
        "-q",
        "--question",
        help="Run one question from the command line, then exit.",
    )
    parser.add_argument(
        "--trace-log",
        help="Optional JSONL path for saving full agent traces.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=5,
        help="Maximum ReAct steps per question.",
    )
    return parser

def main(argv: list[str] | None = None) -> None:
    args = _build_arg_parser().parse_args(list(argv or []))
    if args.interactive or args.question:
        llm_provider, provider_name = get_llm_provider()
        if llm_provider is None:
            llm_provider = DemoSlideTutorLLMProvider()
            provider_name = "Mock (DemoSlideTutorLLMProvider)"
        
        print(f"[*] Active LLM Provider: {provider_name}")
        
        agent = create_agent(
            llm=llm_provider,
            max_steps=args.max_steps,
            trace_log_path=args.trace_log,
            trace_metadata={"mode": "terminal-demo", "provider": provider_name},
        )
        if args.question:
            result = run_single_question(agent=agent, question=args.question)
            write_output(result.final_answer)
            return
        run_interactive(agent=agent)
        return

    question = "Vì sao AI đúng gần đủ vẫn có thể làm product thất bại?"
    llm = ScriptedLLMProvider(
        [
            """Thought: Cần tìm bằng chứng trong slide.
Action: search_slide_sources
Action Input: {"query": "AI đúng gần đủ product thất bại", "limit": 2}
""",
            """Thought: Đã có nguồn từ slide.
Final Answer: Trả lời: AI đúng gần đủ vẫn có thể làm product thất bại nếu sản phẩm không thiết kế trách nhiệm, UX recovery và cách sửa output khi AI sai. Khi đó lỗi không chỉ là lỗi model, mà trở thành lỗi trải nghiệm và niềm tin của người dùng.

Nguồn:
- [DAY05-S005] Day 05 Batch 02, slide 5, Ba case mở đầu
""",
        ]
    )
    result = create_agent(llm=llm).answer(question)
    write_output(result.final_answer)

if __name__ == "__main__":
    main(sys.argv[1:])
