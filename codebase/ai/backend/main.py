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
