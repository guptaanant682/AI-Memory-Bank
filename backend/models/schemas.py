from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DocumentStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class FileType(str, Enum):
    PDF = "pdf"
    TXT = "txt"
    DOC = "doc"
    DOCX = "docx"
    MD = "md"

class Document(BaseModel):
    id: str = Field(..., description="Unique document identifier")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Full document content")
    summary: Optional[str] = Field(None, description="AI-generated summary")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    file_type: FileType = Field(..., description="File type")
    file_path: str = Field(..., description="Path to original file")
    size_bytes: int = Field(..., description="File size in bytes")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    chunk_ids: List[str] = Field(default_factory=list, description="Associated chunk IDs")

class DocumentChunk(BaseModel):
    id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document ID")
    content: str = Field(..., description="Chunk content")
    chunk_index: int = Field(..., description="Position in document")
    word_count: int = Field(..., description="Number of words in chunk")
    embedding: Optional[List[float]] = Field(None, description="Text embedding vector")

class SearchFilters(BaseModel):
    tags: Optional[List[str]] = None
    date_range: Optional[Dict[str, datetime]] = None
    file_types: Optional[List[FileType]] = None
    min_relevance_score: Optional[float] = Field(0.5, ge=0.0, le=1.0)

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User query")
    filters: Optional[SearchFilters] = None
    top_k: Optional[int] = Field(5, ge=1, le=20, description="Number of results to return")
    include_sources: bool = Field(True, description="Include source documents in response")

class QuerySource(BaseModel):
    document_id: str
    document_title: str
    chunk_content: str
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    chunk_index: int

class QueryResponse(BaseModel):
    answer: str = Field(..., description="Generated answer")
    sources: List[QuerySource] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0, description="Response confidence")
    processing_time_ms: int = Field(..., description="Query processing time")

class DocumentResponse(BaseModel):
    id: str
    title: str
    status: DocumentStatus
    message: str
    summary: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    uploaded_at: Optional[datetime] = None
    file_type: Optional[FileType] = None
    size_bytes: Optional[int] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, Any]

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)