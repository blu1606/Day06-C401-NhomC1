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
