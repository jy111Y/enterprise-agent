from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@dataclass
class DocumentChunk:
    chunk_id: str     #片段唯一编号
    source: str       #来源文件名
    content: str

@dataclass
class SearchResult:       #搜索结果
    chunk_id: str
    source: str
    content: str
    score: float       #相似度分数

def split_text(          #文本切分
        text: str,
        chunk_size: int = 300,      #切片大小
        overlap: int = 50,          #重叠部分
) -> list[str]:
    """将文本切分成带重叠区域的片段"""

    text = text.strip()

    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size必须大于0")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap必须大于等于0且小于chunk_size")
    """重叠部分如果大于切片长度会导致下一段起点停止前进,可能导致死循环"""

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)   #将当前带值切片放入chunks列表中

        if end == len(text):
            break
        start = end - overlap

    return chunks


def load_documents(data_dir: Path) -> list[DocumentChunk]:
    """读取 data 目录中的所有 txt 文件并返回DocumentChunk列表。"""

    chunks: list[DocumentChunk] = []

    for file_path in sorted(data_dir.glob("*.txt")):    #sorted是为了使文件顺序更稳定
        text = file_path.read_text(encoding="utf-8")
        file_chunks = split_text(text)     #调用文本切分函数

        for index,content in enumerate(file_chunks):
            """enumerate列举出index索引,content内容"""
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{file_path.stem}-{index}",
                    source=file_path.name,
                    content=content,
                )
            )


    if not chunks:
        raise RuntimeError(f"没有在 {data_dir} 中找到可用文档")

    return chunks

class TfidfRetriever:        #用于检索的类
    """适合中文小型知识库的检索基线。"""

    def __init__(self,chunks: list[DocumentChunk]) -> None:
        self.chunks = chunks

        self.vectorizer = TfidfVectorizer(
            analyzer="char",     #按字符分析
            ngram_range=(2,4),   #连续2到4个字符作为特征
            min_df=1,     #表示一个特征至少出现在一个文档中才保留
        )

        self.document_vectors = self.vectorizer.fit_transform(  #fit学习，将所有文本块转换成TF-IDF向量
            [chunk.content for chunk in chunks]
        )

    def search(
            self,
            query: str,
            top_k: int = 3,
    ) -> list[SearchResult]:
        if not query.strip():
            return []

        query_vector = self.vectorizer.transform([query])
        """这里不用fit_transform是因为之前已经用文档训练好了词汇表,现在查询也必须用同一个词汇表"""

        scores = cosine_similarity(  #计算余弦相似度
            query_vector,
            self.document_vectors,
        )[0]   #[0]用于将结果变成一维数组

        result_count = min(top_k, len(self.chunks))  #防止top_k>chunks中的最大数量
        top_indices = np.argsort(scores)[::-1][:result_count]
        """np.argsort(scores) 返回的是“从小到大排序后的索引"""
        """[::-1] 是 Python 切片反转，把升序变成降序："""
        """相当于最后是从大到小的顺序，top_k取前面几个"""

        results: list[SearchResult] = []

        for index in top_indices:  #indices是index的复数，索引
            chunk = self.chunks[int(index)]

            results.append(
                SearchResult(
                    chunk_id=chunk.chunk_id,
                    source=chunk.source,
                    content=chunk.content,
                    score=float(scores[index]),
                )
            )

        return results

# txt 文件
#   -> 读取
#   -> 切分成 chunk
#   -> TF-IDF 向量化
#   -> 查询向量化
#   -> 余弦相似度排序
#   -> 返回 top_k 结果