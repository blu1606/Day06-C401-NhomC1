def retrieval(content: str) -> dict:
    """
    Hàm lấy dữ liệu cho các công cụ Explain và Summarize.

    Args:
        content (str): Nội dung cần lấy dữ liệu.

    Returns:
        dict: Một từ điển chứa dữ liệu lấy được và thông tin citation.
    """
    # Logic để lấy dữ liệu từ nguồn
    data = fetch_data(content)  # Giả sử có một hàm fetch_data để lấy dữ liệu
    citation = generate_citation(content)  # Giả sử có một hàm generate_citation để tạo citation

    return {
        "data": data,
        "citation": citation
    }