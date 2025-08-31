import logging
import asyncio
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

# Database imports
import json
from pathlib import Path

from models.schemas import Document

logger = logging.getLogger(__name__)

class PermissionLevel(str, Enum):
    OWNER = "owner"
    ADMIN = "admin" 
    EDITOR = "editor"
    VIEWER = "viewer"

class WorkspaceStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    PRIVATE = "private"

class CollaborationService:
    """Service for managing collaborative workspaces and shared knowledge"""
    
    def __init__(self):
        self.workspaces_storage = "collaboration_data"
        Path(self.workspaces_storage).mkdir(exist_ok=True)
        self._ensure_storage_structure()
    
    def _ensure_storage_structure(self):
        """Ensure collaboration storage directories exist"""
        subdirs = ["workspaces", "invitations", "activities", "shared_graphs"]
        for subdir in subdirs:
            Path(f"{self.workspaces_storage}/{subdir}").mkdir(exist_ok=True)
    
    async def create_workspace(self, owner_id: str, name: str, description: str = "", is_public: bool = False) -> Dict[str, Any]:
        """Create a new collaborative workspace"""
        try:
            workspace_id = str(uuid.uuid4())
            workspace = {
                "id": workspace_id,
                "name": name,
                "description": description,
                "owner_id": owner_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "status": WorkspaceStatus.ACTIVE.value,
                "is_public": is_public,
                "members": [{
                    "user_id": owner_id,
                    "permission": PermissionLevel.OWNER.value,
                    "joined_at": datetime.utcnow().isoformat(),
                    "invited_by": owner_id,
                    "status": "active"
                }],
                "settings": {
                    "allow_public_contributions": is_public,
                    "require_approval_for_edits": False,
                    "enable_real_time_collaboration": True,
                    "auto_backup": True
                },
                "statistics": {
                    "document_count": 0,
                    "member_count": 1,
                    "activity_count": 0,
                    "knowledge_graph_size": 0
                }
            }
            
            # Save workspace
            workspace_file = f"{self.workspaces_storage}/workspaces/{workspace_id}.json"
            with open(workspace_file, 'w') as f:
                json.dump(workspace, f, indent=2)
            
            # Log activity
            await self._log_activity(workspace_id, owner_id, "workspace_created", {
                "workspace_name": name,
                "description": description
            })
            
            logger.info(f"Created workspace {workspace_id} for user {owner_id}")
            return workspace
            
        except Exception as e:
            logger.error(f"Error creating workspace: {e}")
            raise
    
    async def get_workspace(self, workspace_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get workspace details if user has access"""
        try:
            workspace_file = f"{self.workspaces_storage}/workspaces/{workspace_id}.json"
            
            if not Path(workspace_file).exists():
                return None
            
            with open(workspace_file, 'r') as f:
                workspace = json.load(f)
            
            # Check if user has access
            if not await self._user_has_access(workspace, user_id):
                if not workspace.get("is_public", False):
                    return None
            
            return workspace
            
        except Exception as e:
            logger.error(f"Error getting workspace {workspace_id}: {e}")
            return None
    
    async def get_user_workspaces(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all workspaces accessible to a user"""
        try:
            workspaces = []
            workspaces_dir = Path(f"{self.workspaces_storage}/workspaces")
            
            for workspace_file in workspaces_dir.glob("*.json"):
                try:
                    with open(workspace_file, 'r') as f:
                        workspace = json.load(f)
                    
                    # Check if user has access or if workspace is public
                    if await self._user_has_access(workspace, user_id) or workspace.get("is_public", False):
                        # Add user's permission level
                        user_permission = await self._get_user_permission(workspace, user_id)
                        workspace["user_permission"] = user_permission
                        workspaces.append(workspace)
                
                except Exception as e:
                    logger.warning(f"Error reading workspace file {workspace_file}: {e}")
                    continue
            
            # Sort by most recent activity
            workspaces.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            return workspaces
            
        except Exception as e:
            logger.error(f"Error getting user workspaces: {e}")
            return []
    
    async def invite_user(self, workspace_id: str, inviter_id: str, invitee_email: str, permission: str = PermissionLevel.VIEWER.value) -> Dict[str, Any]:
        """Invite a user to a workspace"""
        try:
            workspace = await self.get_workspace(workspace_id, inviter_id)
            if not workspace:
                raise ValueError("Workspace not found or access denied")
            
            # Check if inviter has permission to invite
            inviter_permission = await self._get_user_permission(workspace, inviter_id)
            if inviter_permission not in [PermissionLevel.OWNER.value, PermissionLevel.ADMIN.value]:
                raise ValueError("Insufficient permissions to invite users")
            
            # Create invitation
            invitation_id = str(uuid.uuid4())
            invitation = {
                "id": invitation_id,
                "workspace_id": workspace_id,
                "workspace_name": workspace["name"],
                "inviter_id": inviter_id,
                "invitee_email": invitee_email,
                "permission": permission,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "status": "pending",
                "invitation_message": f"You've been invited to collaborate on the '{workspace['name']}' knowledge workspace."
            }
            
            # Save invitation
            invitation_file = f"{self.workspaces_storage}/invitations/{invitation_id}.json"
            with open(invitation_file, 'w') as f:
                json.dump(invitation, f, indent=2)
            
            # Log activity
            await self._log_activity(workspace_id, inviter_id, "user_invited", {
                "invitee_email": invitee_email,
                "permission": permission
            })
            
            logger.info(f"Created invitation {invitation_id} for workspace {workspace_id}")
            return invitation
            
        except Exception as e:
            logger.error(f"Error creating invitation: {e}")
            raise
    
    async def accept_invitation(self, invitation_id: str, user_id: str) -> Dict[str, Any]:
        """Accept a workspace invitation"""
        try:
            invitation_file = f"{self.workspaces_storage}/invitations/{invitation_id}.json"
            
            if not Path(invitation_file).exists():
                raise ValueError("Invitation not found")
            
            with open(invitation_file, 'r') as f:
                invitation = json.load(f)
            
            # Check if invitation is still valid
            if invitation["status"] != "pending":
                raise ValueError("Invitation is no longer valid")
            
            expires_at = datetime.fromisoformat(invitation["expires_at"])
            if datetime.utcnow() > expires_at:
                raise ValueError("Invitation has expired")
            
            # Add user to workspace
            workspace_id = invitation["workspace_id"]
            workspace = await self.get_workspace(workspace_id, invitation["inviter_id"])
            
            if not workspace:
                raise ValueError("Workspace not found")
            
            # Add member to workspace
            new_member = {
                "user_id": user_id,
                "permission": invitation["permission"],
                "joined_at": datetime.utcnow().isoformat(),
                "invited_by": invitation["inviter_id"],
                "status": "active"
            }
            
            workspace["members"].append(new_member)
            workspace["updated_at"] = datetime.utcnow().isoformat()
            workspace["statistics"]["member_count"] = len(workspace["members"])
            
            # Save updated workspace
            workspace_file = f"{self.workspaces_storage}/workspaces/{workspace_id}.json"
            with open(workspace_file, 'w') as f:
                json.dump(workspace, f, indent=2)
            
            # Update invitation status
            invitation["status"] = "accepted"
            invitation["accepted_at"] = datetime.utcnow().isoformat()
            invitation["accepted_by"] = user_id
            
            with open(invitation_file, 'w') as f:
                json.dump(invitation, f, indent=2)
            
            # Log activity
            await self._log_activity(workspace_id, user_id, "invitation_accepted", {
                "inviter_id": invitation["inviter_id"],
                "permission": invitation["permission"]
            })
            
            return {
                "workspace": workspace,
                "invitation": invitation,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error accepting invitation: {e}")
            raise
    
    async def share_document(self, document_id: str, workspace_id: str, user_id: str, permission: str = "view") -> Dict[str, Any]:
        """Share a document with a workspace"""
        try:
            workspace = await self.get_workspace(workspace_id, user_id)
            if not workspace:
                raise ValueError("Workspace not found or access denied")
            
            # Check user permissions
            user_permission = await self._get_user_permission(workspace, user_id)
            if user_permission not in [PermissionLevel.OWNER.value, PermissionLevel.ADMIN.value, PermissionLevel.EDITOR.value]:
                raise ValueError("Insufficient permissions to share documents")
            
            # Create shared document entry
            shared_doc = {
                "document_id": document_id,
                "workspace_id": workspace_id,
                "shared_by": user_id,
                "shared_at": datetime.utcnow().isoformat(),
                "permission": permission,
                "status": "active"
            }
            
            # Save shared document info
            shared_docs_file = f"{self.workspaces_storage}/workspaces/{workspace_id}_shared_docs.json"
            shared_docs = []
            
            if Path(shared_docs_file).exists():
                with open(shared_docs_file, 'r') as f:
                    shared_docs = json.load(f)
            
            shared_docs.append(shared_doc)
            
            with open(shared_docs_file, 'w') as f:
                json.dump(shared_docs, f, indent=2)
            
            # Update workspace statistics
            workspace["statistics"]["document_count"] += 1
            workspace["updated_at"] = datetime.utcnow().isoformat()
            
            workspace_file = f"{self.workspaces_storage}/workspaces/{workspace_id}.json"
            with open(workspace_file, 'w') as f:
                json.dump(workspace, f, indent=2)
            
            # Log activity
            await self._log_activity(workspace_id, user_id, "document_shared", {
                "document_id": document_id,
                "permission": permission
            })
            
            return shared_doc
            
        except Exception as e:
            logger.error(f"Error sharing document: {e}")
            raise
    
    async def get_shared_documents(self, workspace_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get documents shared with a workspace"""
        try:
            workspace = await self.get_workspace(workspace_id, user_id)
            if not workspace:
                return []
            
            shared_docs_file = f"{self.workspaces_storage}/workspaces/{workspace_id}_shared_docs.json"
            
            if not Path(shared_docs_file).exists():
                return []
            
            with open(shared_docs_file, 'r') as f:
                shared_docs = json.load(f)
            
            # Filter active documents
            active_docs = [doc for doc in shared_docs if doc.get("status") == "active"]
            
            return active_docs
            
        except Exception as e:
            logger.error(f"Error getting shared documents: {e}")
            return []
    
    async def create_shared_knowledge_graph(self, workspace_id: str, creator_id: str, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a shared knowledge graph for the workspace"""
        try:
            workspace = await self.get_workspace(workspace_id, creator_id)
            if not workspace:
                raise ValueError("Workspace not found or access denied")
            
            shared_graph = {
                "id": str(uuid.uuid4()),
                "workspace_id": workspace_id,
                "created_by": creator_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "name": f"{workspace['name']} - Knowledge Graph",
                "description": "Collaborative knowledge graph for the workspace",
                "graph_data": graph_data,
                "contributors": [creator_id],
                "version": 1,
                "status": "active"
            }
            
            # Save shared graph
            graph_file = f"{self.workspaces_storage}/shared_graphs/{workspace_id}.json"
            with open(graph_file, 'w') as f:
                json.dump(shared_graph, f, indent=2)
            
            # Update workspace statistics
            workspace["statistics"]["knowledge_graph_size"] = len(graph_data.get("nodes", []))
            workspace["updated_at"] = datetime.utcnow().isoformat()
            
            workspace_file = f"{self.workspaces_storage}/workspaces/{workspace_id}.json"
            with open(workspace_file, 'w') as f:
                json.dump(workspace, f, indent=2)
            
            # Log activity
            await self._log_activity(workspace_id, creator_id, "knowledge_graph_created", {
                "node_count": len(graph_data.get("nodes", [])),
                "edge_count": len(graph_data.get("edges", []))
            })
            
            return shared_graph
            
        except Exception as e:
            logger.error(f"Error creating shared knowledge graph: {e}")
            raise
    
    async def get_workspace_activities(self, workspace_id: str, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent activities in a workspace"""
        try:
            workspace = await self.get_workspace(workspace_id, user_id)
            if not workspace:
                return []
            
            activities_file = f"{self.workspaces_storage}/activities/{workspace_id}.json"
            
            if not Path(activities_file).exists():
                return []
            
            with open(activities_file, 'r') as f:
                activities = json.load(f)
            
            # Sort by timestamp and limit
            activities.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return activities[:limit]
            
        except Exception as e:
            logger.error(f"Error getting workspace activities: {e}")
            return []
    
    async def update_member_permission(self, workspace_id: str, admin_id: str, member_id: str, new_permission: str) -> bool:
        """Update a member's permission level"""
        try:
            workspace = await self.get_workspace(workspace_id, admin_id)
            if not workspace:
                raise ValueError("Workspace not found or access denied")
            
            # Check if admin has permission to modify permissions
            admin_permission = await self._get_user_permission(workspace, admin_id)
            if admin_permission not in [PermissionLevel.OWNER.value, PermissionLevel.ADMIN.value]:
                raise ValueError("Insufficient permissions to modify member permissions")
            
            # Find and update member
            member_updated = False
            for member in workspace["members"]:
                if member["user_id"] == member_id:
                    member["permission"] = new_permission
                    member["permission_updated_at"] = datetime.utcnow().isoformat()
                    member["permission_updated_by"] = admin_id
                    member_updated = True
                    break
            
            if not member_updated:
                raise ValueError("Member not found in workspace")
            
            workspace["updated_at"] = datetime.utcnow().isoformat()
            
            # Save updated workspace
            workspace_file = f"{self.workspaces_storage}/workspaces/{workspace_id}.json"
            with open(workspace_file, 'w') as f:
                json.dump(workspace, f, indent=2)
            
            # Log activity
            await self._log_activity(workspace_id, admin_id, "permission_updated", {
                "member_id": member_id,
                "new_permission": new_permission
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating member permission: {e}")
            raise
    
    async def _user_has_access(self, workspace: Dict[str, Any], user_id: str) -> bool:
        """Check if user has access to workspace"""
        return any(member["user_id"] == user_id for member in workspace.get("members", []))
    
    async def _get_user_permission(self, workspace: Dict[str, Any], user_id: str) -> Optional[str]:
        """Get user's permission level in workspace"""
        for member in workspace.get("members", []):
            if member["user_id"] == user_id:
                return member.get("permission")
        return None
    
    async def _log_activity(self, workspace_id: str, user_id: str, action: str, details: Dict[str, Any] = None):
        """Log activity in workspace"""
        try:
            activity = {
                "id": str(uuid.uuid4()),
                "workspace_id": workspace_id,
                "user_id": user_id,
                "action": action,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            activities_file = f"{self.workspaces_storage}/activities/{workspace_id}.json"
            activities = []
            
            if Path(activities_file).exists():
                with open(activities_file, 'r') as f:
                    activities = json.load(f)
            
            activities.append(activity)
            
            # Keep only last 1000 activities
            activities = activities[-1000:]
            
            with open(activities_file, 'w') as f:
                json.dump(activities, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
    
    async def get_collaboration_analytics(self, workspace_id: str, user_id: str) -> Dict[str, Any]:
        """Get collaboration analytics for a workspace"""
        try:
            workspace = await self.get_workspace(workspace_id, user_id)
            if not workspace:
                return {}
            
            activities = await self.get_workspace_activities(workspace_id, user_id, limit=1000)
            
            analytics = {
                "workspace_id": workspace_id,
                "generated_at": datetime.utcnow().isoformat(),
                "member_analytics": {},
                "activity_trends": {},
                "collaboration_score": 0,
                "engagement_metrics": {}
            }
            
            # Analyze member contributions
            member_contributions = defaultdict(int)
            activity_types = defaultdict(int)
            daily_activities = defaultdict(int)
            
            for activity in activities:
                member_contributions[activity["user_id"]] += 1
                activity_types[activity["action"]] += 1
                
                # Group by day
                activity_date = datetime.fromisoformat(activity["timestamp"]).date().isoformat()
                daily_activities[activity_date] += 1
            
            analytics["member_analytics"] = {
                "total_contributions": dict(member_contributions),
                "most_active_member": max(member_contributions.items(), key=lambda x: x[1])[0] if member_contributions else None
            }
            
            analytics["activity_trends"] = {
                "activity_types": dict(activity_types),
                "daily_activity": dict(daily_activities),
                "total_activities": len(activities)
            }
            
            # Calculate collaboration score (0-100)
            base_score = min(len(workspace["members"]) * 10, 50)  # Member count contribution
            activity_score = min(len(activities) / 10, 30)  # Activity contribution
            diversity_score = min(len(activity_types) * 5, 20)  # Activity diversity
            
            analytics["collaboration_score"] = int(base_score + activity_score + diversity_score)
            
            analytics["engagement_metrics"] = {
                "average_activities_per_member": round(len(activities) / len(workspace["members"]), 2),
                "active_days": len(daily_activities),
                "collaboration_intensity": "High" if analytics["collaboration_score"] > 70 else "Medium" if analytics["collaboration_score"] > 40 else "Low"
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting collaboration analytics: {e}")
            return {}
    
    def health_check(self) -> Dict[str, Any]:
        """Check collaboration service health"""
        try:
            workspaces_dir = Path(f"{self.workspaces_storage}/workspaces")
            workspace_count = len(list(workspaces_dir.glob("*.json")))
            
            return {
                "status": "healthy",
                "storage_accessible": True,
                "workspace_count": workspace_count,
                "features": [
                    "Workspace management",
                    "User invitations",
                    "Document sharing",
                    "Activity tracking",
                    "Permission management",
                    "Collaboration analytics"
                ]
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }