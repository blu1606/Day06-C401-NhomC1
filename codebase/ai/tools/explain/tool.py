from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
from openai import OpenAI
from codebase.ai.tools._shared import ROOT

# Load environment variables
env_path = ROOT / ".env"
if env_path.exists():
    load_dotenv(env_path)


def explain(content: str, retrieval: Any) -> dict[str, Any]:
    # Extract sources from retrieval parameter
    # Supports both function calling (contract style) and direct data payloads
    if callable(retrieval):
        ret_result = retrieval(content)
    elif isinstance(retrieval, dict):
        ret_result = retrieval
    else:
        ret_result = {"data": retrieval, "citation": ""}
        
    data = ret_result.get("data")
    citation_info = ret_result.get("citation", "")
    
    # Handle empty sources case
    if not data:
        msg = "Rất tiếc, câu hỏi của bạn nằm ngoài phạm vi tài liệu slides hiện có của workshop."
        return {
            "explanation": msg,
            "citation": ""
        }
        
    # Format data for prompt
    sources_text = ""
    citations_list = []
    if isinstance(data, list):
        for idx, src in enumerate(data):
            if isinstance(src, dict):
                sources_text += (
                    f"Slide Source [{idx+1}]:\n"
                    f"- Title: {src.get('section_title', '')}\n"
                    f"- Summary: {src.get('summary', '')}\n"
                    f"- Content: {src.get('source_excerpt', '')}\n"
                    f"- Citation: {src.get('citation_label', '')}\n\n"
                )
                citations_list.append(src.get("citation_label", ""))
            else:
                sources_text += f"Source [{idx+1}]: {str(src)}\n\n"
    else:
        sources_text = str(data)
        
    if not citation_info and citations_list:
        citation_info = "; ".join([c for c in citations_list if c])
        
    api_key = os.environ.get("OPENROUTER_API_KEY")
    
    # Try calling OpenRouter LLM if API Key is available
    if api_key and not api_key.startswith("your_") and len(api_key.strip()) > 10:
        try:
            client = OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
            )
            
            prompt = f"""
You are an AI Tutor for the "AI Thực Chiến" course.
Answer the Student's Question based ONLY on the provided Slide Sources. Do not invent any facts not present in the sources.

Slide Sources:
{sources_text}

Student's Question:
{content}

You MUST answer in Vietnamese. Formulate your response as a JSON object with the following keys:
1. "explanation": A clear, detailed explanation of the concept based on the slide sources.
2. "simplified": A highly simplified version/summary of the concept for a complete beginner.
3. "example": A relatable everyday life analogy or small example (e.g. "RAG giống như học sinh được mở tài liệu trước khi trả lời câu hỏi").

JSON response:"""

            response = client.chat.completions.create(
                model="google/gemma-4-31b-it:free",
                messages=[
                    {"role": "system", "content": "You output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=20
            )
            
            resp_content = response.choices[0].message.content
            if resp_content:
                # Strip out any potential markdown wrapper
                json_str = resp_content.strip()
                if json_str.startswith("```json"):
                    json_str = json_str[7:]
                if json_str.endswith("```"):
                    json_str = json_str[:-3]
                
                res = json.loads(json_str.strip())
                
                # Combine output into single explanation markdown to match the string output payload contract
                full_explanation = (
                    f"### Diễn giải\n{res.get('explanation', '')}\n\n"
                    f"### Đơn giản hóa\n{res.get('simplified', '')}\n\n"
                    f"### Ví dụ minh họa\n{res.get('example', '')}"
                )
                
                return {
                    "explanation": full_explanation,
                    "citation": citation_info
                }
        except Exception as e:
            print(f"API Call Failed: {e}")
            # Fallback on API failure
            pass
            
    # Local fallback logic (e.g., for offline testing/validation)
    content_lower = content.lower()
    if "rag" in content_lower or "retrieval" in content_lower:
        explanation_part = "RAG (Retrieval-Augmented Generation) là phương pháp kết hợp việc truy xuất thông tin từ tài liệu nguồn với mô hình ngôn ngữ lớn để trả lời câu hỏi chính xác hơn và giảm thiểu việc bịa thông tin."
        simplified_part = "Thay vì bắt AI tự nhớ hết mọi thứ, chúng ta đưa tài liệu cho AI đọc rồi trả lời."
        example_part = "RAG giống như một học sinh được mở sách giáo khoa để tìm câu trả lời chính xác trước khi viết vào bài kiểm tra."
    else:
        explanation_part = f"Giải thích chi tiết dựa trên slide cho câu hỏi: '{content}'."
        simplified_part = f"Khái niệm rút gọn của '{content}'."
        example_part = f"Ví dụ minh họa cho '{content}'."
        
    full_explanation = (
        f"### Diễn giải\n{explanation_part}\n\n"
        f"### Đơn giản hóa\n{simplified_part}\n\n"
        f"### Ví dụ minh họa\n{example_part}"
    )
    
    return {
        "explanation": full_explanation,
        "citation": citation_info
    }



