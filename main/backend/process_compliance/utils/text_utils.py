from __future__ import annotations

from typing import Any, Dict, List

def int_to_ordinal_word(number: int) -> str:
    ordinals = {
        1: "first",
        2: "second",
        3: "third",
        4: "fourth",
        5: "fifth",
        6: "sixth",
        7: "seventh",
        8: "eighth",
        9: "ninth",
        10: "tenth",
    }
    return ordinals.get(number, str(number))


def trans_case_to_text(case: List[Dict[str, Any]]) -> str:
    if not case:
        return "The trace is empty."
    case_id = case[0].get("case", "unknown_case")
    text = f"The trace of the event log with case number '{case_id}' is as follows: "
    for i, event in enumerate(case):
        text += (
            f"The {int_to_ordinal_word(i + 1)} event was completed by "
            f"'{event.get('org:resource', 'unknown_resource')}' for Activity "
            f"'{event.get('concept:name', 'unknown_activity')}', "
            f"taking {event.get('executionTimeD', 0)} days; "
        )
    return text


def split_document(doc_path: str):
    from langchain_community.document_loaders import TextLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    loader = TextLoader(doc_path, encoding="utf-8-sig")
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", ",", ";", "!", "?"],
    )
    return splitter.split_documents(docs)
