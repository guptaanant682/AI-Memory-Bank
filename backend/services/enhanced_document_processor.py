import logging
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime

from services.document_processor import DocumentProcessor
from services.knowledge_graph import KnowledgeGraph
from models.schemas import Document, DocumentChunk

logger = logging.getLogger(__name__)

class EnhancedDocumentProcessor(DocumentProcessor):
    """Enhanced document processor with knowledge graph integration"""
    
    def __init__(self):
        super().__init__()
        self.knowledge_graph = KnowledgeGraph()
    
    async def process_file_with_knowledge_extraction(self, file_path: str) -> Dict[str, Any]:
        """Process file and extract knowledge graph data"""
        try:
            # Process document normally
            document = await self.process_file(file_path)
            
            # Extract knowledge graph data
            knowledge_data = await self.knowledge_graph.extract_entities_and_relationships(document)
            
            # Store knowledge in graph database
            graph_stored = await self.knowledge_graph.store_knowledge(knowledge_data)
            
            # Enhanced document with knowledge data
            enhanced_result = {
                "document": document,
                "chunks": getattr(self, 'chunks', []),
                "knowledge": knowledge_data,
                "graph_stored": graph_stored,
                "processing_metadata": {
                    "processed_at": datetime.utcnow().isoformat(),
                    "entities_extracted": len(knowledge_data.get("entities", [])),
                    "relationships_found": len(knowledge_data.get("relationships", [])),
                    "concepts_identified": len(knowledge_data.get("concepts", []))
                }
            }
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error in enhanced document processing: {e}")
            # Fallback to basic processing
            document = await self.process_file(file_path)
            return {
                "document": document,
                "chunks": getattr(self, 'chunks', []),
                "knowledge": None,
                "graph_stored": False,
                "error": str(e)
            }
    
    async def analyze_document_context(self, document: Document) -> Dict[str, Any]:
        """Analyze document context using knowledge graph"""
        try:
            context_analysis = {
                "document_id": document.id,
                "related_concepts": [],
                "knowledge_paths": [],
                "semantic_connections": [],
                "topic_coverage": {}
            }
            
            # Find related concepts for each tag
            for tag in document.tags:
                related = await self.knowledge_graph.find_related_concepts(tag, max_results=5)
                if related:
                    context_analysis["related_concepts"].extend([
                        {
                            "source_tag": tag,
                            "related_concept": rel["concept"],
                            "relationship_strength": rel.get("shared_documents", 0),
                            "relationship_type": rel.get("relationship_type", "unknown")
                        }
                        for rel in related
                    ])
            
            # Analyze topic coverage
            context_analysis["topic_coverage"] = await self._analyze_topic_coverage(document)
            
            return context_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing document context: {e}")
            return {"error": str(e)}
    
    async def _analyze_topic_coverage(self, document: Document) -> Dict[str, Any]:
        """Analyze how well document covers different topics"""
        try:
            coverage = {
                "primary_topics": document.tags[:5],  # Top 5 tags as primary topics
                "topic_depth": {},
                "cross_topic_connections": []
            }
            
            # Estimate topic depth based on content length and tag frequency
            content_length = len(document.content.split())
            for tag in document.tags:
                # Simple depth estimation
                tag_mentions = document.content.lower().count(tag.lower())
                depth_score = min(tag_mentions / max(content_length / 1000, 1), 5.0)
                coverage["topic_depth"][tag] = {
                    "mentions": tag_mentions,
                    "depth_score": round(depth_score, 2),
                    "coverage_percentage": round((tag_mentions / content_length) * 100, 2) if content_length > 0 else 0
                }
            
            # Find cross-topic connections
            for i, tag1 in enumerate(document.tags):
                for tag2 in document.tags[i+1:]:
                    paths = await self.knowledge_graph.search_knowledge_paths(tag1, tag2, max_depth=2)
                    if paths:
                        coverage["cross_topic_connections"].append({
                            "topic1": tag1,
                            "topic2": tag2,
                            "connection_paths": paths,
                            "path_count": len(paths)
                        })
            
            return coverage
            
        except Exception as e:
            logger.error(f"Error analyzing topic coverage: {e}")
            return {}
    
    async def suggest_related_documents(self, document: Document, limit: int = 10) -> List[Dict[str, Any]]:
        """Suggest documents related to the current document using knowledge graph"""
        try:
            suggestions = []
            
            # Use document tags to find related concepts
            for tag in document.tags:
                related_concepts = await self.knowledge_graph.find_related_concepts(tag, max_results=3)
                
                for related in related_concepts:
                    suggestions.append({
                        "suggestion_type": "concept_similarity",
                        "source_tag": tag,
                        "related_concept": related["concept"],
                        "strength": related.get("shared_documents", 0),
                        "reason": f"Documents discussing '{tag}' often also cover '{related['concept']}'"
                    })
            
            # Sort by strength and remove duplicates
            suggestions = sorted(suggestions, key=lambda x: x["strength"], reverse=True)
            
            # Deduplicate by related_concept
            seen_concepts = set()
            unique_suggestions = []
            for suggestion in suggestions:
                concept = suggestion["related_concept"]
                if concept not in seen_concepts:
                    seen_concepts.add(concept)
                    unique_suggestions.append(suggestion)
            
            return unique_suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Error suggesting related documents: {e}")
            return []
    
    async def generate_knowledge_summary(self, document_ids: List[str]) -> Dict[str, Any]:
        """Generate a knowledge summary across multiple documents"""
        try:
            summary = {
                "document_count": len(document_ids),
                "knowledge_overview": {
                    "total_concepts": 0,
                    "total_entities": 0,
                    "total_relationships": 0,
                    "dominant_topics": [],
                    "knowledge_clusters": []
                },
                "cross_document_insights": {
                    "shared_concepts": [],
                    "concept_evolution": [],
                    "knowledge_gaps": []
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Get knowledge graph data
            graph_data = await self.knowledge_graph.get_knowledge_graph_data(limit=200)
            
            if graph_data.get("nodes"):
                # Analyze concept distribution
                concept_sizes = [node.get("size", 0) for node in graph_data["nodes"]]
                summary["knowledge_overview"]["total_concepts"] = len(graph_data["nodes"])
                summary["knowledge_overview"]["total_relationships"] = len(graph_data.get("edges", []))
                
                # Find dominant topics (largest nodes)
                dominant_nodes = sorted(graph_data["nodes"], key=lambda x: x.get("size", 0), reverse=True)[:10]
                summary["knowledge_overview"]["dominant_topics"] = [
                    {
                        "concept": node["label"],
                        "importance_score": node.get("size", 0),
                        "type": node.get("type", "unknown")
                    }
                    for node in dominant_nodes
                ]
                
                # Identify knowledge clusters (highly connected concepts)
                edge_counts = {}
                for edge in graph_data.get("edges", []):
                    source = edge["source"]
                    target = edge["target"]
                    edge_counts[source] = edge_counts.get(source, 0) + 1
                    edge_counts[target] = edge_counts.get(target, 0) + 1
                
                highly_connected = sorted(edge_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                summary["knowledge_overview"]["knowledge_clusters"] = [
                    {
                        "central_concept": concept,
                        "connection_count": count,
                        "cluster_type": "hub"
                    }
                    for concept, count in highly_connected
                ]
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating knowledge summary: {e}")
            return {"error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Enhanced health check including knowledge graph"""
        base_health = super().health_check()
        graph_health = self.knowledge_graph.health_check()
        
        return {
            **base_health,
            "knowledge_graph": graph_health,
            "enhanced_processing": True
        }