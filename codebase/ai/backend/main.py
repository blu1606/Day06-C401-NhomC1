from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

AI_ROOT = Path(__file__).resolve().parents[1]
if str(AI_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_ROOT))

from agent import (
    AgentTraceLogger,
    ReActAgent,
    ScriptedLLMProvider,
    Tool,
    make_slide_search_tool,
)


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
        agent = create_agent(
            llm=DemoSlideTutorLLMProvider(),
            max_steps=args.max_steps,
            trace_log_path=args.trace_log,
            trace_metadata={"mode": "terminal-demo"},
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
=======
import os
import json
import glob
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Relative imports inside codebase/ai
from tools.summarize.tool import summarize
from tools.retrieval_function import retrieval

app = FastAPI(title="GapTutor AI Backend", version="1.0")

# Enable CORS for Next.js frontend calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EVAL_DIR = os.path.join(WORKSPACE_DIR, "eval")
RUNS_DIR = os.path.join(EVAL_DIR, "runs")

class ChatHistoryItem(BaseModel):
    role: str
    content: str

class DiagnoseRequest(BaseModel):
    session_id: str
    query: str
    history: Optional[List[Dict[str, str]]] = None

@app.get("/api/v1/eval-cases")
def get_eval_cases():
    results = {}
    
    # Read eval_cases.json and eval_cases_resume.json if they exist
    files = ["eval_cases.json", "eval_cases_resume.json"]
    for filename in files:
        filepath = os.path.join(EVAL_DIR, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Convert the "lab3_style" cases format to the UI-compatible format expected by the frontend
                converted_cases = []
                for case in data.get("eval_cases", []):
                    expected_citations = case.get("expected_citations", [])
                    if not expected_citations and case.get("expected_citation"):
                        expected_citations = [case.get("expected_citation")]
                        
                    converted_cases.append({
                        "id": case.get("id"),
                        "phase": data.get("version", "1.0"),
                        "query": case.get("user_query"),
                        "expect": {
                            "no_tool": len(case.get("dataset_sources", [])) == 0,
                            "behavior": f"Trích dẫn: {', '.join(expected_citations) if expected_citations else 'None'}. Từ khóa mong đợi: {', '.join(case.get('expected_answer_contains', []))}",
                            "tool_calls": [
                                {
                                    "name": "summarize",
                                    "args": {
                                        "query": case.get("user_query")
                                    }
                                }
                            ] if len(case.get("dataset_sources", [])) > 0 else []
                        },
                        "metadata": {
                            "skill": case.get("group"),
                            "difficulty": "medium",
                            "what_it_tests": case.get("expected_trace", {}).get("reasoning_quality", "Đánh giá chất lượng tóm tắt & trích dẫn")
                        }
                    })
                results[filename] = converted_cases
            except Exception as e:
                print(f"Error loading {filename}: {e}")
                
    return results

@app.get("/api/v1/runs")
def get_runs():
    runs_list = []
    if os.path.exists(RUNS_DIR):
        json_files = glob.glob(os.path.join(RUNS_DIR, "*.json"))
        for filepath in sorted(json_files, key=os.path.getmtime, reverse=True):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    run_data = json.load(f)
                    runs_list.append(run_data)
            except Exception as e:
                print(f"Error loading run file {filepath}: {e}")
    return runs_list

@app.get("/api/v1/version-log")
def get_version_log():
    # Return empty log data or parse artifacts/version_log.csv if present
    # Matches the columns expected by version-log-viewer.tsx
    return {"headers": [], "rows": []}

@app.post("/api/v1/diagnose")
def diagnose(payload: DiagnoseRequest):
    try:
        query = payload.query
        
        # 1. Start timer to measure execution trace latency
        start_time = time.perf_counter()
        
        # 2. Call our summarize tool implementation
        result = summarize(query=query)
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        # 3. Build step-by-step reasoning steps for frontend visual trace logs
        steps = []
        
        # Step 1: Query analysis
        steps.append({
            "id": "step-init",
            "title": "Intention & Query Analysis",
            "kind": "thought",
            "content": f"Phân tích câu hỏi: '{query}'. Chế độ chạy: {result.get('mode', 'auto')}.",
            "durationMs": 5
        })
        
        # Step 2: Retrieval simulation
        citations = result.get("citations", [])
        retrieved_ids = [c.get("source_id") for c in citations if c.get("source_id")]
        
        steps.append({
            "id": "step-retrieve",
            "title": "Retrieve Lecture Context",
            "kind": "tool",
            "toolName": "retrieval",
            "content": f"Tìm kiếm trong tri thức slide. Kết quả khớp slide IDs: {retrieved_ids if retrieved_ids else 'Không tìm thấy'}.",
            "durationMs": int(duration_ms * 0.4),
            "input": {"content": query},
            "output": {"citations": citations}
        })
        
        # Step 3: Synthesis
        steps.append({
            "id": "step-synth",
            "title": "Formulate grounded answer",
            "kind": "thought",
            "content": f"Tổng hợp câu trả lời từ dữ liệu slide. Độ tự tin (confidence): {result.get('confidence')}.",
            "durationMs": int(duration_ms * 0.6)
        })
        
        # Format final summary answer
        summary_text = result.get("summary", "")
        citation_str = result.get("citation", "")
        if citation_str and "Không tìm thấy" not in citation_str:
            summary_text += f"\n\n*Nguồn trích dẫn: {citation_str}*"
            
        return {
            "summary": summary_text,
            "steps": steps
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import time
>>>>>>> a2097643c394ac0ce38584f8875848c59b45fd03
