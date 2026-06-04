import sys
import json

# Ensure stdout uses utf-8 on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from codebase.ai.tools.explain.tool import explain

def test_explain_tool_local():
    print("--- TESTING EXPLAIN TOOL LOCALLY ---")
    
    # Mock retrieval function matching the contract
    def mock_retrieval(query_content: str) -> dict:
        return {
            "data": [
                {
                    "source_id": "SRC-W08-S002",
                    "slide_no": 2,
                    "section_title": "RAG la gi",
                    "summary": "RAG giup AI tra loi dua tren tai lieu duoc truy xuat thay vi chi dua vao tri thuc san co cua model.",
                    "source_excerpt": "RAG = retrieve relevant context + generate grounded answer.",
                    "citation_label": "Workshop 8 - RAG Pipeline, slide 2, RAG la gi"
                }
            ],
            "citation": "Workshop 8 - RAG Pipeline, slide 2, RAG la gi"
        }
        
    test_query = "RAG là gì?"
    print(f"Query: '{test_query}'\n")
    
    result = explain(test_query, mock_retrieval)
    print("--- Tool Output ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Validation checks based on contract
    assert "explanation" in result, "Missing 'explanation' in output payload"
    assert "citation" in result, "Missing 'citation' in output payload"
    assert len(result["explanation"]) > 10, "Explanation should be a non-empty string"
    assert "### Diễn giải" in result["explanation"] and "### Ví dụ minh họa" in result["explanation"], "Explanation should contain formatted markdown sections"
    assert result["citation"] == "Workshop 8 - RAG Pipeline, slide 2, RAG la gi", "Citation should match retrieved label"
    
    print("\n[SUCCESS] Local test passed successfully and matches contract!")

if __name__ == "__main__":
    test_explain_tool_local()
