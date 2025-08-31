from flask import Flask, request, jsonify
import json
import uuid
from datetime import datetime

app = Flask(__name__)

# Simple in-memory storage for demo
documents = {
    "demo": {
        "id": "demo",
        "filename": "ai_memory_bank_info.txt",
        "content": "AI Memory Bank: Your Personal Knowledge Assistant. The AI Memory Bank is an intelligent document management and retrieval system that helps you organize, search, and gain insights from your personal knowledge collection. Features include multimodal processing, semantic search, knowledge graphs, and real-time collaboration.",
        "created_at": datetime.now().isoformat()
    }
}

def handler(event, context):
    """Vercel serverless function for file upload"""
    
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
        content = body.get('content', 'Sample document content')
        filename = body.get('filename', f'document_{len(documents)}.txt')
        
        # Create document
        doc_id = str(uuid.uuid4())
        documents[doc_id] = {
            "id": doc_id,
            "filename": filename,
            "content": content[:1000],  # Limit content for demo
            "created_at": datetime.now().isoformat()
        }
        
        response = {
            "document_id": doc_id,
            "filename": filename,
            "status": "uploaded",
            "content_preview": content[:200] + "..." if len(content) > 200 else content
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