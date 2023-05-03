from pydantic import BaseModel, Field
from src.utils.database.database import supabase
from src.tools.context import ToolContext
from src.utils.embeddings import get_embedding_sync

# pydantic model for the document tool


class SaveDocumentToolInput(BaseModel):
    """Input for the document tool."""

    title: str = Field(..., description="name of file")
    document: str = Field(..., description="content of file")


def save_document(title: str, document: str, tool_context: ToolContext):
    normalized_title = title.lower().strip().replace(" ", "_")
    embedding = get_embedding_sync(f"""{title} ({normalized_title})
{document}""")
    supabase.table("Documents").insert(
        {"title": title, "normalized_title": normalized_title, "content": document, "agent_id": str(tool_context.agent_id), "embedding": embedding}
    ).execute()
    return f"Document saved: {title}"


class ReadDocumentToolInput(BaseModel):
    """Input for the document tool."""

    title: str = Field(..., description="name of file")


def read_document(title: str, tool_context: ToolContext):
    normalized_title = title.lower().strip().replace(" ", "_")
    try:
        document = supabase.table("Documents").select("*").eq("normalized_title", normalized_title).execute().data[0]["content"]
    except:
        return f"Document not found: {title}"
    return f"""Document found: {title}
Content:
{document}"""


class SearchDocumentsToolInput(BaseModel):
    """Input for the document tool."""

    query: str = Field(..., description="document query")


def search_documents(query: str, tool_context: ToolContext):
    embedding = get_embedding_sync(query)
    documents = supabase.rpc("match_documents", {"query_embedding": embedding, "match_threshold": 0.78, "match_count": 10}).execute().data
    if len(documents) == 0:
        return f"No documents found for query: {query}"
    document_names = "\"" + "\"\n\"".join(map(lambda document: document["title"], documents)) + "\""
    return f"""Documents found for query "{query}": 
{document_names}"""
