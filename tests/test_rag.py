from pathlib import Path

from app.rag import TfidfRetriever, load_documents, split_text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

def test_split_text_has_overlap() -> None:
    text = "A" * 500

    chunks = split_text(
        text,
        chunk_size=300,
        overlap=50,
    )

    # assert len(chunks) == 2
    # assert chunks[0][-50:] == chunks[1][:50]
    """assert表示我必须保证这个条件为真"""

    assert len(chunks) == 2
    assert len(chunks[0]) == 300
    assert len(chunks[1]) == 250
    """这样更严谨一些, 因为字符串是五百个A"""

def test_load_documents() -> None:
    chunks = load_documents(DATA_DIR)

    assert len(chunks) >= 3
    assert all(chunk.source.endswith(".txt") for chunk in chunks)
    """all(...) 表示“里面所有元素都为真，才返回 True”。
    里遍历每个 chunk,检查它的 source 是不是以 .txt 结尾。"""

def test_remote_work_retrieval() -> None:  #测试验证检索功能
    chunks = load_documents(DATA_DIR)
    retriever = TfidfRetriever(chunks)

    results = retriever.search(
        "每个月最多可以远程办公几天?",
        top_k=3,
    )

    assert results
    assert results[0].source == "employee_handbook.txt"
    assert "四天" in results[0].content

def test_reimbursement_retrieval() -> None:
    chunks = load_documents(DATA_DIR)
    retriever = TfidfRetriever(chunks)

    results = retriever.search(
        "费用发生后多久需要报销?",
         top_k=3,
    )

    assert results
    assert results[0].source == "reimbursement_policy.txt"
    assert "三十个自然日" in results[0].content