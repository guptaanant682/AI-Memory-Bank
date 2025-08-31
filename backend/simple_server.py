#!/usr/bin/env python3
"""
Ultra-simple HTTP server for AI Memory Bank demo
Uses only Python built-in modules
"""

import http.server
import socketserver
import json
import urllib.parse
import os
import uuid
from datetime import datetime
import threading

PORT = 8000
documents = {}
upload_dir = "uploads"

# Create uploads directory
os.makedirs(upload_dir, exist_ok=True)

class AIMemoryBankHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                "message": "AI Memory Bank API - Ultra Simple Version",
                "status": "running",
                "version": "0.1.0",
                "endpoints": {
                    "upload": "POST /upload",
                    "query": "POST /query", 
                    "documents": "GET /documents",
                    "health": "GET /health"
                }
            }
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "documents_count": len(documents)
            }
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/documents':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            doc_list = []
            for doc_id, doc in documents.items():
                doc_list.append({
                    "id": doc_id,
                    "filename": doc["filename"],
                    "created_at": doc["created_at"],
                    "content_preview": doc["content"][:100] + "..." if len(doc["content"]) > 100 else doc["content"]
                })
            response = {"documents": doc_list, "total": len(doc_list)}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/upload':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                # Simple text file handling
                doc_id = str(uuid.uuid4())
                filename = f"document_{len(documents)}.txt"
                
                # Save content
                content = post_data.decode('utf-8', errors='ignore')
                documents[doc_id] = {
                    "id": doc_id,
                    "filename": filename,
                    "content": content[:1000],  # Limit content
                    "created_at": datetime.now().isoformat()
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {
                    "document_id": doc_id,
                    "filename": filename,
                    "status": "uploaded",
                    "content_preview": content[:200] + "..." if len(content) > 200 else content
                }
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
                
        elif self.path == '/query':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode())
                query = data.get('query', '')
                
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
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {
                    "answer": answer,
                    "sources": results[:3],
                    "query": query,
                    "total_documents": len(documents)
                }
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def start_server():
    """Start the simple HTTP server"""
    with socketserver.TCPServer(("", PORT), AIMemoryBankHandler) as httpd:
        print(f"🚀 AI Memory Bank - Simple Server Starting")
        print(f"📍 Server running at: http://localhost:{PORT}")
        print(f"📚 API endpoints:")
        print(f"   GET  /         - API info")
        print(f"   GET  /health   - Health check")
        print(f"   GET  /documents - List documents")
        print(f"   POST /upload   - Upload document")
        print(f"   POST /query    - Query documents")
        print(f"🔧 Press Ctrl+C to stop")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")

if __name__ == "__main__":
    start_server()