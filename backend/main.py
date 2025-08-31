from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from services.document_processor import DocumentProcessor
from services.audio_processor import AudioProcessor
from services.image_processor import ImageProcessor
from services.enhanced_document_processor import EnhancedDocumentProcessor
from services.knowledge_graph import KnowledgeGraph
from services.rag_engine import RAGEngine
from services.vector_store import VectorStore
from services.realtime_integrations import RealtimeIntegrationService
from services.ai_learning_agent import AILearningAgent
from services.collaboration_service import CollaborationService
from services.analytics_service import AdvancedAnalyticsService
from models.schemas import DocumentResponse, QueryRequest, QueryResponse

app = FastAPI(
    title="AI Memory Bank API",
    description="Personal knowledge assistant with RAG capabilities",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
document_processor = DocumentProcessor()
enhanced_processor = EnhancedDocumentProcessor()
audio_processor = AudioProcessor()
image_processor = ImageProcessor()
knowledge_graph = KnowledgeGraph()
vector_store = VectorStore()
rag_engine = RAGEngine(vector_store)
realtime_service = RealtimeIntegrationService(document_processor, vector_store, knowledge_graph)
ai_agent = AILearningAgent(knowledge_graph, vector_store, rag_engine)
collaboration_service = CollaborationService()
analytics_service = AdvancedAnalyticsService(vector_store, knowledge_graph)

# Create uploads directory
os.makedirs("uploads", exist_ok=True)

@app.get("/")
async def root():
    return {"message": "AI Memory Bank API is running!"}

@app.post("/upload", response_model=DocumentResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload and process any supported file type (text, audio, image)"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        # Define supported file types
        text_extensions = {'.txt', '.pdf', '.doc', '.docx', '.md'}
        audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac'}
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
        
        all_extensions = text_extensions | audio_extensions | image_extensions
        
        if file_extension not in all_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_extension} not supported. Supported: {', '.join(sorted(all_extensions))}"
            )
        
        # Save uploaded file
        file_path = f"uploads/{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process file based on type with knowledge extraction
        if file_extension in text_extensions:
            # Use enhanced processor for text documents to extract knowledge
            result = await enhanced_processor.process_file_with_knowledge_extraction(file_path)
            document = result["document"]
            chunks = result.get("chunks", [])
        elif file_extension in audio_extensions:
            document = await audio_processor.process_audio_file(file_path)
            chunks = getattr(audio_processor, 'chunks', [])
            # Extract knowledge from transcribed text
            if document.content:
                knowledge_data = await knowledge_graph.extract_entities_and_relationships(document)
                await knowledge_graph.store_knowledge(knowledge_data)
        elif file_extension in image_extensions:
            document = await image_processor.process_image_file(file_path)
            chunks = getattr(image_processor, 'chunks', [])
            # Extract knowledge from image descriptions
            if document.content:
                knowledge_data = await knowledge_graph.extract_entities_and_relationships(document)
                await knowledge_graph.store_knowledge(knowledge_data)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # Store in vector database
        await vector_store.add_document(document, chunks)
        
        return DocumentResponse(
            id=document.id,
            title=document.title,
            status="completed",
            message=f"{file_extension.upper()} file processed successfully",
            summary=document.summary,
            tags=document.tags
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query documents using RAG"""
    try:
        response = await rag_engine.query(
            query=request.query,
            filters=request.filters,
            top_k=request.top_k or 5
        )
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents", response_model=List[DocumentResponse])
async def get_documents(skip: int = 0, limit: int = 50):
    """Get list of uploaded documents"""
    try:
        documents = await vector_store.get_documents(skip=skip, limit=limit)
        return [
            DocumentResponse(
                id=doc.id,
                title=doc.title,
                status="completed",
                message="",
                summary=doc.summary,
                tags=doc.tags
            )
            for doc in documents
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document"""
    try:
        await vector_store.delete_document(document_id)
        return {"message": "Document deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search/images")
async def search_images(query: str):
    """Search images by natural language description"""
    try:
        # Get all image documents from vector store
        all_docs = await vector_store.get_documents(limit=1000)
        image_paths = [doc.file_path for doc in all_docs if doc.file_type in ['jpeg', 'png', 'gif', 'bmp', 'webp']]
        
        # Search using image processor
        results = await image_processor.search_images_by_description(query, image_paths)
        
        return {
            "query": query,
            "results": [
                {
                    "file_path": path,
                    "relevance_score": score,
                    "filename": os.path.basename(path)
                }
                for path, score in results[:10]  # Top 10 results
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/stats")
async def get_document_stats():
    """Get statistics about uploaded documents"""
    try:
        all_docs = await vector_store.get_documents(limit=1000)
        
        stats = {
            "total_documents": len(all_docs),
            "by_type": {},
            "total_size_bytes": 0,
            "recent_uploads": []
        }
        
        for doc in all_docs:
            # Count by type
            file_type = doc.file_type
            stats["by_type"][file_type] = stats["by_type"].get(file_type, 0) + 1
            
            # Total size
            stats["total_size_bytes"] += doc.size_bytes or 0
            
            # Recent uploads (last 10)
            if len(stats["recent_uploads"]) < 10:
                stats["recent_uploads"].append({
                    "id": doc.id,
                    "title": doc.title,
                    "type": file_type,
                    "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None
                })
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge-graph")
async def get_knowledge_graph(limit: int = 100):
    """Get knowledge graph data for visualization"""
    try:
        graph_data = await knowledge_graph.get_knowledge_graph_data(limit=limit)
        return graph_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge-graph/concept/{concept_name}/related")
async def get_related_concepts(concept_name: str, max_results: int = 10):
    """Get concepts related to a specific concept"""
    try:
        related = await knowledge_graph.find_related_concepts(concept_name, max_results)
        return {
            "concept": concept_name,
            "related_concepts": related
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge-graph/path/{start_concept}/{end_concept}")
async def find_knowledge_path(start_concept: str, end_concept: str, max_depth: int = 3):
    """Find knowledge paths between two concepts"""
    try:
        paths = await knowledge_graph.search_knowledge_paths(start_concept, end_concept, max_depth)
        return {
            "start_concept": start_concept,
            "end_concept": end_concept,
            "paths": paths,
            "path_count": len(paths)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}/context")
async def analyze_document_context(document_id: str):
    """Analyze document context using knowledge graph"""
    try:
        # Get document from vector store
        documents = await vector_store.get_documents(limit=1000)
        document = next((doc for doc in documents if doc.id == document_id), None)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        context = await enhanced_processor.analyze_document_context(document)
        return context
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}/suggestions")
async def get_document_suggestions(document_id: str, limit: int = 10):
    """Get document suggestions based on knowledge graph"""
    try:
        # Get document from vector store
        documents = await vector_store.get_documents(limit=1000)
        document = next((doc for doc in documents if doc.id == document_id), None)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        suggestions = await enhanced_processor.suggest_related_documents(document, limit)
        return {
            "document_id": document_id,
            "suggestions": suggestions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge/summary")
async def get_knowledge_summary():
    """Get overall knowledge summary across all documents"""
    try:
        # Get all document IDs
        documents = await vector_store.get_documents(limit=1000)
        document_ids = [doc.id for doc in documents]
        
        summary = await enhanced_processor.generate_knowledge_summary(document_ids)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Real-time Integration Endpoints

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time updates"""
    await realtime_service.connect_websocket(user_id, websocket)

@app.post("/integrations/google-drive")
async def setup_google_drive(user_id: str, credentials: Dict[str, Any]):
    """Setup Google Drive integration"""
    try:
        result = await realtime_service.setup_google_drive_integration(user_id, credentials)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/integrations/notion")
async def setup_notion(user_id: str, api_token: str, database_id: str):
    """Setup Notion integration"""
    try:
        result = await realtime_service.setup_notion_integration(user_id, api_token, database_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/integrations/slack")
async def setup_slack(user_id: str, bot_token: str, channel_id: str):
    """Setup Slack integration"""
    try:
        result = await realtime_service.setup_slack_integration(user_id, bot_token, channel_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhooks")
async def create_webhook(user_id: str, webhook_config: Dict[str, Any]):
    """Create webhook endpoint"""
    try:
        webhook = await realtime_service.setup_webhook_endpoint(user_id, webhook_config)
        return webhook
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhooks/{webhook_id}")
async def process_webhook(webhook_id: str, payload: Dict[str, Any], signature: str = ""):
    """Process webhook payload"""
    try:
        result = await realtime_service.process_webhook_payload(webhook_id, payload, signature)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/integrations/{user_id}/status")
async def get_integration_status(user_id: str):
    """Get integration status for user"""
    try:
        status = await realtime_service.get_integration_status(user_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# AI Learning Agent Endpoints

@app.get("/ai-agent/{user_id}/knowledge-gaps")
async def analyze_knowledge_gaps(user_id: str):
    """Analyze knowledge gaps and learning opportunities"""
    try:
        analysis = await ai_agent.analyze_knowledge_gaps(user_id)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai-agent/learning-path")
async def generate_learning_path(topic: str, current_level: str = "beginner", target_level: str = "advanced"):
    """Generate learning path for a topic"""
    try:
        path = await ai_agent.generate_learning_path(topic, current_level, target_level)
        return path
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ai-agent/{user_id}/daily-insights")
async def get_daily_insights(user_id: str):
    """Get daily learning insights and recommendations"""
    try:
        insights = await ai_agent.get_daily_insights(user_id)
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Collaboration Endpoints

@app.post("/workspaces")
async def create_workspace(owner_id: str, name: str, description: str = "", is_public: bool = False):
    """Create collaborative workspace"""
    try:
        workspace = await collaboration_service.create_workspace(owner_id, name, description, is_public)
        return workspace
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workspaces/{workspace_id}")
async def get_workspace(workspace_id: str, user_id: str):
    """Get workspace details"""
    try:
        workspace = await collaboration_service.get_workspace(workspace_id, user_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        return workspace
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}/workspaces")
async def get_user_workspaces(user_id: str):
    """Get user's workspaces"""
    try:
        workspaces = await collaboration_service.get_user_workspaces(user_id)
        return {"workspaces": workspaces}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workspaces/{workspace_id}/invite")
async def invite_user(workspace_id: str, inviter_id: str, invitee_email: str, permission: str = "viewer"):
    """Invite user to workspace"""
    try:
        invitation = await collaboration_service.invite_user(workspace_id, inviter_id, invitee_email, permission)
        return invitation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/invitations/{invitation_id}/accept")
async def accept_invitation(invitation_id: str, user_id: str):
    """Accept workspace invitation"""
    try:
        result = await collaboration_service.accept_invitation(invitation_id, user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workspaces/{workspace_id}/analytics")
async def get_collaboration_analytics(workspace_id: str, user_id: str):
    """Get collaboration analytics"""
    try:
        analytics = await collaboration_service.get_collaboration_analytics(workspace_id, user_id)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Advanced Analytics Endpoints

@app.get("/analytics/{user_id}/evolution")
async def analyze_knowledge_evolution(user_id: str, days_back: int = 90):
    """Analyze knowledge evolution over time"""
    try:
        analysis = await analytics_service.analyze_knowledge_evolution(user_id, days_back)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/{user_id}/impact")
async def generate_impact_analysis(user_id: str):
    """Generate impact analysis of knowledge"""
    try:
        analysis = await analytics_service.generate_impact_analysis(user_id)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/{user_id}/dashboard")
async def get_analytics_dashboard(user_id: str):
    """Get analytics dashboard data"""
    try:
        dashboard = await analytics_service.get_analytics_dashboard_data(user_id)
        return dashboard
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "vector_store": await vector_store.health_check(),
            "document_processor": document_processor.health_check(),
            "enhanced_processor": enhanced_processor.health_check(),
            "audio_processor": audio_processor.health_check(),
            "image_processor": image_processor.health_check(),
            "knowledge_graph": knowledge_graph.health_check(),
            "rag_engine": rag_engine.health_check(),
            "realtime_integrations": realtime_service.health_check(),
            "ai_learning_agent": ai_agent.health_check(),
            "collaboration_service": collaboration_service.health_check(),
            "analytics_service": analytics_service.health_check()
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)