import ast
from typing import Optional
import numpy as np
from pydantic import BaseModel, Field

from src.tools.context import ToolContext
from src.utils.database.base import Tables
from src.utils.database.client import get_database
from src.utils.embeddings import cosine_similarity, get_embedding

# pydantic model for the document tool


class SaveDocumentToolInput(BaseModel):
    """Input for the document tool."""

    title: str = Field(..., description="name of file")
    document: str = Field(..., description="content of file")


async def save_document(title: str, document: str, tool_context: ToolContext):
    normalized_title = title.lower().strip().replace(" ", "_")

    await (await get_database()).insert_document_with_embedding(
        {
            "title": title,
            "normalized_title": normalized_title,
            "content": document,
            "agent_id": str(tool_context.agent_id),
        },
        f"""{title} ({normalized_title})
{document}""",
    )

    return f"Document saved: {title}"


class ReadDocumentToolInput(BaseModel):
    """Input for the document tool."""

    title: str = Field(..., description="name of file")


async def read_document(title: str, tool_context: ToolContext):
    normalized_title = title.lower().strip().replace(" ", "_")
    try:
        document = (
            await (await get_database()).get_by_field(
                Tables.Documents, "normalized_title", normalized_title
            )
        )[0]["content"]
    except Exception:
        return f"Document not found: {title}"
    return f"""Document found: {title}
Content:
{document}"""


class SearchDocumentsToolInput(BaseModel):
    """Input for the document tool."""

    query: str = Field(..., description="document query")


async def search_documents(query: str, tool_context: Optional[ToolContext]):
    documents = await (await get_database()).get_all(Tables.Documents)

    # get top 10 documents from embedding cosine similarity

    query_embedding = await get_embedding(query)

    def get_similarity(document) -> float:
        # TODO: get working on sqlite
        embedding = (
            np.array(document["embedding"][1:-1].split(","), dtype=float)
            if type(document["embedding"]) == str
            else np.array(document["embedding"])
        )

        return cosine_similarity(embedding, query_embedding)

    similar_documents = sorted(
        documents,
        key=lambda document: get_similarity(document),
        reverse=True,
    )[:10]

    document_titles = (
        '"'
        + '"\n"'.join(map(lambda document: f'- {document["title"]}', similar_documents))
        + '"'
    )
    return f"""The following documents were found for the query "{query}":

     {document_titles}
    """
