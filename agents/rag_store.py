"""Retrieve versioned guideline references for general educational Q&A."""

import re

from data.cpic_knowledge import GUIDELINES


def get_rag_collection():
    return GUIDELINES


def retrieve_context(query: str) -> str:
    tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
    matches = [
        f"- {drug.title()} / {gene} — [{version}]({source})"
        for drug, (gene, version, source, _) in GUIDELINES.items()
        if drug in tokens or gene.lower() in tokens
    ]
    return "\n".join(matches)
