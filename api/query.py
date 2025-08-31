from flask import Flask, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

# Demo documents
documents = {
    "demo": {
        "id": "demo",
        "filename": "ai_memory_bank_info.txt",
        "content": "AI Memory Bank: Your Personal Knowledge Assistant. The AI Memory Bank is an intelligent document management and retrieval system that helps you organize, search, and gain insights from your personal knowledge collection. Features include multimodal processing, semantic search, knowledge graphs, and real-time collaboration.",
        "created_at": datetime.now().isoformat()
    }
}

def handler(event, context):
    """Vercel serverless function for querying documents"""
    
    # Handle CORS
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json'
    }
    
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        query = body.get('query', '').lower()
        
        # Simple search
        results = []
        for doc_id, doc in documents.items():
            if query in doc['content'].lower():
                results.append({
                    "document_id": doc_id,
                    "filename": doc['filename'],
                    "relevance_score": 0.8,
                    "content_snippet": doc['content'][:200]
                })
        
        answer = f"Found {len(results)} documents matching '{query}'" if results else f"No matches for '{query}'"
        
        response = {
            "answer": answer,
            "sources": results[:3],
            "query": body.get('query', ''),
            "total_documents": len(documents)
        }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(response)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({"error": str(e)})
        }