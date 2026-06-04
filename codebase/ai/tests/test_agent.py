import unittest
import json
from tempfile import TemporaryDirectory
from pathlib import Path

from agent import (
    AgentTraceLogger,
    ReActAgent,
    ScriptedLLMProvider,
    Tool,
    ToolExecutor,
    make_slide_search_tool,
    parse_react_response,
    strip_model_observations,
)


class ReActParserTests(unittest.TestCase):
    def test_parse_action_json_and_ignore_model_written_observation(self):
        raw = """Thought: I should search trusted slide data.
Action: search_slide_sources
Action Input: {"query": "AI failure path", "limit": 2}
Observation: This is invented by the model and must be ignored.
Final Answer: This should not be accepted before the real tool runs.
"""

        parsed = parse_react_response(raw)

        self.assertEqual(parsed.kind, "action")
        self.assertEqual(parsed.tool_name, "search_slide_sources")
        self.assertEqual(parsed.tool_args, {"query": "AI failure path", "limit": 2})
        self.assertNotIn("invented by the model", strip_model_observations(raw))

    def test_parse_final_answer_when_no_action_exists(self):
        parsed = parse_react_response(
            "Thought: I have enough evidence.\nFinal Answer: Đây là câu trả lời cuối."
        )

        self.assertEqual(parsed.kind, "final")
        self.assertIn("câu trả lời cuối", parsed.final_answer)


class ToolExecutorTests(unittest.TestCase):
    def test_execute_tool_with_dict_arguments(self):
        tool = Tool(
            name="echo",
            description="Echo a query.",
            input_format='{"query": "text"}',
            func=lambda query: {"echo": query},
        )

        result = ToolExecutor([tool]).execute("echo", {"query": "hello"})

        self.assertTrue(result.ok)
        self.assertIn("hello", result.observation)

    def test_missing_tool_and_missing_function_are_safe_errors(self):
        executor = ToolExecutor(
            [
                Tool(
                    name="placeholder",
                    description="Tool sẽ được merge sau.",
                    input_format='{"query": "text"}',
                    func=None,
                )
            ]
        )

        missing = executor.execute("unknown", {"query": "x"})
        missing_func = executor.execute("placeholder", {"query": "x"})

        self.assertFalse(missing.ok)
        self.assertIn("not found", missing.observation)
        self.assertFalse(missing_func.ok)
        self.assertIn("missing function", missing_func.observation)


class ReActAgentTests(unittest.TestCase):
    def test_agent_runs_tool_then_uses_real_observation_only(self):
        calls = []

        def search_slide_sources(query, limit=3):
            calls.append({"query": query, "limit": limit})
            return {
                "matches": [
                    {
                        "source_id": "DAY05-S005",
                        "summary": "Failure không chỉ nằm ở model mà còn ở trách nhiệm và UX.",
                        "citation_label": "Day 05 Batch 02, slide 5",
                    }
                ],
                "citations": ["DAY05-S005"],
            }

        llm = ScriptedLLMProvider(
            [
                """Thought: Need slide evidence.
Action: search_slide_sources
Action Input: {"query": "AI đúng gần đủ vẫn fail", "limit": 1}
Observation: fake observation from model
""",
                """Thought: The real observation has the needed source.
Final Answer: AI đúng gần đủ vẫn có thể làm product thất bại nếu thiếu trách nhiệm, UX recovery và khả năng sửa output.

Nguồn:
- [DAY05-S005] Day 05 Batch 02, slide 5
""",
            ]
        )
        tool = Tool(
            name="search_slide_sources",
            description="Search mock Day 05 slide source data.",
            input_format='{"query": "student question", "limit": 3}',
            func=search_slide_sources,
        )

        result = ReActAgent(llm=llm, tools=[tool], max_steps=3).answer(
            "Vì sao AI đúng gần đủ vẫn có thể làm product gãy?"
        )

        self.assertIn("product thất bại", result.final_answer)
        self.assertEqual(calls, [{"query": "AI đúng gần đủ vẫn fail", "limit": 1}])
        self.assertEqual(len(result.trace), 2)
        self.assertIn("DAY05-S005", result.trace[0].observation)
        self.assertNotIn("fake observation from model", llm.prompts[1])

    def test_agent_result_exports_full_trace_for_logging(self):
        llm = ScriptedLLMProvider(
            [
                """Thought: Need slide evidence.
Action: search_slide_sources
Action Input: {"query": "failure path", "limit": 1}
""",
                """Thought: The tool returned enough evidence.
Final Answer: Trả lời: Có citation.

Nguồn:
- [DAY05-S005] Day 05 Batch 02, slide 5
""",
            ]
        )
        tool = Tool(
            name="search_slide_sources",
            description="Search mock data.",
            input_format='{"query": "text", "limit": 1}',
            func=lambda query, limit=1: {
                "matches": [{"source_id": "DAY05-S005"}],
                "citations": ["DAY05-S005"],
            },
        )

        result = ReActAgent(llm=llm, tools=[tool], max_steps=2).answer(
            "Failure path là gì?"
        )
        payload = result.to_dict()

        self.assertTrue(payload["completed"])
        self.assertIn("Có citation", payload["final_answer"])
        self.assertEqual(payload["trace"][0]["thought"], "Need slide evidence.")
        self.assertEqual(payload["trace"][0]["tool_name"], "search_slide_sources")
        self.assertEqual(payload["trace"][0]["tool_args"]["query"], "failure path")
        self.assertIn("DAY05-S005", payload["trace"][0]["observation"])
        self.assertEqual(
            payload["trace"][1]["thought"],
            "The tool returned enough evidence.",
        )

    def test_trace_logger_appends_jsonl_run(self):
        llm = ScriptedLLMProvider(
            [
                """Thought: Need slide evidence.
Action: search_slide_sources
Action Input: {"query": "Air Canada", "limit": 1}
""",
                """Thought: Enough evidence.
Final Answer: Trả lời: Bài học là phải có UX recovery.

Nguồn:
- [DAY05-S005] Day 05 Batch 02, slide 5
""",
            ]
        )
        tool = Tool(
            name="search_slide_sources",
            description="Search mock data.",
            input_format='{"query": "text", "limit": 1}',
            func=lambda query, limit=1: {
                "matches": [{"source_id": "DAY05-S005"}],
                "citations": ["DAY05-S005"],
            },
        )
        result = ReActAgent(llm=llm, tools=[tool], max_steps=2).answer(
            "Bài học từ Air Canada chatbot là gì?"
        )

        with TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "agent_trace.jsonl"
            written_path = AgentTraceLogger(log_path).append(
                user_input="Bài học từ Air Canada chatbot là gì?",
                result=result,
                metadata={"session_id": "demo-session"},
            )

            line = written_path.read_text(encoding="utf-8").strip()
            payload = json.loads(line)

        self.assertEqual(payload["user_input"], "Bài học từ Air Canada chatbot là gì?")
        self.assertEqual(payload["metadata"]["session_id"], "demo-session")
        self.assertIn("UX recovery", payload["final_answer"])
        self.assertEqual(payload["trace"][0]["tool_name"], "search_slide_sources")
        self.assertIn("DAY05-S005", payload["trace"][0]["observation"])

    def test_slide_search_tool_returns_citations_from_mock_data(self):
        repo_root = Path(__file__).resolve().parents[3]
        data_path = repo_root / "02-group-spec" / "data" / "day05_ai_tutor_slide_sources.json"
        tool = make_slide_search_tool(data_path)

        result = tool.func(query="Air Canada chatbot", limit=2)

        self.assertTrue(result["matches"])
        self.assertIn("citations", result)
        self.assertTrue(any("DAY05" in citation for citation in result["citations"]))


if __name__ == "__main__":
    unittest.main()
