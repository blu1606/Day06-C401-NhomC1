from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import TOOL_FUNCTIONS
from tools.classify_question_scope.tool import classify_question_scope
from tools.generate_grounded_answer.tool import generate_grounded_answer
from tools.handle_low_confidence_answer.tool import handle_low_confidence_answer
from tools.list_tools.tool import list_tools
from tools.list_workshop_sources.tool import list_workshop_sources
from tools.retrieve_slide_sources.tool import retrieve_slide_sources
from tools.submit_answer_feedback.tool import submit_answer_feedback


class LearningAssistantToolsTest(unittest.TestCase):
    def test_retrieve_slide_sources_finds_chunking_source(self) -> None:
        result = retrieve_slide_sources(
            question="Chunking anh huong the nao den retrieval quality?",
            topK=2,
        )

        self.assertGreaterEqual(len(result["matches"]), 1)
        self.assertEqual(result["matches"][0]["sourceId"], "SRC-W08-S005")
        self.assertIn("citationLabel", result["matches"][0])

    def test_retrieve_slide_sources_prefers_exact_student_question(self) -> None:
        result = retrieve_slide_sources(
            question="AI product khác software product ở đâu?",
            topK=1,
        )

        self.assertEqual(result["matches"][0]["sourceId"], "DAY05-S008")

    def test_retrieve_slide_sources_respects_topk_and_published_only(self) -> None:
        result = retrieve_slide_sources(question="Build slice la gi?", topK=1)

        self.assertEqual(len(result["matches"]), 1)
        self.assertNotEqual(result["matches"][0]["sourceId"], "SRC-W02-S007")

    def test_retrieve_slide_sources_filters_workshop(self) -> None:
        result = retrieve_slide_sources(
            question="RAG la gi?",
            workshopNo=8,
            topK=3,
        )

        source_ids = [match["sourceId"] for match in result["matches"]]
        self.assertIn("SRC-W08-S002", source_ids)
        self.assertTrue(all(source_id.startswith("SRC-W08") for source_id in source_ids))

    def test_classify_question_scope_uses_match_score(self) -> None:
        result = classify_question_scope(
            question="Chunking la gi?",
            retrievedMatches=[{"sourceId": "SRC-W08-S005", "score": 0.8}],
        )

        self.assertEqual(result["scope"], "in_scope")
        self.assertGreaterEqual(result["confidence"], 0.55)

    def test_classify_question_scope_rejects_out_of_scope_advice(self) -> None:
        retrieved = retrieve_slide_sources(
            question="Cach dau tu chung khoan bang RAG?",
            topK=2,
        )
        result = classify_question_scope(
            question="Cach dau tu chung khoan bang RAG?",
            retrievedMatches=retrieved["matches"],
        )

        self.assertEqual(result["scope"], "out_of_scope")

    def test_classify_question_scope_returns_low_confidence_for_weak_match(self) -> None:
        result = classify_question_scope(
            question="Noi them ve retrieval",
            retrievedMatches=[{"sourceId": "SRC-W08-S002", "score": 0.3}],
        )

        self.assertEqual(result["scope"], "low_confidence")

    def test_classify_question_scope_returns_out_of_scope_without_matches(self) -> None:
        result = classify_question_scope(question="Noi ve chu de khong co trong slide")

        self.assertEqual(result["scope"], "out_of_scope")
        self.assertEqual(result["confidence"], 0.0)

    def test_generate_grounded_answer_returns_answer_example_and_citation(self) -> None:
        retrieved = retrieve_slide_sources(question="Tool calling la gi?", topK=1)
        result = generate_grounded_answer(
            question="Tool calling la gi?",
            sources=retrieved["matches"],
        )

        self.assertIn("answer", result)
        self.assertIn("example", result)
        self.assertEqual(result["citations"][0]["sourceId"], "SRC-W07-S004")

    def test_generate_grounded_answer_without_sources_errors_cleanly(self) -> None:
        result = generate_grounded_answer(question="Quantum computing la gi?", sources=[])

        self.assertEqual(result["answer"], "")
        self.assertEqual(result["citations"], [])
        self.assertIn("error", result)

    def test_generate_grounded_answer_supports_english_output(self) -> None:
        retrieved = retrieve_slide_sources(question="RAG la gi?", topK=1)
        result = generate_grounded_answer(
            question="What is RAG?",
            sources=retrieved["matches"],
            language="en",
        )

        self.assertIn("based only on the retrieved workshop source", result["answer"])
        self.assertTrue(result["example"].startswith("Simple example"))

    def test_low_confidence_answer_suggests_questions(self) -> None:
        result = handle_low_confidence_answer(
            question="Cach dau tu chung khoan bang RAG?",
            reason="out_of_scope",
        )

        self.assertIn("chua tim thay", result["message"])
        self.assertGreaterEqual(len(result["suggestedQuestions"]), 1)

    def test_low_confidence_answer_uses_closest_source_titles_without_duplication(self) -> None:
        result = handle_low_confidence_answer(
            question="Cach dau tu chung khoan bang RAG?",
            reason="out_of_scope",
            closestSources=[
                {
                    "sourceId": "SRC-W08-S002",
                    "sectionTitle": "RAG la gi",
                    "citationLabel": "Workshop 8 - RAG Pipeline, slide 2",
                    "score": 0.4,
                }
            ],
        )

        self.assertEqual(result["suggestedQuestions"][0], "Chunking trong RAG la gi?")

    def test_low_confidence_answer_uses_closest_titles_for_non_sensitive_low_confidence(self) -> None:
        result = handle_low_confidence_answer(
            question="Hoi lai ve RAG",
            reason="low_confidence",
            closestSources=[
                {
                    "sourceId": "SRC-W08-S002",
                    "sectionTitle": "RAG la gi",
                    "citationLabel": "Workshop 8 - RAG Pipeline, slide 2",
                    "score": 0.4,
                }
            ],
        )

        self.assertEqual(result["suggestedQuestions"][0], "RAG la gi")

    def test_submit_answer_feedback_writes_mock_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "feedback.jsonl"
            result = submit_answer_feedback(
                question="Chunking la gi?",
                sourceIds=["SRC-W08-S005"],
                feedbackType="wrong_citation",
                userRole="mentor",
                storage_path=str(storage_path),
            )

            self.assertTrue(result["saved"])
            self.assertEqual(result["nextAction"], "add_to_golden_test")
            self.assertTrue(storage_path.exists())

    def test_submit_answer_feedback_routes_student_unclear_to_mentor_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = submit_answer_feedback(
                question="RAG la gi?",
                feedbackType="unclear_answer",
                userRole="student",
                storage_path=str(Path(tmpdir) / "feedback.jsonl"),
            )

            self.assertEqual(result["nextAction"], "mentor_review")

    def test_submit_answer_feedback_routes_helpful_to_no_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = submit_answer_feedback(
                question="RAG la gi?",
                feedbackType="helpful",
                userRole="student",
                storage_path=str(Path(tmpdir) / "feedback.jsonl"),
            )

            self.assertEqual(result["nextAction"], "no_action")

    def test_list_workshop_sources_filters_published_workshop(self) -> None:
        result = list_workshop_sources(workshopNo=8, status="published")
        source_ids = {source["sourceId"] for source in result["sources"]}

        self.assertIn("SRC-W08-S002", source_ids)
        self.assertIn("SRC-W08-S005", source_ids)

    def test_list_workshop_sources_can_show_draft_for_admin_review(self) -> None:
        result = list_workshop_sources(workshopNo=2, status="draft")
        source_ids = {source["sourceId"] for source in result["sources"]}

        self.assertIn("SRC-W02-S007", source_ids)
        self.assertTrue(all(source["status"] == "draft" for source in result["sources"]))

    def test_list_workshop_sources_returns_ui_ready_fields(self) -> None:
        result = list_workshop_sources(workshopNo=8, status="published")
        required_fields = {
            "sourceId",
            "workshopTitle",
            "slideNo",
            "sectionTitle",
            "status",
            "citationLabel",
        }

        for source in result["sources"]:
            self.assertEqual(required_fields, set(source))
            self.assertTrue(source["citationLabel"])

    def test_list_tools_includes_requested_tools_and_registry(self) -> None:
        result = list_tools()
        tool_names = {tool["name"] for tool in result["tools"]}

        for name in [
            "retrieve_slide_sources",
            "classify_question_scope",
            "generate_grounded_answer",
            "handle_low_confidence_answer",
            "submit_answer_feedback",
            "list_workshop_sources",
            "list_tools",
        ]:
            self.assertIn(name, tool_names)
            self.assertIn(name, TOOL_FUNCTIONS)


if __name__ == "__main__":
    unittest.main()
