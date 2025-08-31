import os
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import asyncio
import json

# Supabase imports
from supabase import create_client, Client
import numpy as np

from models.schemas import Document, DocumentChunk, SearchFilters
from services.multimodal_embedder import MultimodalEmbedder

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.supabase: Optional[Client] = None
        self.embedder: Optional[MultimodalEmbedder] = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize Supabase client and embedding model"""
        try:
            # Initialize Supabase
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_ANON_KEY")
            
            if supabase_url and supabase_key:
                self.supabase = create_client(supabase_url, supabase_key)
                logger.info("Supabase client initialized successfully")
            else:
                logger.warning("Supabase credentials not found, using local storage")
            
            # Initialize multimodal embedder
            self.embedder = MultimodalEmbedder()
            logger.info("Vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            # Fallback to local storage
            self.supabase = None
            self.embedder = None
    
    async def add_document(self, document: Document, chunks: List[DocumentChunk] = None) -> bool:
        """Add document and its chunks to vector store"""
        try:
            # Process chunks with multimodal embeddings
            if chunks and self.embedder:
                chunks = await self.embedder.process_document_chunks(document, chunks)
            
            if self.supabase:
                return await self._add_to_supabase(document, chunks or [])
            else:
                return await self._add_to_local(document, chunks or [])
        except Exception as e:
            logger.error(f"Error adding document {document.id}: {e}")
            raise
    
    async def _add_to_supabase(self, document: Document, chunks: List[DocumentChunk]) -> bool:
        """Add document to Supabase"""
        try:
            # Insert document metadata
            doc_data = {
                "id": document.id,
                "title": document.title,
                "content": document.content,
                "summary": document.summary,
                "tags": document.tags,
                "file_type": document.file_type.value,
                "file_path": document.file_path,
                "size_bytes": document.size_bytes,
                "uploaded_at": document.uploaded_at.isoformat(),
                "processed_at": document.processed_at.isoformat() if document.processed_at else None
            }
            
            result = self.supabase.table("documents").insert(doc_data).execute()
            
            # Insert chunks with embeddings
            for chunk in chunks:
                if not chunk.embedding and self.embedder:
                    # Generate embedding if not present
                    chunk.embedding = await self.embedder.embed_text(chunk.content)
                
                chunk_data = {
                    "id": chunk.id,
                    "document_id": chunk.document_id,
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "word_count": chunk.word_count,
                    "embedding": chunk.embedding
                }
                
                self.supabase.table("document_chunks").insert(chunk_data).execute()
            
            logger.info(f"Successfully added document {document.id} to Supabase")
            return True
            
        except Exception as e:
            logger.error(f"Error adding to Supabase: {e}")
            raise
    
    async def _add_to_local(self, document: Document, chunks: List[DocumentChunk]) -> bool:
        """Fallback: store document locally (for development)"""
        try:
            # Create local storage directory
            storage_dir = "local_storage"
            os.makedirs(storage_dir, exist_ok=True)
            
            # Save document metadata
            doc_file = os.path.join(storage_dir, f"{document.id}.json")
            doc_data = document.model_dump()
            doc_data["uploaded_at"] = doc_data["uploaded_at"].isoformat()
            if doc_data["processed_at"]:
                doc_data["processed_at"] = doc_data["processed_at"].isoformat()
            
            with open(doc_file, 'w') as f:
                json.dump(doc_data, f, indent=2)
            
            # Save chunks
            for chunk in chunks:
                if not chunk.embedding and self.embedder:
                    chunk.embedding = await self.embedder.embed_text(chunk.content)
                
                chunk_file = os.path.join(storage_dir, f"chunk_{chunk.id}.json")
                with open(chunk_file, 'w') as f:
                    json.dump(chunk.model_dump(), f, indent=2)
            
            logger.info(f"Successfully added document {document.id} to local storage")
            return True
            
        except Exception as e:
            logger.error(f"Error adding to local storage: {e}")
            raise
    
    async def search_similar(self, query: str, filters: Optional[SearchFilters] = None, top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        """Search for similar document chunks"""
        try:
            if not self.embedder:
                return []
            
            # Generate query embedding
            query_embedding = await self.embedder.embed_text(query)
            
            if self.supabase:
                return await self._search_supabase(query_embedding, filters, top_k)
            else:
                return await self._search_local(query_embedding, filters, top_k)
                
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
    
    async def _search_supabase(self, query_embedding: List[float], filters: Optional[SearchFilters], top_k: int) -> List[Tuple[DocumentChunk, float]]:
        """Search using Supabase vector similarity"""
        try:
            # Build query with vector similarity
            query_builder = self.supabase.table("document_chunks").select(
                "*, documents!document_chunks_document_id_fkey(*)"
            )
            
            # Apply filters if provided
            if filters:
                if filters.tags:
                    query_builder = query_builder.in_("documents.tags", filters.tags)
                if filters.file_types:
                    file_types = [ft.value for ft in filters.file_types]
                    query_builder = query_builder.in_("documents.file_type", file_types)
            
            # Execute similarity search (simplified - would need proper vector search in production)
            result = query_builder.limit(top_k * 2).execute()  # Get more to filter
            
            # Calculate similarities locally (in production, use database vector search)
            chunks_with_scores = []
            for row in result.data:
                if row['embedding']:
                    similarity = self._cosine_similarity(query_embedding, row['embedding'])
                    
                    if not filters or not filters.min_relevance_score or similarity >= filters.min_relevance_score:
                        chunk = DocumentChunk(
                            id=row['id'],
                            document_id=row['document_id'],
                            content=row['content'],
                            chunk_index=row['chunk_index'],
                            word_count=row['word_count'],
                            embedding=row['embedding']
                        )
                        chunks_with_scores.append((chunk, similarity))
            
            # Sort by similarity and return top_k
            chunks_with_scores.sort(key=lambda x: x[1], reverse=True)
            return chunks_with_scores[:top_k]
            
        except Exception as e:
            logger.error(f"Error in Supabase search: {e}")
            return []
    
    async def _search_local(self, query_embedding: List[float], filters: Optional[SearchFilters], top_k: int) -> List[Tuple[DocumentChunk, float]]:
        """Search using local storage"""
        try:
            storage_dir = "local_storage"
            if not os.path.exists(storage_dir):
                return []
            
            chunks_with_scores = []
            
            # Load all chunks and calculate similarities
            for filename in os.listdir(storage_dir):
                if filename.startswith("chunk_") and filename.endswith(".json"):
                    chunk_file = os.path.join(storage_dir, filename)
                    
                    with open(chunk_file, 'r') as f:
                        chunk_data = json.load(f)
                    
                    if chunk_data.get('embedding'):
                        similarity = self._cosine_similarity(query_embedding, chunk_data['embedding'])
                        
                        if not filters or not filters.min_relevance_score or similarity >= filters.min_relevance_score:
                            chunk = DocumentChunk(**chunk_data)
                            chunks_with_scores.append((chunk, similarity))
            
            # Sort by similarity and return top_k
            chunks_with_scores.sort(key=lambda x: x[1], reverse=True)
            return chunks_with_scores[:top_k]
            
        except Exception as e:
            logger.error(f"Error in local search: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            a = np.array(vec1)
            b = np.array(vec2)
            return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
        except:
            return 0.0
    
    async def get_documents(self, skip: int = 0, limit: int = 50) -> List[Document]:
        """Get list of documents"""
        try:
            if self.supabase:
                result = self.supabase.table("documents").select("*").range(skip, skip + limit - 1).execute()
                return [self._dict_to_document(doc) for doc in result.data]
            else:
                return await self._get_local_documents(skip, limit)
        except Exception as e:
            logger.error(f"Error getting documents: {e}")
            return []
    
    async def _get_local_documents(self, skip: int, limit: int) -> List[Document]:
        """Get documents from local storage"""
        storage_dir = "local_storage"
        if not os.path.exists(storage_dir):
            return []
        
        documents = []
        doc_files = [f for f in os.listdir(storage_dir) if f.endswith('.json') and not f.startswith('chunk_')]
        
        for filename in doc_files[skip:skip + limit]:
            doc_file = os.path.join(storage_dir, filename)
            with open(doc_file, 'r') as f:
                doc_data = json.load(f)
            documents.append(self._dict_to_document(doc_data))
        
        return documents
    
    def _dict_to_document(self, doc_data: Dict[str, Any]) -> Document:
        """Convert dictionary to Document model"""
        # Handle datetime strings
        if isinstance(doc_data.get('uploaded_at'), str):
            doc_data['uploaded_at'] = datetime.fromisoformat(doc_data['uploaded_at'])
        if isinstance(doc_data.get('processed_at'), str):
            doc_data['processed_at'] = datetime.fromisoformat(doc_data['processed_at'])
        
        return Document(**doc_data)
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete document and its chunks"""
        try:
            if self.supabase:
                # Delete chunks first
                self.supabase.table("document_chunks").delete().eq("document_id", document_id).execute()
                # Delete document
                self.supabase.table("documents").delete().eq("id", document_id).execute()
            else:
                # Delete from local storage
                storage_dir = "local_storage"
                doc_file = os.path.join(storage_dir, f"{document_id}.json")
                if os.path.exists(doc_file):
                    os.remove(doc_file)
                
                # Delete chunks
                for filename in os.listdir(storage_dir):
                    if filename.startswith("chunk_") and filename.endswith(".json"):
                        chunk_file = os.path.join(storage_dir, filename)
                        with open(chunk_file, 'r') as f:
                            chunk_data = json.load(f)
                        
                        if chunk_data.get('document_id') == document_id:
                            os.remove(chunk_file)
            
            return True
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check vector store health"""
        status = "healthy"
        details = {}
        
        try:
            if self.supabase:
                # Test Supabase connection
                result = self.supabase.table("documents").select("count", count="exact").execute()
                details["supabase"] = "connected"
                details["document_count"] = result.count
            else:
                details["supabase"] = "not_configured"
                storage_dir = "local_storage"
                if os.path.exists(storage_dir):
                    doc_count = len([f for f in os.listdir(storage_dir) 
                                   if f.endswith('.json') and not f.startswith('chunk_')])
                    details["local_document_count"] = doc_count
            
            details["embedder"] = "available" if self.embedder else "not_available"
            
        except Exception as e:
            status = "unhealthy"
            details["error"] = str(e)
        
        return {"status": status, **details}