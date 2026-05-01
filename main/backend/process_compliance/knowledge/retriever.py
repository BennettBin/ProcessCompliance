from __future__ import annotations

from typing import List


def retrieve_texts(vectorstore, query: str, top_k: int = 5) -> List[str]:
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": max(1, int(top_k))},
    )
    docs = retriever.invoke(query)
    return [getattr(d, "page_content", str(d)) for d in docs]

