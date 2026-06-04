import sys
import os
import json
import time
from datetime import datetime

# Adjust python path to include codebase/ai so imports resolve correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Path definitions
WORKSPACE_DIR = os.path.abspath(os.path.join(current_dir, ".."))
EVAL_CASES_PATH = os.path.join(WORKSPACE_DIR, "eval", "eval_cases_resume.json")
RUNS_DIR = os.path.join(WORKSPACE_DIR, "eval", "runs")

try:
    from tools.summarize.tool import summarize
except ImportError as e:
    print(f"Error: Could not import 'summarize' tool. Make sure to run this script with python path set correctly. Details: {e}")
    sys.exit(1)

def run_case(case):
    query = case.get("user_query", "")
    expected_sources = case.get("dataset_sources", [])
    expected_keywords = case.get("expected_answer_contains", [])
    
    start_time = time.perf_counter()
    try:
        actual_result = summarize(query=query)
        success = True
        error_msg = None
    except Exception as e:
        actual_result = None
        success = False
        error_msg = str(e)
    duration_ms = (time.perf_counter() - start_time) * 1000
    
    failures = []
    
    if not success:
        failures.append(f"Tool crashed with exception: {error_msg}")
        return {
            "passed": False,
            "duration_ms": duration_ms,
            "failures": failures,
            "actual_text": None,
            "actual_tool_calls": [{"name": "summarize", "args": {"query": query}}],
            "actual_result": None
        }
        
    actual_text = actual_result.get("summary", "") or ""
    actual_citations = actual_result.get("citations", []) or []
    actual_source_ids = [c.get("source_id") for c in actual_citations if c.get("source_id")]
    
    # 1. Check sources
    for expected_src in expected_sources:
        if expected_src not in actual_source_ids:
            failures.append(f"Expected source '{expected_src}' not found in actual citations {actual_source_ids}")
            
    # 2. Check keywords
    for keyword in expected_keywords:
        if keyword.lower() not in actual_text.lower():
            failures.append(f"Expected keyword '{keyword}' not found in summary response")
            
    # 3. Check guardrail for empty/low confidence cases
    if len(expected_sources) == 0:
        if actual_result.get("confidence") != "low":
            failures.append(f"Expected low confidence for out-of-domain/guardrail query, but got '{actual_result.get('confidence')}'")
            
    passed = len(failures) == 0
    return {
        "passed": passed,
        "duration_ms": duration_ms,
        "failures": failures,
        "actual_text": actual_text,
        "actual_tool_calls": [{"name": "summarize", "args": {"query": query}}],
        "actual_result": actual_result
    }

def main():
    print("=" * 60)
    print("RUNNING RESUME/SUMMARIZE TOOL EVALUATION RUNNER")
    print(f"Cases File: {EVAL_CASES_PATH}")
    print("=" * 60)
    
    if not os.path.exists(EVAL_CASES_PATH):
        print(f"Error: Eval cases file not found at {EVAL_CASES_PATH}")
        sys.exit(1)
        
    with open(EVAL_CASES_PATH, "r", encoding="utf-8") as f:
        suite_data = json.load(f)
        
    cases = suite_data.get("eval_cases", [])
    suite_name = suite_data.get("eval_suite_name", "resume_tool_eval_suite")
    version = suite_data.get("version", "1.0")
    
    total_cases = len(cases)
    passed_count = 0
    results = []
    
    for case in cases:
        case_id = case.get("id")
        group = case.get("group")
        query = case.get("user_query")
        
        print(f"Running [{case_id}] ({group}) -> '{query}'...")
        res = run_case(case)
        
        if res["passed"]:
            print(f"  \033[92m[PASS]\033[0m Latency: {res['duration_ms']:.2f}ms")
            passed_count += 1
        else:
            print(f"  \033[91m[FAIL]\033[0m Latency: {res['duration_ms']:.2f}ms")
            for fail in res["failures"]:
                print(f"    - {fail}")
                
        results.append({
            "id": case_id,
            "phase": "1",
            "suite": suite_name,
            "input": query,
            "expect": case,
            "result": {
                "passed": res["passed"],
                "actual_text": res["actual_text"],
                "failures": res["failures"],
                "observed_mismatch": res["failures"][0] if res["failures"] else None,
                "actual_tool_calls": res["actual_tool_calls"]
            }
        })
        print("-" * 60)
        
    accuracy = (passed_count / total_cases) * 100 if total_cases > 0 else 0
    print(f"\nEvaluation complete. Passed: {passed_count}/{total_cases} ({accuracy:.1f}%)")
    
    # Save the run report
    os.makedirs(RUNS_DIR, exist_ok=True)
    run_id = f"run_resume_{int(time.time())}"
    generated_at = datetime.utcnow().isoformat() + "Z"
    
    run_detail = {
        "fileName": f"{run_id}.json",
        "runId": run_id,
        "version": version,
        "suite": suite_name,
        "provider": "heuristic_python_rules",
        "model": "summarize-tool-v1",
        "generatedAt": generated_at,
        "summary": {
            "total_cases": total_cases,
            "measured_cases": total_cases,
            "passed_cases": passed_count,
            "case_accuracy": passed_count / total_cases if total_cases > 0 else 0.0
        },
        "results": results
    }
    
    run_file_path = os.path.join(RUNS_DIR, f"{run_id}.json")
    with open(run_file_path, "w", encoding="utf-8") as f:
        json.dump(run_detail, f, indent=2, ensure_ascii=False)
        
    print(f"Saved run report to {run_file_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
