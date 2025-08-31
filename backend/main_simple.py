"""
AI Memory Bank - Simplified Backend
Minimal version that works without heavy AI dependencies
"""

import os
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Simple document models
class SimpleDocument:
    def __init__(self, id: str, filename: str, content: str, file_type: str):
        self.id = id
        self.filename = filename
        self.content = content
        self.file_type = file_type
        self.created_at = datetime.now()

# Create FastAPI app
app = FastAPI(
    title="AI Memory Bank API",
    description="Simplified AI-powered personal knowledge assistant",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory storage (replace with database in production)
documents: Dict[str, SimpleDocument] = {}
upload_dir = Path("uploads")
upload_dir.mkdir(exist_ok=True)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Memory Bank API - Simplified Version",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "online",
            "storage": "simple_memory",
            "documents": len(documents)
        }
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process a document"""
    try:
        # Generate unique ID
        doc_id = str(uuid.uuid4())
        
        # Save file
        file_path = upload_dir / f"{doc_id}_{file.filename}"
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Simple text extraction
        text_content = ""
        if file.filename.lower().endswith('.txt'):
            text_content = content.decode('utf-8', errors='ignore')
        elif file.filename.lower().endswith('.md'):
            text_content = content.decode('utf-8', errors='ignore')
        else:
            # For other file types, just store basic info
            text_content = f"File: {file.filename} (content extraction not implemented in simple version)"
        
        # Create document
        doc = SimpleDocument(
            id=doc_id,
            filename=file.filename,
            content=text_content[:1000],  # Limit content length
            file_type=file.content_type or "unknown"
        )
        
        documents[doc_id] = doc
        
        return {
            "document_id": doc_id,
            "filename": file.filename,
            "status": "uploaded",
            "content_preview": text_content[:200] + "..." if len(text_content) > 200 else text_content,
            "file_type": doc.file_type,
            "created_at": doc.created_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/query")
async def query_documents(query: str = Form(...)):
    """Simple document search and Q&A"""
    try:
        if not documents:
            return {
                "answer": "No documents uploaded yet. Please upload some documents first!",
                "sources": [],
                "query": query
            }
        
        # Simple keyword search
        results = []
        query_lower = query.lower()
        
        for doc_id, doc in documents.items():
            if any(word in doc.content.lower() for word in query_lower.split()):
                results.append({
                    "document_id": doc_id,
                    "filename": doc.filename,
                    "relevance_score": 0.8,  # Simplified scoring
                    "content_snippet": doc.content[:300]
                })
        
        # Simple answer generation
        if results:
            answer = f"Found {len(results)} relevant document(s) for your query '{query}'. "
            answer += f"Most relevant content: {results[0]['content_snippet'][:200]}..."
        else:
            answer = f"No relevant documents found for query '{query}'. Try uploading more documents or using different keywords."
        
        return {
            "answer": answer,
            "sources": results[:3],  # Limit to top 3 results
            "query": query,
            "total_documents": len(documents)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.get("/documents")
async def list_documents():
    """List all uploaded documents"""
    doc_list = []
    for doc_id, doc in documents.items():
        doc_list.append({
            "id": doc_id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "created_at": doc.created_at.isoformat(),
            "content_preview": doc.content[:100] + "..." if len(doc.content) > 100 else doc.content
        })
    
    return {
        "documents": doc_list,
        "total": len(doc_list)
    }

@app.get("/documents/{document_id}")
async def get_document(document_id: str):
    """Get specific document details"""
    if document_id not in documents:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = documents[document_id]
    return {
        "id": document_id,
        "filename": doc.filename,
        "content": doc.content,
        "file_type": doc.file_type,
        "created_at": doc.created_at.isoformat()
    }

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document"""
    if document_id not in documents:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = documents[document_id]
    
    # Remove from storage
    del documents[document_id]
    
    # Try to remove file
    try:
        file_path = upload_dir / f"{document_id}_{doc.filename}"
        if file_path.exists():
            file_path.unlink()
    except Exception:
        pass  # File removal not critical
    
    return {
        "message": f"Document {doc.filename} deleted successfully",
        "document_id": document_id
    }

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    return {
        "total_documents": len(documents),
        "storage_type": "in_memory",
        "uptime": "running",
        "features": {
            "upload": "✅ Available",
            "search": "✅ Basic keyword search",
            "ai_models": "⚠️ Simplified (no heavy AI)",
            "knowledge_graph": "❌ Not available in simple mode",
            "multimodal": "❌ Not available in simple mode"
        }
    }

if __name__ == "__main__":
    print("🚀 Starting AI Memory Bank - Simplified Backend")
    print("📍 API will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔍 To test: Upload a text file and then query it!")
    
    uvicorn.run("main_simple:app", host="0.0.0.0", port=8000, reload=True)