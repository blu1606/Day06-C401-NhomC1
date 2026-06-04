from __future__ import annotations

import json
import re
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol
from uuid import uuid4


class LLMProvider(Protocol):
    """Small interface used by ReActAgent.

    A real provider can call OpenAI, Azure OpenAI, Gemini, a local model, or a
    test double. The agent only needs generated text and optional usage data.
    """

    def generate(self, prompt: str) -> str | "LLMResponse":
        ...


@dataclass
class LLMResponse:
    text: str
    usage: dict[str, Any] | None = None


class ScriptedLLMProvider:
    """Deterministic provider for tests and local demos."""

    def __init__(self, responses: list[str | LLMResponse]):
        self.responses = list(responses)
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str | LLMResponse:
        self.prompts.append(prompt)
        if not self.responses:
            raise RuntimeError("ScriptedLLMProvider has no response left.")
        return self.responses.pop(0)


@dataclass
class Tool:
    name: str
    description: str
    input_format: str
    func: Callable[..., Any] | None = None


@dataclass
class ToolExecutionResult:
    ok: bool
    observation: str
    raw: Any = None
    elapsed_ms: float = 0.0
    error: str | None = None


@dataclass
class ParsedReActResponse:
    kind: str
    thought: str = ""
    tool_name: str | None = None
    tool_args: Any = None
    final_answer: str = ""
    error: str | None = None
    sanitized_text: str = ""


@dataclass
class AgentStep:
    step_index: int
    prompt: str
    llm_response: str
    sanitized_response: str
    parsed_kind: str
    thought: str = ""
    tool_name: str | None = None
    tool_args: Any = None
    observation: str = ""
    elapsed_ms: float = 0.0
    usage: dict[str, Any] | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "prompt": self.prompt,
            "llm_response": self.llm_response,
            "sanitized_response": self.sanitized_response,
            "parsed_kind": self.parsed_kind,
            "thought": self.thought,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "observation": self.observation,
            "elapsed_ms": self.elapsed_ms,
            "usage": self.usage,
            "error": self.error,
        }


@dataclass
class AgentResult:
    final_answer: str
    trace: list[AgentStep] = field(default_factory=list)
    completed: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "final_answer": self.final_answer,
            "completed": self.completed,
            "trace": [step.to_dict() for step in self.trace],
        }


class AgentTraceLogger:
    """Append complete agent runs to a JSONL file."""

    def __init__(self, log_path: str | Path):
        self.log_path = Path(log_path)

    def append(
        self,
        user_input: str,
        result: AgentResult,
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "run_id": str(uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "user_input": user_input,
            "metadata": metadata or {},
            **result.to_dict(),
        }
        with self.log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False, default=str))
            file.write("\n")
        return self.log_path


_OBSERVATION_RE = re.compile(r"^\s*Observation\s*:", re.IGNORECASE)
_LABEL_RE = re.compile(
    r"^\s*(Thought|Action|Action Input|Final Answer|Observation)\s*:",
    re.IGNORECASE,
)


def strip_model_observations(text: str) -> str:
    """Remove Observation blocks written by the model.

    Runtime observations must come from tools. If a model prints its own
    Observation, it is treated as untrusted scratch text and removed before
    parsing or adding to the next prompt.
    """

    kept: list[str] = []
    skipping_observation = False
    for line in text.splitlines():
        if _OBSERVATION_RE.match(line):
            skipping_observation = True
            continue
        if skipping_observation and _LABEL_RE.match(line):
            skipping_observation = False
        if not skipping_observation:
            kept.append(line)
    return "\n".join(kept).strip()


def _extract_block(text: str, label: str, stop_labels: tuple[str, ...]) -> str:
    stop_pattern = "|".join(re.escape(stop_label) for stop_label in stop_labels)
    pattern = re.compile(
        rf"^\s*{re.escape(label)}\s*:\s*(.*?)(?=^\s*(?:{stop_pattern})\s*:|\Z)",
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def _parse_action_input(raw_input: str) -> Any:
    if not raw_input:
        return {}

    candidate = raw_input.strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return candidate


def parse_react_response(text: str) -> ParsedReActResponse:
    sanitized = strip_model_observations(text)
    thought = _extract_block(
        sanitized,
        "Thought",
        ("Action", "Action Input", "Final Answer", "Observation"),
    )

    action_match = re.search(
        r"^\s*Action\s*:\s*([A-Za-z0-9_.-]+)\s*$",
        sanitized,
        re.IGNORECASE | re.MULTILINE,
    )
    if action_match:
        raw_input = _extract_block(
            sanitized,
            "Action Input",
            ("Thought", "Action", "Final Answer", "Observation"),
        )
        return ParsedReActResponse(
            kind="action",
            thought=thought,
            tool_name=action_match.group(1).strip(),
            tool_args=_parse_action_input(raw_input),
            sanitized_text=sanitized,
        )

    final_answer = _extract_block(
        sanitized,
        "Final Answer",
        ("Thought", "Action", "Action Input", "Observation"),
    )
    if final_answer:
        return ParsedReActResponse(
            kind="final",
            thought=thought,
            final_answer=final_answer,
            sanitized_text=sanitized,
        )

    return ParsedReActResponse(
        kind="invalid",
        thought=thought,
        error="Model output must contain either Action or Final Answer.",
        sanitized_text=sanitized,
    )


def _jsonish(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


class ToolExecutor:
    def __init__(self, tools: list[Tool]):
        self.tools = {tool.name: tool for tool in tools}

    def execute(self, tool_name: str | None, args: Any) -> ToolExecutionResult:
        started = time.perf_counter()
        if not tool_name or tool_name not in self.tools:
            return ToolExecutionResult(
                ok=False,
                observation=f"Tool not found: {tool_name}",
                elapsed_ms=_elapsed_ms(started),
                error="tool_not_found",
            )

        tool = self.tools[tool_name]
        if tool.func is None:
            return ToolExecutionResult(
                ok=False,
                observation=f"Tool '{tool_name}' missing function.",
                elapsed_ms=_elapsed_ms(started),
                error="tool_missing_function",
            )

        try:
            if args is None:
                raw = tool.func()
            elif isinstance(args, dict):
                raw = tool.func(**args)
            else:
                raw = tool.func(args)
            return ToolExecutionResult(
                ok=True,
                observation=_jsonish(raw),
                raw=raw,
                elapsed_ms=_elapsed_ms(started),
            )
        except TypeError as exc:
            return ToolExecutionResult(
                ok=False,
                observation=f"Tool '{tool_name}' argument error: {exc}",
                elapsed_ms=_elapsed_ms(started),
                error="tool_argument_error",
            )
        except Exception as exc:
            return ToolExecutionResult(
                ok=False,
                observation=f"Tool '{tool_name}' runtime error: {exc}",
                elapsed_ms=_elapsed_ms(started),
                error="tool_runtime_error",
            )


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 3)


def _normalize_text(value: Any) -> str:
    text = str(value).lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return text


def _record_haystack(record: dict[str, Any]) -> str:
    parts = [
        record.get("source_id", ""),
        record.get("section_title", ""),
        record.get("learning_objective", ""),
        record.get("summary", ""),
        record.get("source_excerpt", ""),
        record.get("citation_label", ""),
        " ".join(record.get("skill_tags", [])),
        " ".join(record.get("example_student_questions", [])),
    ]
    return _normalize_text(" ".join(str(part) for part in parts))


def load_slide_source_records(data_path: str | Path) -> list[dict[str, Any]]:
    path = Path(data_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    records = data.get("records", [])
    if not isinstance(records, list):
        raise ValueError("Slide source data must contain a list field named 'records'.")
    return records


def search_slide_source_records(
    records: list[dict[str, Any]],
    query: str,
    limit: int = 3,
) -> dict[str, Any]:
    normalized_query = _normalize_text(query)
    tokens = [token for token in re.split(r"\W+", normalized_query) if len(token) >= 2]
    scored: list[tuple[int, dict[str, Any]]] = []

    for record in records:
        haystack = _record_haystack(record)
        score = sum(1 for token in tokens if token in haystack)
        if normalized_query and normalized_query in haystack:
            score += 5
        if score > 0:
            scored.append((score, record))

    scored.sort(key=lambda item: (-item[0], item[1].get("slide_no", 0)))
    matches = []
    for score, record in scored[: max(1, int(limit))]:
        matches.append(
            {
                "source_id": record.get("source_id"),
                "slide_no": record.get("slide_no"),
                "section_title": record.get("section_title"),
                "summary": record.get("summary"),
                "source_excerpt": record.get("source_excerpt"),
                "citation_label": record.get("citation_label"),
                "score": score,
            }
        )

    return {
        "query": query,
        "matches": matches,
        "citations": [
            match["source_id"] for match in matches if match.get("source_id")
        ],
    }


def make_slide_search_tool(data_path: str | Path) -> Tool:
    records = load_slide_source_records(data_path)

    def search_slide_sources(query: str, limit: int = 3) -> dict[str, Any]:
        return search_slide_source_records(records=records, query=query, limit=limit)

    return Tool(
        name="search_slide_sources",
        description=(
            "Search mock Day 05 slide source records and return concise evidence "
            "with source_id/citation_label for citations."
        ),
        input_format='{"query": "student question or concept", "limit": 3}',
        func=search_slide_sources,
    )


def _tools_prompt(tools: list[Tool]) -> str:
    lines = []
    for tool in tools:
        lines.append(
            f"- {tool.name}: {tool.description}\n  Input: {tool.input_format}"
        )
    return "\n".join(lines) if lines else "- No tools registered."


def build_system_prompt(tools: list[Tool]) -> str:
    return f"""Bạn là AI Tutor hỗ trợ sinh viên học kiến thức từ slide đã được duyệt.

Bạn có các tool sau:
{_tools_prompt(tools)}

Luật bắt buộc:
- Nếu câu hỏi cần kiến thức từ slide hoặc citation, hãy gọi tool trước khi trả lời.
- Chỉ runtime được viết Observation. Bạn không được tự viết hoặc bịa Observation.
- Không bịa citation. Chỉ dùng source_id/citation_label có trong Observation thật.
- Nếu tool không tìm thấy nguồn phù hợp, nói rõ là chưa đủ nguồn trong mock data.
- Khi đã có đủ bằng chứng, trả lời bằng tiếng Việt, ngắn gọn, dễ hiểu cho sinh viên.

Định dạng khi cần gọi tool:
Thought: lý do ngắn
Action: tool_name
Action Input: JSON hợp lệ hoặc text

Định dạng khi kết thúc:
Thought: lý do ngắn
Final Answer: câu trả lời cuối

Trong Final Answer nên có:
Trả lời: ...

Nguồn:
- [source_id] citation_label
"""


def _scratchpad_text_before_runtime_observation(raw_model_text: str) -> str:
    kept: list[str] = []
    for line in raw_model_text.splitlines():
        if _OBSERVATION_RE.match(line) or re.match(
            r"^\s*Final Answer\s*:", line, re.IGNORECASE
        ):
            break
        kept.append(line)
    return "\n".join(kept).strip()


class ReActAgent:
    def __init__(
        self,
        llm: LLMProvider,
        tools: list[Tool],
        max_steps: int = 5,
        system_prompt: str | None = None,
        trace_logger: AgentTraceLogger | None = None,
        trace_metadata: dict[str, Any] | None = None,
    ):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.executor = ToolExecutor(tools)
        self.system_prompt = system_prompt or build_system_prompt(tools)
        self.trace_logger = trace_logger
        self.trace_metadata = trace_metadata or {}

    def answer(self, user_input: str) -> AgentResult:
        trace: list[AgentStep] = []
        scratchpad = ""

        for step_index in range(1, self.max_steps + 1):
            prompt = self._build_prompt(user_input=user_input, scratchpad=scratchpad)
            started = time.perf_counter()
            response = self.llm.generate(prompt)
            elapsed_ms = _elapsed_ms(started)
            response_text, usage = self._unpack_llm_response(response)
            parsed = parse_react_response(response_text)

            if parsed.kind == "final":
                trace.append(
                    AgentStep(
                        step_index=step_index,
                        prompt=prompt,
                        llm_response=response_text,
                        sanitized_response=parsed.sanitized_text,
                        parsed_kind=parsed.kind,
                        thought=parsed.thought,
                        elapsed_ms=elapsed_ms,
                        usage=usage,
                    )
                )
                result = AgentResult(
                    final_answer=parsed.final_answer,
                    trace=trace,
                    completed=True,
                )
                self._persist_trace(user_input=user_input, result=result)
                return result

            if parsed.kind == "action":
                tool_result = self.executor.execute(parsed.tool_name, parsed.tool_args)
                observation = tool_result.observation
                scratch_model_text = _scratchpad_text_before_runtime_observation(
                    response_text
                )
                scratchpad = (
                    f"{scratchpad}\n\n{scratch_model_text}\n"
                    f"Observation: {observation}"
                ).strip()
                trace.append(
                    AgentStep(
                        step_index=step_index,
                        prompt=prompt,
                        llm_response=response_text,
                        sanitized_response=parsed.sanitized_text,
                        parsed_kind=parsed.kind,
                        thought=parsed.thought,
                        tool_name=parsed.tool_name,
                        tool_args=parsed.tool_args,
                        observation=observation,
                        elapsed_ms=round(elapsed_ms + tool_result.elapsed_ms, 3),
                        usage=usage,
                        error=tool_result.error,
                    )
                )
                continue

            observation = f"Parser error: {parsed.error}"
            scratchpad = (
                f"{scratchpad}\n\n{parsed.sanitized_text}\nObservation: {observation}"
            ).strip()
            trace.append(
                AgentStep(
                    step_index=step_index,
                    prompt=prompt,
                    llm_response=response_text,
                    sanitized_response=parsed.sanitized_text,
                    parsed_kind=parsed.kind,
                    thought=parsed.thought,
                    observation=observation,
                    elapsed_ms=elapsed_ms,
                    usage=usage,
                    error=parsed.error,
                )
            )

        result = AgentResult(
            final_answer=(
                "Mình chưa thể hoàn tất câu trả lời trong giới hạn bước hiện tại. "
                "Hãy thử hỏi hẹp hơn hoặc tăng max_steps."
            ),
            trace=trace,
            completed=False,
        )
        self._persist_trace(user_input=user_input, result=result)
        return result

    def _build_prompt(self, user_input: str, scratchpad: str) -> str:
        return f"""{self.system_prompt}

Câu hỏi của sinh viên:
{user_input}

Scratchpad hiện tại:
{scratchpad if scratchpad else "(chưa có)"}

Hãy sinh bước tiếp theo theo đúng định dạng ReAct.
"""

    def _persist_trace(self, user_input: str, result: AgentResult) -> None:
        if self.trace_logger is not None:
            self.trace_logger.append(
                user_input=user_input,
                result=result,
                metadata=self.trace_metadata,
            )

    @staticmethod
    def _unpack_llm_response(response: Any) -> tuple[str, dict[str, Any] | None]:
        if isinstance(response, LLMResponse):
            return response.text, response.usage
        if hasattr(response, "text"):
            return getattr(response, "text"), getattr(response, "usage", None)
        return str(response), None
