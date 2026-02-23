"""Search TEAM/ONDC knowledge base using RAG."""

from typing import Any

from src.tools.base import BaseTool
from src.core.logging import log


class SearchKnowledgeTool(BaseTool):
    """RAG search on TEAM scheme + ONDC knowledge base."""

    name = "search_knowledge"
    description = (
        "Search the TEAM initiative and ONDC knowledge base for information about "
        "ONDC network, SNPs, TEAM scheme eligibility, MSME onboarding process, etc. "
        "Use when the user asks about TEAM, ONDC, SNPs, or MSME onboarding."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query",
            },
            "limit": {
                "type": "integer",
                "description": "Max results to return (default 5)",
            },
        },
        "required": ["query"],
    }

    async def execute(self, arguments: dict[str, Any], context: dict[str, Any]) -> dict:
        query = arguments.get("query", "")
        limit = arguments.get("limit", 5)

        try:
            from src.rag.qdrant_search import QdrantSearch, KNOWLEDGE_COLLECTION
            results = QdrantSearch.search(
                query=query,
                collection_name=KNOWLEDGE_COLLECTION,
                limit=limit,
            )

            if not results:
                return {
                    "query": query,
                    "results": [],
                    "message": "No relevant information found. Please ask about ONDC, TEAM scheme, or SNPs.",
                }

            return {
                "query": query,
                "results": [
                    {"content": r["content"], "score": r["score"]}
                    for r in results
                ],
            }
        except Exception as e:
            log.error(f"search_knowledge failed: {e}")
            return {"query": query, "error": str(e)}
