import logging
import asyncio
import json
import uuid
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp
import aiofiles
from fastapi import WebSocket
from collections import defaultdict

# External API clients
import httpx

from models.schemas import Document
from services.document_processor import DocumentProcessor
from services.vector_store import VectorStore
from services.knowledge_graph import KnowledgeGraph

logger = logging.getLogger(__name__)

class RealtimeIntegrationService:
    """Service for managing real-time integrations with external platforms"""
    
    def __init__(self, document_processor: DocumentProcessor, vector_store: VectorStore, knowledge_graph: KnowledgeGraph):
        self.document_processor = document_processor
        self.vector_store = vector_store
        self.knowledge_graph = knowledge_graph
        self.integrations_storage = "integrations_data"
        self.active_connections = defaultdict(list)  # WebSocket connections
        self.sync_queues = defaultdict(list)  # Pending sync items
        Path(self.integrations_storage).mkdir(exist_ok=True)
        self._ensure_integration_structure()
        
    def _ensure_integration_structure(self):
        """Ensure integration storage structure exists"""
        subdirs = ["google_drive", "notion", "slack", "webhooks", "sync_logs"]
        for subdir in subdirs:
            Path(f"{self.integrations_storage}/{subdir}").mkdir(exist_ok=True)

    async def setup_google_drive_integration(self, user_id: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Setup Google Drive integration for automatic document sync"""
        try:
            integration = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "platform": "google_drive",
                "status": "active",
                "credentials": credentials,  # Should be encrypted in production
                "sync_settings": {
                    "auto_sync": True,
                    "sync_frequency": "real_time",
                    "folders_to_watch": ["/AI Memory Bank"],
                    "file_types": ["pdf", "docx", "txt", "md"],
                    "last_sync": None
                },
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Save integration config
            integration_file = f"{self.integrations_storage}/google_drive/{user_id}.json"
            async with aiofiles.open(integration_file, 'w') as f:
                await f.write(json.dumps(integration, indent=2))
            
            # Test connection
            connection_test = await self._test_google_drive_connection(credentials)
            if not connection_test["success"]:
                raise ValueError(f"Failed to connect to Google Drive: {connection_test['error']}")
            
            # Start monitoring for changes
            asyncio.create_task(self._monitor_google_drive_changes(user_id, integration))
            
            logger.info(f"Google Drive integration setup for user {user_id}")
            return {
                "integration_id": integration["id"],
                "status": "connected",
                "message": "Google Drive integration setup successfully"
            }
            
        except Exception as e:
            logger.error(f"Error setting up Google Drive integration: {e}")
            raise

    async def _test_google_drive_connection(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Test Google Drive API connection"""
        try:
            # Simulate Google Drive API call
            # In production, use actual Google Drive API
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _monitor_google_drive_changes(self, user_id: str, integration: Dict[str, Any]):
        """Monitor Google Drive for file changes"""
        try:
            while integration.get("status") == "active":
                try:
                    # Check for new/modified files
                    changes = await self._check_google_drive_changes(user_id, integration)
                    
                    for change in changes:
                        await self._process_google_drive_change(user_id, change)
                    
                    # Update last sync time
                    integration["sync_settings"]["last_sync"] = datetime.utcnow().isoformat()
                    await self._save_integration(user_id, "google_drive", integration)
                    
                    # Wait before next check (in production, use webhooks for real-time)
                    await asyncio.sleep(60)  # Check every minute
                    
                except Exception as e:
                    logger.error(f"Error monitoring Google Drive changes: {e}")
                    await asyncio.sleep(300)  # Wait 5 minutes on error
                    
        except Exception as e:
            logger.error(f"Google Drive monitoring stopped for user {user_id}: {e}")

    async def _check_google_drive_changes(self, user_id: str, integration: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for changes in Google Drive"""
        try:
            # Simulate checking Google Drive API for changes
            # In production, use Google Drive API changes endpoint
            
            # Mock changes for demonstration
            if integration["sync_settings"]["last_sync"] is None:
                return [
                    {
                        "file_id": "sample_file_1",
                        "name": "Research Paper.pdf",
                        "type": "file",
                        "modified_time": datetime.utcnow().isoformat(),
                        "action": "created",
                        "download_url": "https://drive.google.com/file/d/sample_file_1"
                    }
                ]
            
            return []  # No changes in this simulation
            
        except Exception as e:
            logger.error(f"Error checking Google Drive changes: {e}")
            return []

    async def _process_google_drive_change(self, user_id: str, change: Dict[str, Any]):
        """Process a Google Drive file change"""
        try:
            if change["action"] in ["created", "modified"]:
                # Download and process the file
                file_content = await self._download_google_drive_file(change["download_url"])
                
                if file_content:
                    # Create document object
                    document = Document(
                        id=str(uuid.uuid4()),
                        title=change["name"],
                        content=file_content.get("text", ""),
                        file_type=change["name"].split(".")[-1].lower(),
                        tags=["google_drive", "auto_sync"],
                        summary=file_content.get("summary", ""),
                        uploaded_at=datetime.utcnow(),
                        source_platform="google_drive",
                        source_id=change["file_id"]
                    )
                    
                    # Process and store document
                    processed = await self.document_processor.process_document(document)
                    if processed:
                        # Notify connected clients
                        await self._broadcast_sync_update(user_id, {
                            "type": "document_synced",
                            "platform": "google_drive",
                            "document": {
                                "id": document.id,
                                "title": document.title,
                                "status": "processed"
                            }
                        })
                        
                        # Log sync activity
                        await self._log_sync_activity(user_id, "google_drive", "document_synced", {
                            "file_name": change["name"],
                            "file_id": change["file_id"]
                        })
            
            elif change["action"] == "deleted":
                # Handle file deletion
                await self._handle_file_deletion(user_id, change["file_id"])
                
        except Exception as e:
            logger.error(f"Error processing Google Drive change: {e}")

    async def _download_google_drive_file(self, download_url: str) -> Optional[Dict[str, Any]]:
        """Download file from Google Drive"""
        try:
            # Simulate file download and processing
            # In production, use Google Drive API
            return {
                "text": "Sample document content from Google Drive",
                "summary": "This is a sample document synced from Google Drive"
            }
            
        except Exception as e:
            logger.error(f"Error downloading Google Drive file: {e}")
            return None

    async def setup_notion_integration(self, user_id: str, api_token: str, database_id: str) -> Dict[str, Any]:
        """Setup Notion integration for knowledge base sync"""
        try:
            integration = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "platform": "notion",
                "status": "active",
                "credentials": {
                    "api_token": api_token,  # Should be encrypted
                    "database_id": database_id
                },
                "sync_settings": {
                    "auto_sync": True,
                    "sync_frequency": "real_time",
                    "sync_direction": "bidirectional",  # Import from and export to Notion
                    "last_sync": None
                },
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Test Notion connection
            connection_test = await self._test_notion_connection(api_token, database_id)
            if not connection_test["success"]:
                raise ValueError(f"Failed to connect to Notion: {connection_test['error']}")
            
            # Save integration
            integration_file = f"{self.integrations_storage}/notion/{user_id}.json"
            async with aiofiles.open(integration_file, 'w') as f:
                await f.write(json.dumps(integration, indent=2))
            
            # Start monitoring
            asyncio.create_task(self._monitor_notion_changes(user_id, integration))
            
            logger.info(f"Notion integration setup for user {user_id}")
            return {
                "integration_id": integration["id"],
                "status": "connected",
                "message": "Notion integration setup successfully"
            }
            
        except Exception as e:
            logger.error(f"Error setting up Notion integration: {e}")
            raise

    async def _test_notion_connection(self, api_token: str, database_id: str) -> Dict[str, Any]:
        """Test Notion API connection"""
        try:
            # Simulate Notion API test
            # In production, make actual Notion API call
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _monitor_notion_changes(self, user_id: str, integration: Dict[str, Any]):
        """Monitor Notion database for changes"""
        try:
            while integration.get("status") == "active":
                try:
                    # Check for new/modified pages
                    changes = await self._check_notion_changes(user_id, integration)
                    
                    for change in changes:
                        await self._process_notion_change(user_id, change)
                    
                    # Update sync time
                    integration["sync_settings"]["last_sync"] = datetime.utcnow().isoformat()
                    await self._save_integration(user_id, "notion", integration)
                    
                    await asyncio.sleep(60)  # Check every minute
                    
                except Exception as e:
                    logger.error(f"Error monitoring Notion changes: {e}")
                    await asyncio.sleep(300)
                    
        except Exception as e:
            logger.error(f"Notion monitoring stopped for user {user_id}: {e}")

    async def _check_notion_changes(self, user_id: str, integration: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for changes in Notion database"""
        try:
            # Mock Notion changes
            if integration["sync_settings"]["last_sync"] is None:
                return [
                    {
                        "page_id": "sample_page_1",
                        "title": "Knowledge Base Entry",
                        "content": "Sample content from Notion page",
                        "tags": ["notion", "knowledge"],
                        "last_edited": datetime.utcnow().isoformat(),
                        "action": "created"
                    }
                ]
            
            return []
            
        except Exception as e:
            logger.error(f"Error checking Notion changes: {e}")
            return []

    async def _process_notion_change(self, user_id: str, change: Dict[str, Any]):
        """Process a Notion page change"""
        try:
            if change["action"] in ["created", "modified"]:
                # Create document from Notion page
                document = Document(
                    id=str(uuid.uuid4()),
                    title=change["title"],
                    content=change["content"],
                    file_type="notion_page",
                    tags=change.get("tags", []) + ["notion", "auto_sync"],
                    summary=change["content"][:200] + "..." if len(change["content"]) > 200 else change["content"],
                    uploaded_at=datetime.utcnow(),
                    source_platform="notion",
                    source_id=change["page_id"]
                )
                
                # Process document
                processed = await self.document_processor.process_document(document)
                if processed:
                    await self._broadcast_sync_update(user_id, {
                        "type": "document_synced",
                        "platform": "notion",
                        "document": {
                            "id": document.id,
                            "title": document.title,
                            "status": "processed"
                        }
                    })
                    
        except Exception as e:
            logger.error(f"Error processing Notion change: {e}")

    async def setup_slack_integration(self, user_id: str, bot_token: str, channel_id: str) -> Dict[str, Any]:
        """Setup Slack integration for message archiving"""
        try:
            integration = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "platform": "slack",
                "status": "active",
                "credentials": {
                    "bot_token": bot_token,  # Should be encrypted
                    "channel_id": channel_id
                },
                "sync_settings": {
                    "auto_sync": True,
                    "archive_messages": True,
                    "archive_threads": True,
                    "minimum_message_length": 50,
                    "last_sync": None
                },
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Test Slack connection
            connection_test = await self._test_slack_connection(bot_token)
            if not connection_test["success"]:
                raise ValueError(f"Failed to connect to Slack: {connection_test['error']}")
            
            # Save integration
            integration_file = f"{self.integrations_storage}/slack/{user_id}.json"
            async with aiofiles.open(integration_file, 'w') as f:
                await f.write(json.dumps(integration, indent=2))
            
            # Start monitoring
            asyncio.create_task(self._monitor_slack_messages(user_id, integration))
            
            logger.info(f"Slack integration setup for user {user_id}")
            return {
                "integration_id": integration["id"],
                "status": "connected",
                "message": "Slack integration setup successfully"
            }
            
        except Exception as e:
            logger.error(f"Error setting up Slack integration: {e}")
            raise

    async def _test_slack_connection(self, bot_token: str) -> Dict[str, Any]:
        """Test Slack API connection"""
        try:
            # Simulate Slack API test
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _monitor_slack_messages(self, user_id: str, integration: Dict[str, Any]):
        """Monitor Slack messages for archiving"""
        try:
            while integration.get("status") == "active":
                try:
                    # Check for new messages
                    messages = await self._check_slack_messages(user_id, integration)
                    
                    for message in messages:
                        await self._process_slack_message(user_id, message)
                    
                    # Update sync time
                    integration["sync_settings"]["last_sync"] = datetime.utcnow().isoformat()
                    await self._save_integration(user_id, "slack", integration)
                    
                    await asyncio.sleep(60)
                    
                except Exception as e:
                    logger.error(f"Error monitoring Slack messages: {e}")
                    await asyncio.sleep(300)
                    
        except Exception as e:
            logger.error(f"Slack monitoring stopped for user {user_id}: {e}")

    async def _check_slack_messages(self, user_id: str, integration: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for new Slack messages"""
        try:
            # Mock Slack messages
            if integration["sync_settings"]["last_sync"] is None:
                return [
                    {
                        "message_id": "msg_1",
                        "text": "This is an important discussion about AI Memory Bank implementation that should be archived for future reference.",
                        "user": "john_doe",
                        "timestamp": datetime.utcnow().isoformat(),
                        "channel": integration["credentials"]["channel_id"],
                        "thread_ts": None
                    }
                ]
            
            return []
            
        except Exception as e:
            logger.error(f"Error checking Slack messages: {e}")
            return []

    async def _process_slack_message(self, user_id: str, message: Dict[str, Any]):
        """Process a Slack message for archiving"""
        try:
            # Check if message meets archiving criteria
            if len(message["text"]) < 50:  # Skip short messages
                return
            
            # Create document from message
            document = Document(
                id=str(uuid.uuid4()),
                title=f"Slack Discussion - {message['user']}",
                content=message["text"],
                file_type="slack_message",
                tags=["slack", "discussion", "auto_archive"],
                summary=message["text"][:200] + "..." if len(message["text"]) > 200 else message["text"],
                uploaded_at=datetime.utcnow(),
                source_platform="slack",
                source_id=message["message_id"],
                metadata={
                    "user": message["user"],
                    "channel": message["channel"],
                    "timestamp": message["timestamp"],
                    "thread_ts": message.get("thread_ts")
                }
            )
            
            # Process document
            processed = await self.document_processor.process_document(document)
            if processed:
                await self._broadcast_sync_update(user_id, {
                    "type": "message_archived",
                    "platform": "slack",
                    "document": {
                        "id": document.id,
                        "title": document.title,
                        "user": message["user"]
                    }
                })
                
        except Exception as e:
            logger.error(f"Error processing Slack message: {e}")

    async def setup_webhook_endpoint(self, user_id: str, webhook_config: Dict[str, Any]) -> Dict[str, Any]:
        """Setup webhook endpoint for external integrations"""
        try:
            webhook_id = str(uuid.uuid4())
            webhook = {
                "id": webhook_id,
                "user_id": user_id,
                "name": webhook_config.get("name", "Generic Webhook"),
                "url": f"/webhooks/{webhook_id}",
                "secret": str(uuid.uuid4()),  # Webhook verification secret
                "events": webhook_config.get("events", ["document.created", "document.updated"]),
                "status": "active",
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Save webhook config
            webhook_file = f"{self.integrations_storage}/webhooks/{webhook_id}.json"
            async with aiofiles.open(webhook_file, 'w') as f:
                await f.write(json.dumps(webhook, indent=2))
            
            logger.info(f"Webhook endpoint created for user {user_id}: {webhook['url']}")
            return webhook
            
        except Exception as e:
            logger.error(f"Error setting up webhook: {e}")
            raise

    async def process_webhook_payload(self, webhook_id: str, payload: Dict[str, Any], signature: str) -> Dict[str, Any]:
        """Process incoming webhook payload"""
        try:
            # Load webhook config
            webhook_file = f"{self.integrations_storage}/webhooks/{webhook_id}.json"
            if not Path(webhook_file).exists():
                raise ValueError("Webhook not found")
            
            async with aiofiles.open(webhook_file, 'r') as f:
                webhook_data = json.loads(await f.read())
            
            # Verify webhook signature (in production)
            # verify_signature(payload, signature, webhook_data["secret"])
            
            # Process based on event type
            event_type = payload.get("event", "unknown")
            
            if event_type == "document.created":
                await self._process_webhook_document_created(webhook_data["user_id"], payload["data"])
            elif event_type == "document.updated":
                await self._process_webhook_document_updated(webhook_data["user_id"], payload["data"])
            
            # Log webhook activity
            await self._log_sync_activity(webhook_data["user_id"], "webhook", event_type, payload)
            
            return {"status": "processed", "event": event_type}
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            raise

    async def _process_webhook_document_created(self, user_id: str, data: Dict[str, Any]):
        """Process webhook document creation event"""
        try:
            # Create document from webhook data
            document = Document(
                id=str(uuid.uuid4()),
                title=data.get("title", "Untitled"),
                content=data.get("content", ""),
                file_type=data.get("file_type", "unknown"),
                tags=data.get("tags", []) + ["webhook"],
                summary=data.get("summary", ""),
                uploaded_at=datetime.utcnow(),
                source_platform="webhook",
                source_id=data.get("external_id")
            )
            
            # Process document
            processed = await self.document_processor.process_document(document)
            if processed:
                await self._broadcast_sync_update(user_id, {
                    "type": "webhook_document_created",
                    "document": {
                        "id": document.id,
                        "title": document.title,
                        "status": "processed"
                    }
                })
                
        except Exception as e:
            logger.error(f"Error processing webhook document creation: {e}")

    async def connect_websocket(self, user_id: str, websocket: WebSocket):
        """Connect WebSocket for real-time updates"""
        try:
            await websocket.accept()
            self.active_connections[user_id].append(websocket)
            
            # Send initial connection confirmation
            await websocket.send_json({
                "type": "connection_established",
                "message": "Real-time sync connected",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"WebSocket connected for user {user_id}")
            
            # Keep connection alive
            try:
                while True:
                    # Wait for messages or send heartbeat
                    await asyncio.sleep(30)
                    if websocket.client_state.name != 'DISCONNECTED':
                        await websocket.send_json({
                            "type": "heartbeat",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    else:
                        break
            except Exception:
                pass
            finally:
                # Remove connection
                if websocket in self.active_connections[user_id]:
                    self.active_connections[user_id].remove(websocket)
                
        except Exception as e:
            logger.error(f"Error in WebSocket connection: {e}")

    async def _broadcast_sync_update(self, user_id: str, update: Dict[str, Any]):
        """Broadcast sync update to connected clients"""
        try:
            if user_id not in self.active_connections:
                return
            
            update["timestamp"] = datetime.utcnow().isoformat()
            
            # Send to all active connections for this user
            disconnected = []
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_json(update)
                except Exception:
                    disconnected.append(websocket)
            
            # Remove disconnected websockets
            for ws in disconnected:
                self.active_connections[user_id].remove(ws)
                
        except Exception as e:
            logger.error(f"Error broadcasting sync update: {e}")

    async def _save_integration(self, user_id: str, platform: str, integration: Dict[str, Any]):
        """Save integration configuration"""
        try:
            integration_file = f"{self.integrations_storage}/{platform}/{user_id}.json"
            async with aiofiles.open(integration_file, 'w') as f:
                await f.write(json.dumps(integration, indent=2))
        except Exception as e:
            logger.error(f"Error saving integration: {e}")

    async def _log_sync_activity(self, user_id: str, platform: str, action: str, details: Dict[str, Any]):
        """Log synchronization activity"""
        try:
            log_entry = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "platform": platform,
                "action": action,
                "details": details,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            log_file = f"{self.integrations_storage}/sync_logs/{user_id}_{datetime.utcnow().date()}.json"
            
            # Append to daily log file
            logs = []
            if Path(log_file).exists():
                async with aiofiles.open(log_file, 'r') as f:
                    logs = json.loads(await f.read())
            
            logs.append(log_entry)
            
            async with aiofiles.open(log_file, 'w') as f:
                await f.write(json.dumps(logs, indent=2))
                
        except Exception as e:
            logger.error(f"Error logging sync activity: {e}")

    async def get_integration_status(self, user_id: str) -> Dict[str, Any]:
        """Get status of all integrations for a user"""
        try:
            integrations = {}
            
            # Check each platform
            platforms = ["google_drive", "notion", "slack"]
            for platform in platforms:
                integration_file = f"{self.integrations_storage}/{platform}/{user_id}.json"
                if Path(integration_file).exists():
                    async with aiofiles.open(integration_file, 'r') as f:
                        integration_data = json.loads(await f.read())
                    integrations[platform] = {
                        "status": integration_data.get("status", "unknown"),
                        "last_sync": integration_data.get("sync_settings", {}).get("last_sync"),
                        "created_at": integration_data.get("created_at")
                    }
                else:
                    integrations[platform] = {"status": "not_configured"}
            
            # Get recent sync activity
            recent_activity = await self._get_recent_sync_activity(user_id, limit=10)
            
            return {
                "user_id": user_id,
                "integrations": integrations,
                "recent_activity": recent_activity,
                "websocket_connections": len(self.active_connections.get(user_id, [])),
                "sync_queue_size": len(self.sync_queues.get(user_id, []))
            }
            
        except Exception as e:
            logger.error(f"Error getting integration status: {e}")
            return {"error": str(e)}

    async def _get_recent_sync_activity(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent sync activity for a user"""
        try:
            activities = []
            
            # Check recent log files (last 7 days)
            for i in range(7):
                date = (datetime.utcnow() - timedelta(days=i)).date()
                log_file = f"{self.integrations_storage}/sync_logs/{user_id}_{date}.json"
                
                if Path(log_file).exists():
                    async with aiofiles.open(log_file, 'r') as f:
                        daily_logs = json.loads(await f.read())
                    activities.extend(daily_logs)
            
            # Sort by timestamp and limit
            activities.sort(key=lambda x: x["timestamp"], reverse=True)
            return activities[:limit]
            
        except Exception as e:
            logger.error(f"Error getting recent sync activity: {e}")
            return []

    async def _handle_file_deletion(self, user_id: str, source_id: str):
        """Handle file deletion from external platform"""
        try:
            # Find and mark document as deleted
            # In production, implement proper deletion handling
            logger.info(f"File deletion handled for source_id: {source_id}")
            
        except Exception as e:
            logger.error(f"Error handling file deletion: {e}")

    def health_check(self) -> Dict[str, Any]:
        """Check real-time integration service health"""
        try:
            active_users = len(self.active_connections)
            total_connections = sum(len(connections) for connections in self.active_connections.values())
            
            return {
                "status": "healthy",
                "active_users": active_users,
                "total_websocket_connections": total_connections,
                "supported_platforms": ["google_drive", "notion", "slack", "webhooks"],
                "storage_accessible": Path(self.integrations_storage).exists(),
                "capabilities": [
                    "Google Drive sync",
                    "Notion integration",
                    "Slack message archiving",
                    "Webhook endpoints",
                    "Real-time WebSocket updates",
                    "Automated document processing"
                ]
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }