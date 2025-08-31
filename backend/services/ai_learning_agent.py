import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import uuid
from collections import defaultdict, Counter

# AI imports for intelligent analysis
import numpy as np
from transformers import pipeline

from services.knowledge_graph import KnowledgeGraph
from services.vector_store import VectorStore
from services.rag_engine import RAGEngine
from models.schemas import Document

logger = logging.getLogger(__name__)

class AILearningAgent:
    """Proactive AI agent that analyzes knowledge gaps and suggests learning paths"""
    
    def __init__(self, knowledge_graph: KnowledgeGraph, vector_store: VectorStore, rag_engine: RAGEngine):
        self.knowledge_graph = knowledge_graph
        self.vector_store = vector_store
        self.rag_engine = rag_engine
        self.classifier = None
        self.user_preferences = {}
        self._initialize_ai_models()
    
    def _initialize_ai_models(self):
        """Initialize AI models for learning analysis"""
        try:
            # Initialize text classifier for topic classification
            self.classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=-1  # Use CPU
            )
            logger.info("AI Learning Agent models initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing AI models: {e}")
            self.classifier = None
    
    async def analyze_knowledge_gaps(self, user_id: str = "default") -> Dict[str, Any]:
        """Analyze user's knowledge to identify gaps and opportunities"""
        try:
            # Get all user documents and knowledge graph data
            documents = await self.vector_store.get_documents(limit=1000)
            graph_data = await self.knowledge_graph.get_knowledge_graph_data(limit=200)
            
            analysis = {
                "user_id": user_id,
                "analyzed_at": datetime.utcnow().isoformat(),
                "knowledge_coverage": {},
                "identified_gaps": [],
                "learning_opportunities": [],
                "suggested_topics": [],
                "knowledge_depth_analysis": {}
            }
            
            # Analyze knowledge coverage
            coverage = await self._analyze_knowledge_coverage(documents, graph_data)
            analysis["knowledge_coverage"] = coverage
            
            # Identify knowledge gaps
            gaps = await self._identify_knowledge_gaps(documents, graph_data)
            analysis["identified_gaps"] = gaps
            
            # Generate learning opportunities
            opportunities = await self._generate_learning_opportunities(gaps, graph_data)
            analysis["learning_opportunities"] = opportunities
            
            # Suggest new topics based on current interests
            suggested = await self._suggest_new_topics(documents, graph_data)
            analysis["suggested_topics"] = suggested
            
            # Analyze depth of knowledge in different areas
            depth_analysis = await self._analyze_knowledge_depth(documents, graph_data)
            analysis["knowledge_depth_analysis"] = depth_analysis
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing knowledge gaps: {e}")
            return {
                "error": str(e),
                "analyzed_at": datetime.utcnow().isoformat()
            }
    
    async def _analyze_knowledge_coverage(self, documents: List[Document], graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how well different knowledge areas are covered"""
        try:
            coverage = {
                "total_documents": len(documents),
                "topic_distribution": {},
                "concept_coverage": {},
                "domain_analysis": {}
            }
            
            # Analyze topic distribution
            all_tags = []
            for doc in documents:
                all_tags.extend(doc.tags)
            
            tag_counts = Counter(all_tags)
            total_tags = len(all_tags)
            
            coverage["topic_distribution"] = {
                tag: {
                    "count": count,
                    "percentage": round((count / total_tags) * 100, 2) if total_tags > 0 else 0
                }
                for tag, count in tag_counts.most_common(20)
            }
            
            # Analyze concept coverage from knowledge graph
            nodes = graph_data.get("nodes", [])
            if nodes:
                concept_sizes = [node.get("size", 0) for node in nodes]
                coverage["concept_coverage"] = {
                    "total_concepts": len(nodes),
                    "highly_connected": len([n for n in nodes if n.get("size", 0) > 30]),
                    "moderately_connected": len([n for n in nodes if 10 <= n.get("size", 0) <= 30]),
                    "weakly_connected": len([n for n in nodes if n.get("size", 0) < 10]),
                    "average_connections": round(np.mean(concept_sizes), 2) if concept_sizes else 0
                }
            
            # Domain analysis using AI classification if available
            if self.classifier and documents:
                domains = await self._classify_knowledge_domains(documents)
                coverage["domain_analysis"] = domains
            
            return coverage
            
        except Exception as e:
            logger.error(f"Error analyzing knowledge coverage: {e}")
            return {}
    
    async def _classify_knowledge_domains(self, documents: List[Document]) -> Dict[str, Any]:
        """Classify documents into knowledge domains using AI"""
        try:
            # Define knowledge domains for classification
            candidate_domains = [
                "Technology and Programming",
                "Science and Research",
                "Business and Management",
                "Arts and Creativity",
                "Health and Medicine",
                "Education and Learning",
                "Personal Development",
                "History and Culture",
                "Philosophy and Ethics",
                "Mathematics and Logic"
            ]
            
            domain_classification = defaultdict(list)
            
            # Classify a sample of documents
            sample_docs = documents[:50]  # Limit for performance
            
            for doc in sample_docs:
                try:
                    # Use document title and summary for classification
                    text_to_classify = f"{doc.title}. {doc.summary or doc.content[:500]}"
                    
                    result = self.classifier(text_to_classify, candidate_domains)
                    
                    # Get top domain with confidence > 0.3
                    if result['scores'][0] > 0.3:
                        top_domain = result['labels'][0]
                        confidence = result['scores'][0]
                        
                        domain_classification[top_domain].append({
                            "document_id": doc.id,
                            "title": doc.title,
                            "confidence": round(confidence, 3)
                        })
                
                except Exception as e:
                    logger.warning(f"Error classifying document {doc.id}: {e}")
                    continue
            
            # Calculate domain statistics
            domain_stats = {}
            total_classified = sum(len(docs) for docs in domain_classification.values())
            
            for domain, docs in domain_classification.items():
                domain_stats[domain] = {
                    "document_count": len(docs),
                    "percentage": round((len(docs) / total_classified) * 100, 2) if total_classified > 0 else 0,
                    "avg_confidence": round(np.mean([doc["confidence"] for doc in docs]), 3),
                    "sample_titles": [doc["title"] for doc in docs[:3]]
                }
            
            return {
                "classification_method": "AI-powered domain classification",
                "domains": domain_stats,
                "total_classified": total_classified,
                "coverage_analysis": self._analyze_domain_coverage(domain_stats)
            }
            
        except Exception as e:
            logger.error(f"Error in domain classification: {e}")
            return {}
    
    def _analyze_domain_coverage(self, domain_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze coverage across different domains"""
        if not domain_stats:
            return {}
        
        percentages = [stats["percentage"] for stats in domain_stats.values()]
        
        return {
            "most_covered_domain": max(domain_stats.items(), key=lambda x: x[1]["percentage"])[0],
            "least_covered_domain": min(domain_stats.items(), key=lambda x: x[1]["percentage"])[0],
            "knowledge_diversity": round(len([p for p in percentages if p > 5]), 0),
            "concentration_score": round(max(percentages), 2),
            "balance_score": round(100 - (max(percentages) - np.mean(percentages)), 2)
        }
    
    async def _identify_knowledge_gaps(self, documents: List[Document], graph_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify specific knowledge gaps and missing connections"""
        try:
            gaps = []
            
            # Analyze concept connectivity gaps
            nodes = graph_data.get("nodes", [])
            edges = graph_data.get("edges", [])
            
            if nodes and edges:
                # Find isolated concepts (low connectivity)
                edge_counts = defaultdict(int)
                for edge in edges:
                    edge_counts[edge["source"]] += 1
                    edge_counts[edge["target"]] += 1
                
                isolated_concepts = []
                for node in nodes:
                    connections = edge_counts.get(node["id"], 0)
                    if connections <= 1 and node.get("size", 0) > 10:  # Important but isolated
                        isolated_concepts.append({
                            "concept": node["label"],
                            "importance": node.get("size", 0),
                            "connections": connections,
                            "gap_type": "isolated_important_concept"
                        })
                
                if isolated_concepts:
                    gaps.append({
                        "gap_category": "Connectivity Gaps",
                        "description": "Important concepts that lack connections to other knowledge areas",
                        "severity": "medium",
                        "concepts": isolated_concepts[:5],
                        "recommendation": "Explore how these concepts relate to your other knowledge areas"
                    })
            
            # Analyze topic depth gaps
            if documents:
                topic_depth = await self._analyze_topic_depth_gaps(documents)
                if topic_depth:
                    gaps.extend(topic_depth)
            
            # Identify missing foundational knowledge
            foundational_gaps = await self._identify_foundational_gaps(documents, graph_data)
            if foundational_gaps:
                gaps.extend(foundational_gaps)
            
            return gaps
            
        except Exception as e:
            logger.error(f"Error identifying knowledge gaps: {e}")
            return []
    
    async def _analyze_topic_depth_gaps(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Analyze depth of knowledge in different topics"""
        try:
            gaps = []
            
            # Count documents per topic
            topic_docs = defaultdict(list)
            for doc in documents:
                for tag in doc.tags:
                    topic_docs[tag].append(doc)
            
            # Identify topics with only surface-level coverage
            shallow_topics = []
            for topic, docs in topic_docs.items():
                if 1 <= len(docs) <= 2:  # Only 1-2 documents on this topic
                    total_content_length = sum(len(doc.content.split()) for doc in docs)
                    avg_content_length = total_content_length / len(docs)
                    
                    if avg_content_length < 1000:  # Short documents indicate shallow coverage
                        shallow_topics.append({
                            "topic": topic,
                            "document_count": len(docs),
                            "avg_content_length": round(avg_content_length),
                            "gap_type": "shallow_coverage"
                        })
            
            if shallow_topics:
                gaps.append({
                    "gap_category": "Depth Gaps",
                    "description": "Topics with only surface-level coverage that could benefit from deeper exploration",
                    "severity": "low",
                    "topics": shallow_topics[:5],
                    "recommendation": "Consider finding more comprehensive resources on these topics"
                })
            
            return gaps
            
        except Exception as e:
            logger.error(f"Error analyzing topic depth gaps: {e}")
            return []
    
    async def _identify_foundational_gaps(self, documents: List[Document], graph_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify missing foundational knowledge"""
        try:
            gaps = []
            
            # Define foundational concepts for different domains
            foundational_concepts = {
                "Technology": ["programming", "algorithms", "data structures", "databases", "networking"],
                "Science": ["scientific method", "statistics", "research methods", "peer review", "hypothesis"],
                "Business": ["finance", "marketing", "operations", "strategy", "management"],
                "Learning": ["critical thinking", "problem solving", "research skills", "note taking", "memory"]
            }
            
            # Check which foundational concepts are missing
            user_concepts = set()
            if graph_data.get("nodes"):
                user_concepts = {node["label"].lower() for node in graph_data["nodes"]}
            
            # Also add document tags
            for doc in documents:
                user_concepts.update(tag.lower() for tag in doc.tags)
            
            missing_foundational = []
            for domain, concepts in foundational_concepts.items():
                missing_in_domain = []
                for concept in concepts:
                    if not any(concept in user_concept for user_concept in user_concepts):
                        missing_in_domain.append(concept)
                
                if missing_in_domain and len(missing_in_domain) < len(concepts):  # Some domain knowledge exists
                    missing_foundational.append({
                        "domain": domain,
                        "missing_concepts": missing_in_domain,
                        "coverage_percentage": round(((len(concepts) - len(missing_in_domain)) / len(concepts)) * 100, 1)
                    })
            
            if missing_foundational:
                gaps.append({
                    "gap_category": "Foundational Knowledge Gaps",
                    "description": "Missing foundational concepts in domains where you have some knowledge",
                    "severity": "high",
                    "domains": missing_foundational,
                    "recommendation": "Consider learning these foundational concepts to strengthen your knowledge base"
                })
            
            return gaps
            
        except Exception as e:
            logger.error(f"Error identifying foundational gaps: {e}")
            return []
    
    async def _generate_learning_opportunities(self, gaps: List[Dict[str, Any]], graph_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific learning opportunities based on identified gaps"""
        try:
            opportunities = []
            
            for gap in gaps:
                gap_category = gap.get("gap_category", "")
                
                if gap_category == "Connectivity Gaps":
                    # Suggest connecting isolated concepts
                    concepts = gap.get("concepts", [])
                    for concept_info in concepts[:3]:
                        concept = concept_info["concept"]
                        opportunities.append({
                            "opportunity_type": "Bridge Knowledge",
                            "title": f"Connect '{concept}' to your other knowledge",
                            "description": f"Explore how '{concept}' relates to your existing knowledge areas",
                            "action_items": [
                                f"Search for content that connects '{concept}' to your other interests",
                                f"Look for interdisciplinary applications of '{concept}'",
                                f"Find case studies or examples that bridge '{concept}' with other domains"
                            ],
                            "priority": "medium",
                            "estimated_time": "2-4 hours"
                        })
                
                elif gap_category == "Depth Gaps":
                    # Suggest deepening knowledge
                    topics = gap.get("topics", [])
                    for topic_info in topics[:2]:
                        topic = topic_info["topic"]
                        opportunities.append({
                            "opportunity_type": "Deepen Knowledge",
                            "title": f"Expand your understanding of '{topic}'",
                            "description": f"Your knowledge of '{topic}' could benefit from more comprehensive resources",
                            "action_items": [
                                f"Find a comprehensive book or course on '{topic}'",
                                f"Look for advanced articles or research papers about '{topic}'",
                                f"Seek practical applications or case studies in '{topic}'"
                            ],
                            "priority": "low",
                            "estimated_time": "4-8 hours"
                        })
                
                elif gap_category == "Foundational Knowledge Gaps":
                    # Suggest learning foundational concepts
                    domains = gap.get("domains", [])
                    for domain_info in domains[:2]:
                        domain = domain_info["domain"]
                        missing = domain_info["missing_concepts"]
                        opportunities.append({
                            "opportunity_type": "Foundation Building",
                            "title": f"Strengthen your {domain.lower()} foundation",
                            "description": f"Learn key foundational concepts in {domain.lower()}",
                            "action_items": [
                                f"Study the basics of: {', '.join(missing[:3])}",
                                f"Find introductory resources for {domain.lower()}",
                                f"Build connections between these foundations and your existing knowledge"
                            ],
                            "priority": "high",
                            "estimated_time": "6-12 hours"
                        })
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error generating learning opportunities: {e}")
            return []
    
    async def _suggest_new_topics(self, documents: List[Document], graph_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest new topics based on current interests and trends"""
        try:
            suggestions = []
            
            # Analyze current interests
            current_topics = set()
            for doc in documents:
                current_topics.update(doc.tags)
            
            # Topic expansion suggestions based on current interests
            topic_expansions = {
                "machine learning": ["deep learning", "neural networks", "computer vision", "natural language processing"],
                "programming": ["software architecture", "design patterns", "testing", "devops"],
                "business": ["entrepreneurship", "innovation", "leadership", "strategy"],
                "science": ["research methods", "data analysis", "scientific writing", "peer review"],
                "technology": ["artificial intelligence", "blockchain", "cloud computing", "cybersecurity"],
                "health": ["nutrition", "mental health", "exercise science", "medical research"],
                "education": ["learning science", "pedagogy", "educational technology", "assessment"]
            }
            
            # Find expansion opportunities
            for current_topic in current_topics:
                current_lower = current_topic.lower()
                for base_topic, expansions in topic_expansions.items():
                    if base_topic in current_lower or any(word in current_lower for word in base_topic.split()):
                        for expansion in expansions:
                            if expansion not in [t.lower() for t in current_topics]:
                                suggestions.append({
                                    "suggestion_type": "Topic Expansion",
                                    "suggested_topic": expansion.title(),
                                    "reason": f"Natural extension of your interest in '{current_topic}'",
                                    "relevance_score": 0.8,
                                    "learning_path": [
                                        f"Introduction to {expansion}",
                                        f"{expansion.title()} fundamentals",
                                        f"Advanced {expansion} concepts",
                                        f"Practical applications of {expansion}"
                                    ]
                                })
            
            # Remove duplicates and sort by relevance
            unique_suggestions = []
            seen_topics = set()
            
            for suggestion in suggestions:
                topic = suggestion["suggested_topic"].lower()
                if topic not in seen_topics:
                    seen_topics.add(topic)
                    unique_suggestions.append(suggestion)
            
            return unique_suggestions[:10]  # Return top 10 suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting new topics: {e}")
            return []
    
    async def _analyze_knowledge_depth(self, documents: List[Document], graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze depth of knowledge in different areas"""
        try:
            depth_analysis = {
                "topic_depth_scores": {},
                "overall_depth_rating": "",
                "deep_knowledge_areas": [],
                "shallow_knowledge_areas": [],
                "recommendations": []
            }
            
            # Analyze depth by topic
            topic_analysis = defaultdict(lambda: {"docs": [], "total_words": 0, "connections": 0})
            
            for doc in documents:
                for tag in doc.tags:
                    topic_analysis[tag]["docs"].append(doc)
                    topic_analysis[tag]["total_words"] += len(doc.content.split())
            
            # Calculate depth scores
            depth_scores = {}
            for topic, analysis in topic_analysis.items():
                doc_count = len(analysis["docs"])
                avg_words_per_doc = analysis["total_words"] / doc_count if doc_count > 0 else 0
                
                # Calculate depth score (0-100)
                depth_score = min(100, (doc_count * 20) + (avg_words_per_doc / 50))
                depth_scores[topic] = {
                    "score": round(depth_score, 1),
                    "document_count": doc_count,
                    "avg_document_length": round(avg_words_per_doc),
                    "total_content": analysis["total_words"]
                }
            
            depth_analysis["topic_depth_scores"] = depth_scores
            
            # Categorize knowledge areas
            deep_areas = [(topic, score) for topic, score in depth_scores.items() if score["score"] >= 70]
            shallow_areas = [(topic, score) for topic, score in depth_scores.items() if score["score"] <= 30]
            
            depth_analysis["deep_knowledge_areas"] = [
                {"topic": topic, "score": score["score"], "documents": score["document_count"]}
                for topic, score in sorted(deep_areas, key=lambda x: x[1]["score"], reverse=True)[:5]
            ]
            
            depth_analysis["shallow_knowledge_areas"] = [
                {"topic": topic, "score": score["score"], "documents": score["document_count"]}
                for topic, score in sorted(shallow_areas, key=lambda x: x[1]["score"])[:5]
            ]
            
            # Overall depth rating
            if depth_scores:
                avg_depth = np.mean([score["score"] for score in depth_scores.values()])
                if avg_depth >= 70:
                    depth_analysis["overall_depth_rating"] = "Deep and comprehensive knowledge base"
                elif avg_depth >= 50:
                    depth_analysis["overall_depth_rating"] = "Good depth with room for improvement"
                elif avg_depth >= 30:
                    depth_analysis["overall_depth_rating"] = "Moderate depth, consider focusing on key areas"
                else:
                    depth_analysis["overall_depth_rating"] = "Broad but shallow knowledge base"
            
            return depth_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing knowledge depth: {e}")
            return {}
    
    async def generate_learning_path(self, topic: str, current_level: str = "beginner", target_level: str = "advanced") -> Dict[str, Any]:
        """Generate a personalized learning path for a specific topic"""
        try:
            learning_path = {
                "topic": topic,
                "current_level": current_level,
                "target_level": target_level,
                "generated_at": datetime.utcnow().isoformat(),
                "estimated_duration": "",
                "learning_stages": [],
                "resources": [],
                "milestones": [],
                "prerequisites": []
            }
            
            # Define learning stages based on levels
            stages = {
                "beginner": {
                    "Foundation": [
                        f"Introduction to {topic}",
                        f"Basic concepts and terminology",
                        f"Historical context and importance",
                        f"Key principles and fundamentals"
                    ]
                },
                "intermediate": {
                    "Application": [
                        f"Practical applications of {topic}",
                        f"Common use cases and examples",
                        f"Tools and technologies",
                        f"Best practices and methodologies"
                    ]
                },
                "advanced": {
                    "Mastery": [
                        f"Advanced {topic} techniques",
                        f"Research and cutting-edge developments",
                        f"Problem-solving and innovation",
                        f"Teaching and mentoring others"
                    ]
                }
            }
            
            # Build learning stages
            level_order = ["beginner", "intermediate", "advanced"]
            start_idx = level_order.index(current_level)
            end_idx = level_order.index(target_level)
            
            for i in range(start_idx, end_idx + 1):
                level = level_order[i]
                for stage_name, activities in stages.get(level, {}).items():
                    learning_path["learning_stages"].append({
                        "stage": stage_name,
                        "level": level,
                        "activities": activities,
                        "estimated_time": f"{len(activities) * 2}-{len(activities) * 4} hours"
                    })
            
            # Estimate total duration
            total_activities = sum(len(stage["activities"]) for stage in learning_path["learning_stages"])
            learning_path["estimated_duration"] = f"{total_activities * 2}-{total_activities * 4} hours"
            
            # Generate milestones
            learning_path["milestones"] = [
                {
                    "milestone": f"Complete {stage['stage']} stage",
                    "description": f"Successfully understand and apply {stage['level']}-level {topic} concepts",
                    "assessment": f"Can explain key concepts and complete practical exercises"
                }
                for stage in learning_path["learning_stages"]
            ]
            
            return learning_path
            
        except Exception as e:
            logger.error(f"Error generating learning path: {e}")
            return {"error": str(e)}
    
    async def get_daily_insights(self, user_id: str = "default") -> Dict[str, Any]:
        """Generate daily insights and recommendations"""
        try:
            insights = {
                "date": datetime.utcnow().date().isoformat(),
                "user_id": user_id,
                "insights": [],
                "recommended_actions": [],
                "knowledge_highlight": None,
                "learning_streak": 0,
                "motivation": ""
            }
            
            # Get recent knowledge analysis
            knowledge_gaps = await self.analyze_knowledge_gaps(user_id)
            
            # Generate insights based on knowledge state
            if knowledge_gaps.get("knowledge_coverage"):
                coverage = knowledge_gaps["knowledge_coverage"]
                
                # Coverage insights
                if coverage.get("topic_distribution"):
                    top_topic = max(coverage["topic_distribution"].items(), key=lambda x: x[1]["count"])
                    insights["insights"].append({
                        "type": "knowledge_focus",
                        "title": "Your Knowledge Focus",
                        "description": f"Your strongest knowledge area is '{top_topic[0]}' with {top_topic[1]['count']} related documents.",
                        "icon": "📚"
                    })
                
                # Concept connectivity insight
                if coverage.get("concept_coverage"):
                    concept_coverage = coverage["concept_coverage"]
                    insights["insights"].append({
                        "type": "connectivity",
                        "title": "Knowledge Network",
                        "description": f"You have {concept_coverage.get('total_concepts', 0)} concepts with an average of {concept_coverage.get('average_connections', 0)} connections each.",
                        "icon": "🕸️"
                    })
            
            # Generate recommended actions
            if knowledge_gaps.get("learning_opportunities"):
                opportunities = knowledge_gaps["learning_opportunities"][:3]
                for opp in opportunities:
                    insights["recommended_actions"].append({
                        "action": opp.get("title", "Explore new topic"),
                        "description": opp.get("description", ""),
                        "priority": opp.get("priority", "medium"),
                        "estimated_time": opp.get("estimated_time", "Unknown")
                    })
            
            # Knowledge highlight
            documents = await self.vector_store.get_documents(limit=100)
            if documents:
                # Highlight most recent or interesting document
                recent_doc = max(documents, key=lambda x: x.uploaded_at or datetime.min)
                insights["knowledge_highlight"] = {
                    "title": recent_doc.title,
                    "summary": recent_doc.summary or "No summary available",
                    "tags": recent_doc.tags[:5],
                    "uploaded_at": recent_doc.uploaded_at.isoformat() if recent_doc.uploaded_at else None
                }
            
            # Motivational message
            insights["motivation"] = self._generate_motivational_message(knowledge_gaps)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating daily insights: {e}")
            return {"error": str(e), "date": datetime.utcnow().date().isoformat()}
    
    def _generate_motivational_message(self, knowledge_gaps: Dict[str, Any]) -> str:
        """Generate a motivational message based on knowledge state"""
        messages = [
            "Your knowledge network grows stronger with each connection you make!",
            "Every document you add brings new insights and discoveries.",
            "Knowledge is a treasure that grows when shared and explored.",
            "Your learning journey is unique and valuable - keep exploring!",
            "Each question you ask opens doors to new understanding.",
            "The connections between ideas often lead to the greatest breakthroughs.",
            "Your curiosity is the key to unlocking new knowledge domains.",
            "Every expert was once a beginner - embrace your learning journey!"
        ]
        
        # Customize based on knowledge state
        if knowledge_gaps.get("knowledge_coverage", {}).get("total_documents", 0) > 50:
            messages.extend([
                "You've built an impressive knowledge base - time to explore deeper connections!",
                "With your extensive knowledge collection, you're ready for advanced synthesis!",
                "Your knowledge repository shows dedication to continuous learning!"
            ])
        
        import random
        return random.choice(messages)
    
    def health_check(self) -> Dict[str, Any]:
        """Check AI learning agent health"""
        return {
            "status": "healthy" if self.classifier else "degraded",
            "ai_classifier_available": bool(self.classifier),
            "knowledge_graph_connected": bool(self.knowledge_graph),
            "vector_store_connected": bool(self.vector_store),
            "capabilities": [
                "Knowledge gap analysis",
                "Learning path generation",
                "Topic suggestions",
                "Daily insights",
                "Proactive recommendations"
            ]
        }