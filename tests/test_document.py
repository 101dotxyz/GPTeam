import unittest
from unittest.mock import AsyncMock, Mock, patch

from src.tools.document import search_documents


class SearchDocumentsTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_matching_document_titles(self):
        database = Mock()
        database.search_document_embeddings = AsyncMock(
            return_value=[{"title": "Project Notes"}, {"title": "Meeting Log"}]
        )

        with patch(
            "src.tools.document.get_database", new=AsyncMock(return_value=database)
        ):
            result = await search_documents("project", None)

        database.search_document_embeddings.assert_awaited_once_with("project", 10)
        self.assertEqual(
            result,
            'Documents found for query "project":\n"Project Notes"\n"Meeting Log"',
        )

    async def test_reports_when_no_documents_match(self):
        database = Mock()
        database.search_document_embeddings = AsyncMock(return_value=[])

        with patch(
            "src.tools.document.get_database", new=AsyncMock(return_value=database)
        ):
            result = await search_documents("missing", None)

        self.assertEqual(result, "No documents found for query: missing")


if __name__ == "__main__":
    unittest.main()
