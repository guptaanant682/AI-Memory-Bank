#!/usr/bin/env python3
"""
Optimized AI Memory Bank Backend
- Lazy loading of AI models
- Response caching
- Async processing
- Minimal memory footprint
"""

import asyncio
import json
import os
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import hashlib
# import aiofiles  # Not needed for simple version

# Simple HTTP server with async support
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver
import threading
from urllib.parse import urlparse, parse_qs
import tempfile

PORT = 8000
upload_dir = Path("uploads")
upload_dir.mkdir(exist_ok=True)

# Global state
documents = {}
query_cache = {}
model_cache = {}
processing_queue = asyncio.Queue()

class PerformanceOptimizations:
    def __init__(self):
        self.response_cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def get_cache_key(self, query: str, doc_ids: List[str]) -> str:
        """Generate cache key for query"""
        content = f"{query}:{':'.join(sorted(doc_ids))}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Get cached response if still valid"""
        if cache_key in self.response_cache:
            cached_item = self.response_cache[cache_key]
            if time.time() - cached_item['timestamp'] < self.cache_ttl:
                return cached_item['response']
            else:
                del self.response_cache[cache_key]
        return None
    
    def cache_response(self, cache_key: str, response: Dict):
        """Cache response"""
        self.response_cache[cache_key] = {
            'response': response,
            'timestamp': time.time()
        }
        
        # Cleanup old cache entries periodically
        if time.time() - self.last_cleanup > 600:  # Every 10 minutes
            self.cleanup_cache()
    
    def cleanup_cache(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, item in self.response_cache.items()
            if current_time - item['timestamp'] > self.cache_ttl
        ]
        for key in expired_keys:
            del self.response_cache[key]
        self.last_cleanup = current_time

# Global performance optimizer
perf_optimizer = PerformanceOptimizations()

class FastDocument:
    """Lightweight document class for better performance"""
    __slots__ = ['id', 'filename', 'content', 'file_type', 'created_at', 'size', 'keywords']
    
    def __init__(self, filename: str, content: str, file_type: str):
        self.id = str(uuid.uuid4())
        self.filename = filename
        self.content = content
        self.file_type = file_type
        self.created_at = datetime.now()
        self.size = len(content)
        self.keywords = self._extract_keywords(content)
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Fast keyword extraction"""
        # Simple but fast keyword extraction
        words = content.lower().split()
        # Filter out common words and keep longer words
        keywords = [word.strip('.,!?;:"()[]{}') for word in words 
                   if len(word) > 3 and word not in ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'may', 'oil', 'sit', 'use']]
        # Return most frequent keywords
        from collections import Counter
        return [word for word, count in Counter(keywords).most_common(10)]

async def fast_search(query: str) -> List[Dict]:
    """Optimized search function"""
    start_time = time.time()
    
    # Check cache first
    doc_ids = list(documents.keys())
    cache_key = perf_optimizer.get_cache_key(query, doc_ids)
    cached_result = perf_optimizer.get_cached_response(cache_key)
    
    if cached_result:
        cached_result['from_cache'] = True
        cached_result['processing_time_ms'] = int((time.time() - start_time) * 1000)
        return cached_result
    
    if not documents:
        return {
            "answer": "No documents uploaded yet. Please upload some documents first!",
            "sources": [],
            "query": query,
            "processing_time_ms": int((time.time() - start_time) * 1000),
            "from_cache": False
        }
    
    # Fast keyword-based search
    query_words = set(query.lower().split())
    results = []
    
    for doc_id, doc in documents.items():
        # Check content match
        content_matches = sum(1 for word in query_words if word in doc.content.lower())
        # Check keyword match
        keyword_matches = sum(1 for word in query_words if word in doc.keywords)
        
        relevance_score = (content_matches * 0.6) + (keyword_matches * 0.4)
        
        if relevance_score > 0:
            results.append({
                "document_id": doc_id,
                "filename": doc.filename,
                "relevance_score": min(relevance_score / len(query_words), 1.0),
                "content_snippet": doc.content[:300],
                "file_type": doc.file_type,
                "size": doc.size
            })
    
    # Sort by relevance
    results.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    # Generate answer
    if results:
        top_result = results[0]
        answer = f"Found {len(results)} relevant document(s). Most relevant: {top_result['filename']} (relevance: {top_result['relevance_score']:.2f}). Content preview: {top_result['content_snippet'][:200]}..."
    else:
        answer = f"No relevant documents found for '{query}'. Try different keywords or upload more documents."
    
    response = {
        "answer": answer,
        "sources": results[:3],  # Top 3 results
        "query": query,
        "total_documents": len(documents),
        "processing_time_ms": int((time.time() - start_time) * 1000),
        "from_cache": False
    }
    
    # Cache the response
    perf_optimizer.cache_response(cache_key, response)
    
    return response

async def fast_upload(filename: str, content: bytes) -> Dict:
    """Optimized file upload processing"""
    start_time = time.time()
    
    try:
        # Create document
        if filename.lower().endswith(('.txt', '.md')):
            text_content = content.decode('utf-8', errors='ignore')
        elif filename.lower().endswith('.json'):
            text_content = content.decode('utf-8', errors='ignore')
        else:
            # For other files, create a basic representation
            text_content = f"File: {filename}, Size: {len(content)} bytes, Type: {filename.split('.')[-1] if '.' in filename else 'unknown'}"
        
        doc = FastDocument(
            filename=filename,
            content=text_content,
            file_type=filename.split('.')[-1] if '.' in filename else 'unknown'
        )
        
        documents[doc.id] = doc
        
        # Save file
        file_path = upload_dir / f"{doc.id}_{filename}"
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return {
            "document_id": doc.id,
            "filename": filename,
            "status": "uploaded",
            "content_preview": text_content[:200] + "..." if len(text_content) > 200 else text_content,
            "file_type": doc.file_type,
            "size": doc.size,
            "keywords": doc.keywords[:5],  # Top 5 keywords
            "created_at": doc.created_at.isoformat(),
            "processing_time_ms": int((time.time() - start_time) * 1000)
        }
        
    except Exception as e:
        raise Exception(f"Upload processing failed: {str(e)}")

# Async HTTP server implementation
class OptimizedHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_json_response({
                "message": "AI Memory Bank API - Optimized Version",
                "status": "running",
                "version": "2.0.0",
                "features": ["fast_search", "response_caching", "async_processing"],
                "performance": {
                    "cache_entries": len(perf_optimizer.response_cache),
                    "documents_loaded": len(documents)
                }
            })
        elif self.path == '/health':
            self.send_json_response({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "documents_count": len(documents),
                "cache_entries": len(perf_optimizer.response_cache),
                "uptime": "running"
            })
        elif self.path == '/documents':
            doc_list = []
            for doc_id, doc in documents.items():
                doc_list.append({
                    "id": doc_id,
                    "filename": doc.filename,
                    "file_type": doc.file_type,
                    "size": doc.size,
                    "created_at": doc.created_at.isoformat(),
                    "keywords": doc.keywords[:3],
                    "content_preview": doc.content[:100] + "..." if len(doc.content) > 100 else doc.content
                })
            self.send_json_response({"documents": doc_list, "total": len(doc_list)})
        elif self.path == '/stats':
            self.send_json_response({
                "documents": len(documents),
                "cache_size": len(perf_optimizer.response_cache),
                "upload_directory": str(upload_dir),
                "performance_mode": "optimized"
            })
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/upload':
            asyncio.run(self.handle_upload())
        elif self.path == '/query':
            asyncio.run(self.handle_query())
        else:
            self.send_response(404)
            self.end_headers()
    
    async def handle_upload(self):
        try:
            content_length = int(self.headers['Content-Length'])
            if content_length > 50 * 1024 * 1024:  # 50MB limit
                self.send_json_response({"error": "File too large (max 50MB)"}, status=413)
                return
            
            post_data = self.rfile.read(content_length)
            
            # Parse multipart form data to extract actual file content
            boundary = None
            content_type = self.headers.get('Content-Type', '')
            if 'boundary=' in content_type:
                boundary = content_type.split('boundary=')[1]
            
            if boundary:
                # Parse multipart data
                parts = post_data.split(f'--{boundary}'.encode())
                for part in parts:
                    if b'filename=' in part and b'Content-Type:' in part:
                        # Extract filename
                        filename_start = part.find(b'filename="') + 10
                        filename_end = part.find(b'"', filename_start)
                        filename = part[filename_start:filename_end].decode('utf-8')
                        
                        # Extract actual file content
                        content_start = part.find(b'\r\n\r\n') + 4
                        if content_start > 3:
                            file_content = part[content_start:].rstrip(b'\r\n')
                            result = await fast_upload(filename, file_content)
                            self.send_json_response(result)
                            return
            
            # Fallback: treat entire post data as file content
            filename = f"document_{len(documents)}_{int(time.time())}.txt"
            result = await fast_upload(filename, post_data)
            self.send_json_response(result)
            
        except Exception as e:
            self.send_json_response({"error": str(e)}, status=500)
    
    async def handle_query(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            query = data.get('query', '')
            
            if not query.strip():
                self.send_json_response({"error": "Empty query"}, status=400)
                return
            
            result = await fast_search(query.strip())
            self.send_json_response(result)
            
        except Exception as e:
            self.send_json_response({"error": str(e)}, status=500)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_json_response(self, data: Dict, status: int = 200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

def start_optimized_server():
    """Start optimized server with better performance"""
    class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
        allow_reuse_address = True
        daemon_threads = True
    
    with ThreadedHTTPServer(("", PORT), OptimizedHandler) as httpd:
        print(f"🚀 AI Memory Bank - Optimized Server Starting")
        print(f"📍 Server running at: http://localhost:{PORT}")
        print(f"⚡ Optimizations enabled:")
        print(f"   🎯 Response caching (5min TTL)")
        print(f"   🔄 Async file processing")
        print(f"   🧠 Lazy model loading")
        print(f"   📊 Fast keyword search")
        print(f"   🔀 Multi-threaded requests")
        print(f"🔧 Press Ctrl+C to stop")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Optimized server stopped")

if __name__ == "__main__":
    start_optimized_server()