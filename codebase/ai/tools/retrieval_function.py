import os
import json
import unicodedata

def remove_diacritics(text: str) -> str:
    """
    Loại bỏ dấu tiếng Việt để đối sánh chính xác hơn.
    """
    if not text:
        return ""
    normalized = unicodedata.normalize('NFKD', text)
    no_diacritics = "".join([c for c in normalized if not unicodedata.combining(c)])
    return no_diacritics.replace('đ', 'd').replace('Đ', 'd')

def retrieval(content: str) -> dict:
    """
    Hàm lấy dữ liệu cho các công cụ Explain và Summarize.

    Args:
        content (str): Nội dung cần lấy dữ liệu.

    Returns:
        dict: Một từ điển chứa dữ liệu lấy được và thông tin citation.
    """
    # 1. Đường dẫn động tới thư mục chứa dữ liệu mock
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "02-group-spec", "data"))
    
    files_to_load = [
        "mock_ai_tutor_slide_sources.json",
        "day05_ai_tutor_slide_sources.json"
    ]
    
    records = []
    for file_name in files_to_load:
        file_path = os.path.join(data_dir, file_name)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "records" in data and isinstance(data["records"], list):
                        records.extend(data["records"])
            except Exception:
                pass

    if not records:
        return {
            "data": {
                "source_id": None,
                "source_type": None,
                "section_title": "Lỗi hệ thống",
                "summary": "Không thể tải dữ liệu mock hoặc thư mục rỗng.",
                "source_excerpt": "Lỗi đọc dữ liệu.",
                "learning_objective": None,
                "skill_tags": []
            },
            "citation": "Không xác định"
        }

    # 2. Chuẩn hóa truy vấn tìm kiếm và lọc stopword
    query_normalized = remove_diacritics(content).lower().strip()
    stopwords = {"la", "gi", "khong", "co", "va", "cua", "cho", "de", "trong", "mot", "nay", "voi", "den", "nao", "the", "lam", "ho", "ai", "em", "vi", "sao", "ve", "cac", "nhung", "thi"}
    query_tokens = [
        token for token in query_normalized.split() 
        if len(token) >= 2 and token not in stopwords
    ]

    best_record = None
    best_score = -1

    for record in records:
        score = 0
        
        # Lấy các trường tìm kiếm chính và chuẩn hóa
        section_title = remove_diacritics(record.get("section_title", "")).lower()
        summary = remove_diacritics(record.get("summary", "")).lower()
        source_excerpt = remove_diacritics(record.get("source_excerpt", "")).lower()
        learning_objective = remove_diacritics(record.get("learning_objective", "")).lower()
        
        skill_tags = [remove_diacritics(tag).lower() for tag in record.get("skill_tags", [])]
        example_student_questions = [remove_diacritics(q).lower() for q in record.get("example_student_questions", [])]

        # A. So khớp chuỗi đầy đủ (Substring match của toàn bộ query)
        if query_normalized:
            # So khớp trong tag
            if any(query_normalized == tag for tag in skill_tags):
                score += 100
            elif any(query_normalized in tag for tag in skill_tags):
                score += 50
                
            # So khớp trong tiêu đề chương
            if query_normalized in section_title:
                score += 80
            
            # So khớp trong câu hỏi ví dụ
            if any(query_normalized in q for q in example_student_questions):
                score += 60
                
            # So khớp trong nội dung khác
            if query_normalized in summary:
                score += 40
            if query_normalized in source_excerpt:
                score += 40
            if query_normalized in learning_objective:
                score += 30

        # B. So khớp theo từ khóa (Token match)
        for token in query_tokens:
            if any(token in tag for tag in skill_tags):
                score += 15
            if token in section_title:
                score += 10
            if any(token in q for q in example_student_questions):
                score += 8
            if token in summary:
                score += 5
            if token in source_excerpt:
                score += 5
            if token in learning_objective:
                score += 4

        # Cập nhật kết quả tốt nhất
        if score > best_score:
            best_score = score
            best_record = record

    # 3. Trả về kết quả
    if best_record and best_score >= 30:
        return {
            "data": {
                "source_id": best_record.get("source_id"),
                "source_type": best_record.get("source_type"),
                "section_title": best_record.get("section_title"),
                "summary": best_record.get("summary"),
                "source_excerpt": best_record.get("source_excerpt"),
                "learning_objective": best_record.get("learning_objective"),
                "skill_tags": best_record.get("skill_tags")
            },
            "citation": best_record.get("citation_label", "Nguồn học liệu")
        }
    
    # Fallback khi không tìm thấy slide nào phù hợp
    return {
        "data": {
            "source_id": None,
            "source_type": None,
            "section_title": "Không tìm thấy tài liệu phù hợp",
            "summary": "Không tìm thấy nội dung bài học nào phù hợp với câu hỏi.",
            "source_excerpt": "Không tìm thấy đoạn trích phù hợp.",
            "learning_objective": None,
            "skill_tags": []
        },
        "citation": "Không tìm thấy nguồn phù hợp"
    }