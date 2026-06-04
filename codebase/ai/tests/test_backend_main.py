import unittest
import sys
import json
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from agent import ScriptedLLMProvider
from backend.main import (
    DemoSlideTutorLLMProvider,
    create_agent,
    main,
    run_interactive,
    run_single_question,
)


class Cp1252Console:
    encoding = "cp1252"

    def __init__(self):
        self.buffer = BytesIO()

    def write(self, text):
        text.encode(self.encoding)
        return len(text)

    def flush(self):
        pass


class BackendMainTests(unittest.TestCase):
    def test_create_agent_wires_default_slide_tool(self):
        llm = ScriptedLLMProvider(
            [
                'Thought: Need source.\nAction: search_slide_sources\nAction Input: {"query": "Air Canada", "limit": 1}',
                "Thought: Done.\nFinal Answer: Trả lời: Có nguồn.\n\nNguồn:\n- [DAY05-S005] Day 05 Batch 02, slide 5",
            ]
        )

        agent = create_agent(llm=llm, max_steps=2)
        result = agent.answer("Bài học từ Air Canada chatbot là gì?")

        self.assertTrue(result.completed)
        self.assertIn("Có nguồn", result.final_answer)
        self.assertEqual(result.trace[0].tool_name, "search_slide_sources")

    def test_create_agent_can_persist_trace_log(self):
        llm = ScriptedLLMProvider(
            [
                'Thought: Need source.\nAction: search_slide_sources\nAction Input: {"query": "Air Canada", "limit": 1}',
                "Thought: Done.\nFinal Answer: Trả lời: Có log.\n\nNguồn:\n- [DAY05-S005] Day 05 Batch 02, slide 5",
            ]
        )

        with TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "agent-trace.jsonl"
            agent = create_agent(llm=llm, max_steps=2, trace_log_path=log_path)
            result = agent.answer("Bài học từ Air Canada chatbot là gì?")

            payload = json.loads(log_path.read_text(encoding="utf-8").strip())

        self.assertTrue(result.completed)
        self.assertEqual(payload["user_input"], "Bài học từ Air Canada chatbot là gì?")
        self.assertIn("Có log", payload["final_answer"])
        self.assertEqual(payload["trace"][0]["tool_name"], "search_slide_sources")

    def test_demo_provider_answers_terminal_question_through_react_loop(self):
        agent = create_agent(
            llm=DemoSlideTutorLLMProvider(),
            max_steps=2,
        )

        result = run_single_question(
            agent=agent,
            question="Bai hoc tu Air Canada chatbot la gi?",
        )

        self.assertTrue(result.completed)
        self.assertIn("Tra loi:", result.final_answer)
        self.assertIn("Nguon:", result.final_answer)
        self.assertEqual(result.trace[0].tool_name, "search_slide_sources")
        self.assertIn("Air Canada", result.trace[0].tool_args["query"])

    def test_interactive_loop_accepts_question_then_exit(self):
        agent = create_agent(
            llm=DemoSlideTutorLLMProvider(),
            max_steps=2,
        )
        inputs = iter(["Vi sao can thiet ke failure path?", "exit"])
        output = StringIO()

        run_interactive(
            agent=agent,
            input_func=lambda prompt: next(inputs),
            output_stream=output,
        )

        transcript = output.getvalue()
        self.assertIn("Tra loi:", transcript)
        self.assertIn("Nguon:", transcript)
        self.assertIn("Ket thuc", transcript)

    def test_main_writes_vietnamese_output_on_cp1252_console(self):
        original_stdout = sys.stdout
        fake_stdout = Cp1252Console()
        sys.stdout = fake_stdout
        try:
            main()
        finally:
            sys.stdout = original_stdout

        self.assertIn("Trả lời", fake_stdout.buffer.getvalue().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
