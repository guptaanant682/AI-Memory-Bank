import os
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
import asyncio
from datetime import datetime

# Neo4j imports
try:
    from neo4j import GraphDatabase, AsyncGraphDatabase
    from neo4j.exceptions import ServiceUnavailable
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logging.warning("Neo4j driver not available. Knowledge graph features will be disabled.")

# NLP for entity extraction
import spacy
from collections import defaultdict, Counter

from models.schemas import Document, DocumentChunk

logger = logging.getLogger(__name__)

class KnowledgeGraph:
    """Knowledge graph service using Neo4j for storing and querying entity relationships"""
    
    def __init__(self):
        self.driver = None
        self.nlp = None
        self._local_graph = defaultdict(list)  # Fallback local storage
        self._initialize_connections()
    
    def _initialize_connections(self):
        """Initialize Neo4j connection and NLP models"""
        try:
            # Initialize Neo4j driver
            if NEO4J_AVAILABLE:
                uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
                user = os.getenv("NEO4J_USER", "neo4j")
                password = os.getenv("NEO4J_PASSWORD", "password123")
                
                self.driver = GraphDatabase.driver(uri, auth=(user, password))
                
                # Test connection
                with self.driver.session() as session:
                    session.run("RETURN 1 as test").single()
                
                logger.info(f"Neo4j connected successfully at {uri}")
            else:
                logger.warning("Neo4j not available, using local fallback")
            
            # Initialize spaCy for entity extraction
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("spaCy NLP model loaded for entity extraction")
            except OSError:
                logger.warning("spaCy model not available, entity extraction will be limited")
                
        except Exception as e:
            logger.error(f"Error initializing knowledge graph: {e}")
            self.driver = None
    
    async def extract_entities_and_relationships(self, document: Document) -> Dict[str, Any]:
        """Extract entities and relationships from document content"""
        try:
            if not self.nlp:
                return self._fallback_entity_extraction(document)
            
            # Process document content with spaCy
            doc_nlp = self.nlp(document.content[:10000])  # Limit for performance
            
            # Extract entities
            entities = self._extract_entities(doc_nlp)
            
            # Extract relationships
            relationships = self._extract_relationships(doc_nlp, entities)
            
            # Extract concepts from document
            concepts = self._extract_concepts(document, doc_nlp)
            
            return {
                "document_id": document.id,
                "entities": entities,
                "relationships": relationships,
                "concepts": concepts,
                "processed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error extracting entities from document {document.id}: {e}")
            return self._fallback_entity_extraction(document)
    
    def _extract_entities(self, doc) -> List[Dict[str, Any]]:
        """Extract named entities from spaCy doc"""
        entities = []
        
        for ent in doc.ents:
            if len(ent.text.strip()) > 1 and ent.label_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT', 'EVENT', 'WORK_OF_ART', 'LAW', 'LANGUAGE']:
                entities.append({
                    "text": ent.text.strip(),
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "confidence": 1.0  # spaCy doesn't provide confidence, using 1.0
                })
        
        # Deduplicate entities
        seen = set()
        unique_entities = []
        for entity in entities:
            key = (entity["text"].lower(), entity["label"])
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    def _extract_relationships(self, doc, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract relationships between entities using dependency parsing"""
        relationships = []
        entity_texts = {ent["text"].lower() for ent in entities}
        
        for sent in doc.sents:
            # Look for subject-verb-object patterns
            for token in sent:
                if token.dep_ == "nsubj" and token.head.pos_ == "VERB":
                    subject = token.text.lower()
                    verb = token.head.text.lower()
                    
                    # Find object
                    objects = [child for child in token.head.children if child.dep_ in ["dobj", "pobj", "attr"]]
                    
                    for obj in objects:
                        if subject in entity_texts and obj.text.lower() in entity_texts:
                            relationships.append({
                                "subject": subject,
                                "predicate": verb,
                                "object": obj.text.lower(),
                                "confidence": 0.8,
                                "sentence": sent.text.strip()
                            })
        
        return relationships
    
    def _extract_concepts(self, document: Document, doc) -> List[Dict[str, Any]]:
        """Extract key concepts and topics from document"""
        concepts = []
        
        # Use document tags as concepts
        for tag in document.tags:
            concepts.append({
                "name": tag,
                "type": "topic",
                "frequency": 1,
                "source": "document_tags"
            })
        
        # Extract noun phrases as potential concepts
        noun_phrases = [chunk.text.lower().strip() for chunk in doc.noun_chunks 
                       if len(chunk.text.split()) <= 4 and len(chunk.text.strip()) > 3]
        
        # Count frequency and filter
        phrase_counts = Counter(noun_phrases)
        for phrase, count in phrase_counts.most_common(20):
            if count >= 2:  # Only concepts mentioned multiple times
                concepts.append({
                    "name": phrase,
                    "type": "concept",
                    "frequency": count,
                    "source": "noun_phrases"
                })
        
        return concepts
    
    def _fallback_entity_extraction(self, document: Document) -> Dict[str, Any]:
        """Fallback entity extraction when spaCy is not available"""
        # Simple keyword-based extraction
        entities = []
        relationships = []
        concepts = []
        
        # Use document tags as entities and concepts
        for tag in document.tags:
            entities.append({
                "text": tag,
                "label": "TOPIC",
                "confidence": 0.5
            })
            concepts.append({
                "name": tag,
                "type": "topic",
                "frequency": 1,
                "source": "fallback"
            })
        
        return {
            "document_id": document.id,
            "entities": entities,
            "relationships": relationships,
            "concepts": concepts,
            "processed_at": datetime.utcnow().isoformat()
        }
    
    async def store_knowledge(self, knowledge_data: Dict[str, Any]) -> bool:
        """Store extracted knowledge in Neo4j graph database"""
        try:
            if self.driver:
                return await self._store_in_neo4j(knowledge_data)
            else:
                return await self._store_in_local(knowledge_data)
        except Exception as e:
            logger.error(f"Error storing knowledge: {e}")
            return False
    
    async def _store_in_neo4j(self, knowledge_data: Dict[str, Any]) -> bool:
        """Store knowledge in Neo4j database"""
        try:
            document_id = knowledge_data["document_id"]
            entities = knowledge_data.get("entities", [])
            relationships = knowledge_data.get("relationships", [])
            concepts = knowledge_data.get("concepts", [])
            
            async with self.driver.session() as session:
                # Create document node
                await session.run("""
                    MERGE (d:Document {id: $doc_id})
                    SET d.processed_at = $processed_at
                """, doc_id=document_id, processed_at=knowledge_data.get("processed_at"))
                
                # Create entity nodes and relationships to document
                for entity in entities:
                    await session.run("""
                        MERGE (e:Entity {name: $name, type: $type})
                        MERGE (d:Document {id: $doc_id})
                        MERGE (e)-[:MENTIONED_IN]->(d)
                        SET e.confidence = $confidence
                    """, 
                    name=entity["text"], 
                    type=entity["label"], 
                    doc_id=document_id,
                    confidence=entity.get("confidence", 1.0))
                
                # Create concept nodes
                for concept in concepts:
                    await session.run("""
                        MERGE (c:Concept {name: $name})
                        MERGE (d:Document {id: $doc_id})
                        MERGE (c)-[:DISCUSSED_IN {frequency: $frequency}]->(d)
                        SET c.type = $type
                    """,
                    name=concept["name"],
                    type=concept["type"],
                    doc_id=document_id,
                    frequency=concept.get("frequency", 1))
                
                # Create relationships between entities
                for rel in relationships:
                    await session.run("""
                        MERGE (s:Entity {name: $subject})
                        MERGE (o:Entity {name: $object})
                        MERGE (s)-[r:RELATES_TO {predicate: $predicate}]->(o)
                        SET r.confidence = $confidence, r.sentence = $sentence
                    """,
                    subject=rel["subject"],
                    object=rel["object"],
                    predicate=rel["predicate"],
                    confidence=rel.get("confidence", 0.8),
                    sentence=rel.get("sentence", ""))
            
            logger.info(f"Stored knowledge for document {document_id} in Neo4j")
            return True
            
        except Exception as e:
            logger.error(f"Error storing in Neo4j: {e}")
            return False
    
    async def _store_in_local(self, knowledge_data: Dict[str, Any]) -> bool:
        """Store knowledge in local fallback storage"""
        try:
            document_id = knowledge_data["document_id"]
            self._local_graph[document_id] = knowledge_data
            logger.info(f"Stored knowledge for document {document_id} in local storage")
            return True
        except Exception as e:
            logger.error(f"Error storing in local storage: {e}")
            return False
    
    async def find_related_concepts(self, concept: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Find concepts related to a given concept"""
        try:
            if self.driver:
                return await self._find_related_neo4j(concept, max_results)
            else:
                return await self._find_related_local(concept, max_results)
        except Exception as e:
            logger.error(f"Error finding related concepts: {e}")
            return []
    
    async def _find_related_neo4j(self, concept: str, max_results: int) -> List[Dict[str, Any]]:
        """Find related concepts using Neo4j graph queries"""
        try:
            async with self.driver.session() as session:
                # Find concepts that appear in the same documents
                result = await session.run("""
                    MATCH (c1:Concept {name: $concept})-[:DISCUSSED_IN]->(d:Document)<-[:DISCUSSED_IN]-(c2:Concept)
                    WHERE c1 <> c2
                    RETURN c2.name as concept, c2.type as type, count(d) as shared_documents
                    ORDER BY shared_documents DESC
                    LIMIT $limit
                """, concept=concept, limit=max_results)
                
                related = []
                async for record in result:
                    related.append({
                        "concept": record["concept"],
                        "type": record["type"],
                        "shared_documents": record["shared_documents"],
                        "relationship_type": "co_occurrence"
                    })
                
                return related
                
        except Exception as e:
            logger.error(f"Error querying Neo4j for related concepts: {e}")
            return []
    
    async def _find_related_local(self, concept: str, max_results: int) -> List[Dict[str, Any]]:
        """Find related concepts using local storage"""
        try:
            related_concepts = defaultdict(int)
            
            # Find documents containing the concept
            concept_docs = []
            for doc_id, knowledge in self._local_graph.items():
                for c in knowledge.get("concepts", []):
                    if c["name"].lower() == concept.lower():
                        concept_docs.append(doc_id)
                        break
            
            # Find other concepts in those documents
            for doc_id in concept_docs:
                knowledge = self._local_graph[doc_id]
                for c in knowledge.get("concepts", []):
                    if c["name"].lower() != concept.lower():
                        related_concepts[c["name"]] += 1
            
            # Sort by frequency
            related = []
            for concept_name, count in sorted(related_concepts.items(), key=lambda x: x[1], reverse=True)[:max_results]:
                related.append({
                    "concept": concept_name,
                    "type": "concept",
                    "shared_documents": count,
                    "relationship_type": "co_occurrence"
                })
            
            return related
            
        except Exception as e:
            logger.error(f"Error finding related concepts locally: {e}")
            return []
    
    async def get_knowledge_graph_data(self, limit: int = 100) -> Dict[str, Any]:
        """Get knowledge graph data for visualization"""
        try:
            if self.driver:
                return await self._get_graph_data_neo4j(limit)
            else:
                return await self._get_graph_data_local(limit)
        except Exception as e:
            logger.error(f"Error getting knowledge graph data: {e}")
            return {"nodes": [], "edges": []}
    
    async def _get_graph_data_neo4j(self, limit: int) -> Dict[str, Any]:
        """Get graph data from Neo4j for visualization"""
        try:
            nodes = []
            edges = []
            
            async with self.driver.session() as session:
                # Get concept nodes
                result = await session.run("""
                    MATCH (c:Concept)-[r:DISCUSSED_IN]->(d:Document)
                    RETURN c.name as name, c.type as type, count(r) as document_count
                    ORDER BY document_count DESC
                    LIMIT $limit
                """, limit=limit)
                
                async for record in result:
                    nodes.append({
                        "id": record["name"],
                        "label": record["name"],
                        "type": "concept",
                        "size": min(record["document_count"] * 10, 50),
                        "color": "#3b82f6"
                    })
                
                # Get relationships between concepts
                result = await session.run("""
                    MATCH (c1:Concept)-[:DISCUSSED_IN]->(d:Document)<-[:DISCUSSED_IN]-(c2:Concept)
                    WHERE c1 <> c2
                    WITH c1, c2, count(d) as strength
                    WHERE strength >= 2
                    RETURN c1.name as source, c2.name as target, strength
                    LIMIT $limit
                """, limit=limit)
                
                async for record in result:
                    edges.append({
                        "source": record["source"],
                        "target": record["target"],
                        "strength": record["strength"],
                        "type": "co_occurrence"
                    })
            
            return {
                "nodes": nodes,
                "edges": edges,
                "metadata": {
                    "total_nodes": len(nodes),
                    "total_edges": len(edges),
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting Neo4j graph data: {e}")
            return {"nodes": [], "edges": []}
    
    async def _get_graph_data_local(self, limit: int) -> Dict[str, Any]:
        """Get graph data from local storage for visualization"""
        try:
            concept_counts = defaultdict(int)
            concept_co_occurrence = defaultdict(int)
            
            # Count concepts and co-occurrences
            for doc_id, knowledge in self._local_graph.items():
                doc_concepts = [c["name"] for c in knowledge.get("concepts", [])]
                
                for concept in doc_concepts:
                    concept_counts[concept] += 1
                
                # Co-occurrence relationships
                for i, c1 in enumerate(doc_concepts):
                    for c2 in doc_concepts[i+1:]:
                        key = tuple(sorted([c1, c2]))
                        concept_co_occurrence[key] += 1
            
            # Create nodes
            nodes = []
            for concept, count in sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)[:limit]:
                nodes.append({
                    "id": concept,
                    "label": concept,
                    "type": "concept",
                    "size": min(count * 10, 50),
                    "color": "#3b82f6"
                })
            
            # Create edges
            edges = []
            node_ids = {node["id"] for node in nodes}
            for (c1, c2), strength in concept_co_occurrence.items():
                if strength >= 2 and c1 in node_ids and c2 in node_ids:
                    edges.append({
                        "source": c1,
                        "target": c2,
                        "strength": strength,
                        "type": "co_occurrence"
                    })
            
            return {
                "nodes": nodes,
                "edges": edges,
                "metadata": {
                    "total_nodes": len(nodes),
                    "total_edges": len(edges),
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting local graph data: {e}")
            return {"nodes": [], "edges": []}
    
    async def search_knowledge_paths(self, start_concept: str, end_concept: str, max_depth: int = 3) -> List[List[str]]:
        """Find knowledge paths between two concepts"""
        try:
            if self.driver:
                return await self._search_paths_neo4j(start_concept, end_concept, max_depth)
            else:
                return await self._search_paths_local(start_concept, end_concept, max_depth)
        except Exception as e:
            logger.error(f"Error searching knowledge paths: {e}")
            return []
    
    async def _search_paths_neo4j(self, start: str, end: str, max_depth: int) -> List[List[str]]:
        """Search for paths in Neo4j graph"""
        try:
            async with self.driver.session() as session:
                result = await session.run("""
                    MATCH path = shortestPath((start:Concept {name: $start})-[:DISCUSSED_IN|:RELATES_TO*1..{}]-(end:Concept {name: $end}))
                    RETURN [node in nodes(path) | node.name] as path
                    LIMIT 10
                """.format(max_depth * 2), start=start, end=end)
                
                paths = []
                async for record in result:
                    paths.append(record["path"])
                
                return paths
                
        except Exception as e:
            logger.error(f"Error searching Neo4j paths: {e}")
            return []
    
    async def _search_paths_local(self, start: str, end: str, max_depth: int) -> List[List[str]]:
        """Search for paths in local storage using BFS"""
        try:
            # Build adjacency list
            adjacency = defaultdict(set)
            for doc_id, knowledge in self._local_graph.items():
                concepts = [c["name"] for c in knowledge.get("concepts", [])]
                for i, c1 in enumerate(concepts):
                    for c2 in concepts[i+1:]:
                        adjacency[c1].add(c2)
                        adjacency[c2].add(c1)
            
            # BFS to find shortest path
            if start not in adjacency or end not in adjacency:
                return []
            
            from collections import deque
            queue = deque([(start, [start])])
            visited = {start}
            
            while queue:
                current, path = queue.popleft()
                
                if len(path) > max_depth:
                    continue
                
                if current == end:
                    return [path]
                
                for neighbor in adjacency[current]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))
            
            return []
            
        except Exception as e:
            logger.error(f"Error searching local paths: {e}")
            return []
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
    
    def health_check(self) -> Dict[str, Any]:
        """Check knowledge graph service health"""
        status = "healthy"
        details = {
            "neo4j_available": NEO4J_AVAILABLE,
            "neo4j_connected": False,
            "nlp_available": bool(self.nlp),
            "storage_type": "neo4j" if self.driver else "local"
        }
        
        try:
            if self.driver:
                with self.driver.session() as session:
                    session.run("RETURN 1").single()
                    details["neo4j_connected"] = True
            
            if self._local_graph:
                details["local_documents"] = len(self._local_graph)
                
        except Exception as e:
            status = "degraded"
            details["error"] = str(e)
        
        return {"status": status, **details}