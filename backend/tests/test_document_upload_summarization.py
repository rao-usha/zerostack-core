"""Integration tests for document upload and summarization."""
import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from domains.contexts.service import ContextService
from domains.contexts.router import router
from fastapi import FastAPI


# Create a test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestDocumentUploadSummarization:
    """Test document upload with summarization."""
    
    @pytest.fixture
    def context_service(self):
        """Create a test context service."""
        return ContextService()
    
    @pytest.fixture
    def test_context_id(self, context_service):
        """Create a test context."""
        result = context_service.create_context(
            name="Test Context",
            org_id="demo"
        )
        return result["context_id"]
    
    def test_upload_with_auto_summarize_skipped_if_no_key(self, test_context_id):
        """Test that upload succeeds even if summarization is skipped due to no API key."""
        with patch('domains.contexts.service.DocumentSummarizer') as mock_summarizer_class:
            mock_summarizer = Mock()
            mock_summarizer.summarize.return_value = None
            mock_summarizer_class.return_value = mock_summarizer
            
            service = ContextService()
            service.summarizer = mock_summarizer
            
            from fastapi import UploadFile
            import io
            
            test_file = UploadFile(
                filename="test.txt",
                file=io.BytesIO(b"This is a test document with enough text for summarization. " * 10),
                headers={"content-type": "text/plain"}
            )
            
            # This should not raise an exception even if summarization fails
            result = await service.upload_document(
                context_id=test_context_id,
                file=test_file,
                auto_summarize=True
            )
            
            assert result is not None
            assert "document_id" in result
    
    def test_summarize_document_with_valid_key(self, test_context_id):
        """Test summarizing a document when API key is configured."""
        with patch('domains.contexts.service.DocumentSummarizer') as mock_summarizer_class:
            mock_summarizer = Mock()
            mock_summarizer.summarize.return_value = "This is a test summary of the document."
            mock_summarizer_class.return_value = mock_summarizer
            
            service = ContextService()
            service.summarizer = mock_summarizer
            
            # First upload a document
            from fastapi import UploadFile
            import io
            
            test_file = UploadFile(
                filename="test.txt",
                file=io.BytesIO(b"This is a test document with enough text for summarization. " * 10),
                headers={"content-type": "text/plain"}
            )
            
            upload_result = await service.upload_document(
                context_id=test_context_id,
                file=test_file,
                auto_summarize=False  # Don't auto-summarize
            )
            
            doc_id = upload_result["document_id"]
            
            # Now try to summarize
            summary = service.summarize_document(doc_id, style="concise")
            
            assert summary is not None
            assert summary == "This is a test summary of the document."
            mock_summarizer.summarize.assert_called_once()
    
    def test_summarize_document_without_key(self, test_context_id):
        """Test summarizing returns None when API key is not configured."""
        with patch('domains.contexts.service.DocumentSummarizer') as mock_summarizer_class:
            mock_summarizer = Mock()
            mock_summarizer.summarize.return_value = None  # Simulates no API key
            mock_summarizer_class.return_value = mock_summarizer
            
            service = ContextService()
            service.summarizer = mock_summarizer
            
            from fastapi import UploadFile
            import io
            
            test_file = UploadFile(
                filename="test.txt",
                file=io.BytesIO(b"This is a test document with enough text for summarization. " * 10),
                headers={"content-type": "text/plain"}
            )
            
            upload_result = await service.upload_document(
                context_id=test_context_id,
                file=test_file,
                auto_summarize=False
            )
            
            doc_id = upload_result["document_id"]
            
            # Try to summarize
            summary = service.summarize_document(doc_id, style="concise")
            
            assert summary is None
    
    def test_summarize_document_not_found(self):
        """Test that summarizing a non-existent document raises ValueError."""
        service = ContextService()
        
        with pytest.raises(ValueError, match="Document not found"):
            service.summarize_document(str(uuid.uuid4()), style="concise")
    
    def test_summarize_document_no_extractable_text(self, test_context_id):
        """Test that summarizing a document without extractable text returns None."""
        service = ContextService()
        
        from fastapi import UploadFile
        import io
        
        # Upload a binary file that can't be extracted
        test_file = UploadFile(
            filename="test.bin",
            file=io.BytesIO(b"\x00\x01\x02\x03" * 100),  # Binary data
            headers={"content-type": "application/octet-stream"}
        )
        
        upload_result = await service.upload_document(
            context_id=test_context_id,
            file=test_file,
            auto_summarize=False
        )
        
        doc_id = upload_result["document_id"]
        
        # Try to summarize - should return None due to no extractable text
        summary = service.summarize_document(doc_id, style="concise")
        
        assert summary is None


class TestSummarizationEndpoint:
    """Test the summarization API endpoint."""
    
    def test_summarize_endpoint_success(self):
        """Test successful summarization via API endpoint."""
        with patch('domains.contexts.service.ContextService') as mock_service_class:
            mock_service = Mock()
            mock_service.summarize_document.return_value = "Test summary"
            mock_service_class.return_value = mock_service
            
            # Note: This would require proper app setup with mocked service
            # For now, this is a placeholder for endpoint testing
            pass
    
    def test_summarize_endpoint_no_api_key(self):
        """Test endpoint returns 400 when API key is not configured."""
        with patch('domains.contexts.service.ContextService') as mock_service_class:
            mock_service = Mock()
            mock_service.summarize_document.return_value = None  # No API key
            mock_service_class.return_value = mock_service
            
            # Note: This would require proper app setup
            pass
    
    def test_summarize_endpoint_document_not_found(self):
        """Test endpoint returns 404 for non-existent document."""
        with patch('domains.contexts.service.ContextService') as mock_service_class:
            mock_service = Mock()
            mock_service.summarize_document.side_effect = ValueError("Document not found: test-id")
            mock_service_class.return_value = mock_service
            
            # Note: This would require proper app setup
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

