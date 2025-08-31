from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import uuid
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Simple in-memory storage for demo
documents = {}

def handler(request):
    """Vercel serverless function handler"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    
    path = request.path
    method = request.method
    
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json'
    }
    
    try:
        if path == '/' or path == '/api':
            return jsonify({
                "message": "AI Memory Bank API - Vercel Serverless",
                "status": "running",
                "version": "1.0.0",
                "endpoints": {
                    "upload": "POST /api/upload",
                    "query": "POST /api/query", 
                    "documents": "GET /api/documents",
                    "health": "GET /api/health"
                }
            }), 200, headers
            
        elif path == '/api/health':
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "documents_count": len(documents)
            }), 200, headers
            
        elif path == '/api/documents':
            doc_list = []
            for doc_id, doc in documents.items():
                doc_list.append({
                    "id": doc_id,
                    "filename": doc["filename"],
                    "created_at": doc["created_at"],
                    "content_preview": doc["content"][:100] + "..." if len(doc["content"]) > 100 else doc["content"]
                })
            return jsonify({"documents": doc_list, "total": len(doc_list)}), 200, headers
            
        elif path == '/api/upload' and method == 'POST':
            # Handle file upload
            doc_id = str(uuid.uuid4())
            filename = f"document_{len(documents)}.txt"
            
            # Get content from request
            if request.content_type and 'application/json' in request.content_type:
                data = request.get_json()
                content = data.get('content', 'Sample AI Memory Bank content')
            else:
                content = request.get_data(as_text=True) or "AI Memory Bank: Your Personal Knowledge Assistant"
            
            documents[doc_id] = {
                "id": doc_id,
                "filename": filename,
                "content": content[:1000],  # Limit content
                "created_at": datetime.now().isoformat()
            }
            
            return jsonify({
                "document_id": doc_id,
                "filename": filename,
                "status": "uploaded",
                "content_preview": content[:200] + "..." if len(content) > 200 else content
            }), 200, headers
            
        elif path == '/api/query' and method == 'POST':
            data = request.get_json()
            query = data.get('query', '') if data else ''
            
            # Simple search
            results = []
            for doc_id, doc in documents.items():
                if query.lower() in doc['content'].lower():
                    results.append({
                        "document_id": doc_id,
                        "filename": doc['filename'],
                        "relevance_score": 0.8,
                        "content_snippet": doc['content'][:200]
                    })
            
            answer = f"Found {len(results)} documents matching '{query}'" if results else f"No matches for '{query}'"
            
            return jsonify({
                "answer": answer,
                "sources": results[:3],
                "query": query,
                "total_documents": len(documents)
            }), 200, headers
            
        else:
            return jsonify({"error": "Not found"}), 404, headers
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500, headers

# Default documents for demo
documents["demo"] = {
    "id": "demo",
    "filename": "ai_memory_bank_info.txt",
    "content": "AI Memory Bank: Your Personal Knowledge Assistant. The AI Memory Bank is an intelligent document management and retrieval system that helps you organize, search, and gain insights from your personal knowledge collection. Features include multimodal processing, semantic search, knowledge graphs, and real-time collaboration.",
    "created_at": datetime.now().isoformat()
}