from __future__ import annotations

import unittest

from tools.summarize.tool import _key_points, _summary, summarize


class SummarizeToolTest(unittest.TestCase):
    def test_chunking_query_returns_chunking_source(self) -> None:
        result = summarize("Tom tat chunking anh huong retrieval quality")

        self.assertEqual(result["confidence"], "high")
        self.assertEqual(result["citations"][0]["source_id"], "SRC-W08-S005")

    def test_rag_query_returns_rag_source(self) -> None:
        result = summarize("RAG la gi")

        self.assertEqual(result["confidence"], "high")
        self.assertEqual(result["citations"][0]["source_id"], "SRC-W08-S002")

    def test_unknown_query_returns_low_confidence(self) -> None:
        result = summarize("Quantum computing la gi")

        self.assertEqual(result["confidence"], "low")
        self.assertEqual(result["citations"], [])

    def test_draft_source_is_not_used(self) -> None:
        result = summarize("Tom tat build slice")

        source_ids = [item["source_id"] for item in result.get("citations", [])]
        self.assertNotIn("SRC-W02-S007", source_ids)

    def test_lab_answer_request_is_guarded(self) -> None:
        result = summarize("Lam ho em bai lab RAG hoan chinh")

        self.assertEqual(result["confidence"], "low")
        self.assertEqual(result["citations"], [])
        self.assertIn("khong lam ho", result["summary"])

    def test_workshop_mode_returns_multiple_citations(self) -> None:
        result = summarize("Tom tat workshop 8")

        self.assertEqual(result["confidence"], "high")
        self.assertEqual(result["mode"], "workshop")
        self.assertEqual(
            [item["source_id"] for item in result["citations"]],
            ["SRC-W08-S002", "SRC-W08-S005"],
        )

    def test_explicit_workshop_mode_uses_workshop_no(self) -> None:
        result = summarize("Tom tat noi dung workshop", mode="workshop", workshop_no=8)

        self.assertEqual(result["confidence"], "high")
        self.assertGreaterEqual(len(result["citations"]), 2)

    def test_workshop_mode_respects_max_sources(self) -> None:
        result = summarize("Tom tat workshop 1", max_sources=2)

        self.assertEqual(result["mode"], "workshop")
        self.assertEqual(len(result["citations"]), 2)

    def test_draft_observability_does_not_match_generic_deploy_source(self) -> None:
        result = summarize("Sau khi deploy AI app can theo doi gi")

        self.assertEqual(result["confidence"], "low")
        self.assertEqual(result["citations"], [])

    def test_long_slide_text_uses_relevant_chunks(self) -> None:
        source = {
            "source_id": "SRC-LONG",
            "section_title": "RAG pipeline deep dive",
            "learning_objective": "Hoc vien hieu pipeline.",
            "summary": "Slide dai ve nhieu chu de RAG.",
            "source_excerpt": "RAG pipeline gom nhieu buoc.",
            "citation_label": "Workshop 8 - RAG Pipeline, slide long",
            "content": (
                "Phan dau noi ve lich hoc va cach lam viec nhom. "
                "Noi dung nay khong lien quan den retrieval quality. "
                "Chunking anh huong retrieval quality vi chunk qua ngan lam mat ngu canh. "
                "Chunk qua dai co the dua qua nhieu thong tin nhieu vao retrieval. "
                "Metadata va overlap giup he thong truy xuat dung ngu canh hon."
            ),
        }

        summary = _summary(source, query="chunking retrieval quality")
        key_points = _key_points(source, query="chunking retrieval quality")

        self.assertIn("Chunking", summary)
        self.assertIn("retrieval quality", summary)
        self.assertLessEqual(len(key_points), 3)


if __name__ == "__main__":
    unittest.main()
