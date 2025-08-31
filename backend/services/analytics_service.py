import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json
import numpy as np
from pathlib import Path

# ML imports for predictive analytics
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import LatentDirichletAllocation
import pandas as pd

from services.vector_store import VectorStore
from services.knowledge_graph import KnowledgeGraph
from models.schemas import Document

logger = logging.getLogger(__name__)

class AdvancedAnalyticsService:
    """Service for advanced analytics, trends, and predictive insights"""
    
    def __init__(self, vector_store: VectorStore, knowledge_graph: KnowledgeGraph):
        self.vector_store = vector_store
        self.knowledge_graph = knowledge_graph
        self.analytics_storage = "analytics_data"
        self.vectorizer = None
        self.topic_model = None
        Path(self.analytics_storage).mkdir(exist_ok=True)
        self._initialize_ml_models()
    
    def _initialize_ml_models(self):
        """Initialize ML models for analytics"""
        try:
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            self.topic_model = LatentDirichletAllocation(
                n_components=10,
                random_state=42,
                max_iter=20
            )
            logger.info("Analytics ML models initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing ML models: {e}")
    
    async def analyze_knowledge_evolution(self, user_id: str = "default", days_back: int = 90) -> Dict[str, Any]:
        """Analyze how knowledge has evolved over time"""
        try:
            documents = await self.vector_store.get_documents(limit=1000)
            
            if not documents:
                return {"error": "No documents found for analysis"}
            
            evolution_analysis = {
                "user_id": user_id,
                "analysis_period": f"{days_back} days",
                "analyzed_at": datetime.utcnow().isoformat(),
                "timeline_analysis": {},
                "topic_evolution": {},
                "knowledge_growth": {},
                "trend_predictions": {}
            }
            
            # Timeline analysis
            timeline = await self._analyze_timeline(documents, days_back)
            evolution_analysis["timeline_analysis"] = timeline
            
            # Topic evolution
            topic_evolution = await self._analyze_topic_evolution(documents, days_back)
            evolution_analysis["topic_evolution"] = topic_evolution
            
            # Knowledge growth metrics
            growth_metrics = await self._calculate_growth_metrics(documents, days_back)
            evolution_analysis["knowledge_growth"] = growth_metrics
            
            # Trend predictions
            predictions = await self._predict_trends(documents)
            evolution_analysis["trend_predictions"] = predictions
            
            # Save analysis for historical comparison
            await self._save_evolution_snapshot(evolution_analysis)
            
            return evolution_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing knowledge evolution: {e}")
            return {"error": str(e)}
    
    async def _analyze_timeline(self, documents: List[Document], days_back: int) -> Dict[str, Any]:
        """Analyze document upload timeline"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Group documents by time periods
            daily_counts = defaultdict(int)
            weekly_counts = defaultdict(int)
            monthly_counts = defaultdict(int)
            topic_timeline = defaultdict(lambda: defaultdict(int))
            
            recent_docs = []
            for doc in documents:
                if doc.uploaded_at and doc.uploaded_at >= cutoff_date:
                    recent_docs.append(doc)
                    
                    # Daily counts
                    day_key = doc.uploaded_at.date().isoformat()
                    daily_counts[day_key] += 1
                    
                    # Weekly counts (ISO week)
                    week_key = f"{doc.uploaded_at.year}-W{doc.uploaded_at.isocalendar()[1]}"
                    weekly_counts[week_key] += 1
                    
                    # Monthly counts
                    month_key = f"{doc.uploaded_at.year}-{doc.uploaded_at.month:02d}"
                    monthly_counts[month_key] += 1
                    
                    # Topic timeline
                    for tag in doc.tags:
                        topic_timeline[tag][day_key] += 1
            
            # Calculate velocity and acceleration
            daily_values = list(daily_counts.values())
            velocity = np.mean(daily_values) if daily_values else 0
            acceleration = np.std(daily_values) if daily_values else 0
            
            return {
                "total_documents_in_period": len(recent_docs),
                "daily_upload_velocity": round(velocity, 2),
                "upload_consistency": round(100 - (acceleration / max(velocity, 1)) * 100, 1),
                "daily_distribution": dict(daily_counts),
                "weekly_distribution": dict(weekly_counts),
                "monthly_distribution": dict(monthly_counts),
                "most_active_day": max(daily_counts.items(), key=lambda x: x[1])[0] if daily_counts else None,
                "topic_timeline": dict(topic_timeline),
                "peak_activity_periods": self._identify_peak_periods(daily_counts)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing timeline: {e}")
            return {}
    
    def _identify_peak_periods(self, daily_counts: dict) -> List[Dict[str, Any]]:
        """Identify periods of high activity"""
        if not daily_counts:
            return []
        
        values = list(daily_counts.values())
        if len(values) < 3:
            return []
        
        threshold = np.mean(values) + np.std(values)
        peaks = []
        
        dates = sorted(daily_counts.keys())
        for date in dates:
            if daily_counts[date] > threshold:
                peaks.append({
                    "date": date,
                    "document_count": daily_counts[date],
                    "above_average": round(daily_counts[date] / np.mean(values), 2)
                })
        
        return peaks[:10]  # Return top 10 peaks
    
    async def _analyze_topic_evolution(self, documents: List[Document], days_back: int) -> Dict[str, Any]:
        """Analyze how topics have evolved over time"""
        try:
            if not documents:
                return {}
            
            # Group documents by time periods
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            periods = {
                "early": cutoff_date,
                "middle": cutoff_date + timedelta(days=days_back//3),
                "recent": cutoff_date + timedelta(days=2*days_back//3)
            }
            
            period_topics = {
                "early": defaultdict(int),
                "middle": defaultdict(int), 
                "recent": defaultdict(int)
            }
            
            for doc in documents:
                if not doc.uploaded_at:
                    continue
                    
                period = "recent"
                if doc.uploaded_at < periods["middle"]:
                    period = "early"
                elif doc.uploaded_at < periods["recent"]:
                    period = "middle"
                
                for tag in doc.tags:
                    period_topics[period][tag] += 1
            
            # Analyze topic trends
            trending_up = []
            trending_down = []
            new_topics = []
            
            all_topics = set()
            for period_data in period_topics.values():
                all_topics.update(period_data.keys())
            
            for topic in all_topics:
                early_count = period_topics["early"][topic]
                middle_count = period_topics["middle"][topic]
                recent_count = period_topics["recent"][topic]
                
                # Calculate trend
                if early_count == 0 and recent_count > 0:
                    new_topics.append({
                        "topic": topic,
                        "recent_mentions": recent_count,
                        "growth_type": "new"
                    })
                elif early_count > 0 and recent_count > early_count:
                    growth_rate = (recent_count - early_count) / early_count * 100
                    trending_up.append({
                        "topic": topic,
                        "growth_rate": round(growth_rate, 1),
                        "early_count": early_count,
                        "recent_count": recent_count
                    })
                elif early_count > 0 and recent_count < early_count:
                    decline_rate = (early_count - recent_count) / early_count * 100
                    trending_down.append({
                        "topic": topic,
                        "decline_rate": round(decline_rate, 1),
                        "early_count": early_count,
                        "recent_count": recent_count
                    })
            
            # Sort by significance
            trending_up.sort(key=lambda x: x["growth_rate"], reverse=True)
            trending_down.sort(key=lambda x: x["decline_rate"], reverse=True)
            new_topics.sort(key=lambda x: x["recent_mentions"], reverse=True)
            
            return {
                "analysis_periods": {
                    "early": periods["early"].isoformat(),
                    "middle": periods["middle"].isoformat(),
                    "recent": periods["recent"].isoformat()
                },
                "trending_up": trending_up[:10],
                "trending_down": trending_down[:10],
                "new_topics": new_topics[:10],
                "period_topic_counts": {k: dict(v) for k, v in period_topics.items()},
                "topic_diversity_trend": [
                    len(period_topics["early"]),
                    len(period_topics["middle"]),
                    len(period_topics["recent"])
                ]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing topic evolution: {e}")
            return {}
    
    async def _calculate_growth_metrics(self, documents: List[Document], days_back: int) -> Dict[str, Any]:
        """Calculate various knowledge growth metrics"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            recent_docs = [doc for doc in documents if doc.uploaded_at and doc.uploaded_at >= cutoff_date]
            
            if not recent_docs:
                return {}
            
            # Sort by upload date
            recent_docs.sort(key=lambda x: x.uploaded_at or datetime.min)
            
            # Calculate metrics
            total_content_words = sum(len(doc.content.split()) for doc in recent_docs)
            total_unique_tags = len(set(tag for doc in recent_docs for tag in doc.tags))
            
            # Knowledge velocity (documents per day)
            days_with_activity = len(set(doc.uploaded_at.date() for doc in recent_docs if doc.uploaded_at))
            doc_velocity = len(recent_docs) / max(days_with_activity, 1)
            
            # Content depth (average words per document)
            avg_content_depth = total_content_words / len(recent_docs)
            
            # Topic diversity (unique tags per document)
            topic_diversity = total_unique_tags / len(recent_docs)
            
            # Calculate growth trajectory
            mid_point = len(recent_docs) // 2
            first_half = recent_docs[:mid_point]
            second_half = recent_docs[mid_point:]
            
            growth_trajectory = "stable"
            if len(second_half) > len(first_half) * 1.2:
                growth_trajectory = "accelerating"
            elif len(second_half) < len(first_half) * 0.8:
                growth_trajectory = "decelerating"
            
            return {
                "total_documents": len(recent_docs),
                "total_content_words": total_content_words,
                "unique_topics": total_unique_tags,
                "document_velocity": round(doc_velocity, 2),
                "content_depth": round(avg_content_depth, 1),
                "topic_diversity": round(topic_diversity, 2),
                "growth_trajectory": growth_trajectory,
                "learning_intensity": self._calculate_learning_intensity(recent_docs),
                "knowledge_breadth_vs_depth": self._analyze_breadth_vs_depth(recent_docs)
            }
            
        except Exception as e:
            logger.error(f"Error calculating growth metrics: {e}")
            return {}
    
    def _calculate_learning_intensity(self, documents: List[Document]) -> Dict[str, Any]:
        """Calculate learning intensity metrics"""
        if not documents:
            return {}
        
        # Group by week
        weekly_docs = defaultdict(list)
        for doc in documents:
            if doc.uploaded_at:
                week = doc.uploaded_at.isocalendar()[:2]  # (year, week)
                weekly_docs[week].append(doc)
        
        weekly_intensities = []
        for week_docs in weekly_docs.values():
            intensity = len(week_docs) + sum(len(doc.tags) for doc in week_docs) / 10
            weekly_intensities.append(intensity)
        
        avg_intensity = np.mean(weekly_intensities) if weekly_intensities else 0
        
        return {
            "average_weekly_intensity": round(avg_intensity, 2),
            "peak_intensity": round(max(weekly_intensities), 2) if weekly_intensities else 0,
            "intensity_consistency": round(100 - (np.std(weekly_intensities) / max(avg_intensity, 1)) * 100, 1),
            "high_intensity_weeks": len([i for i in weekly_intensities if i > avg_intensity * 1.5])
        }
    
    def _analyze_breadth_vs_depth(self, documents: List[Document]) -> Dict[str, Any]:
        """Analyze whether learning is broad (many topics) vs deep (few topics, much content)"""
        if not documents:
            return {}
        
        topic_doc_counts = Counter()
        topic_content_lengths = defaultdict(int)
        
        for doc in documents:
            content_length = len(doc.content.split())
            for tag in doc.tags:
                topic_doc_counts[tag] += 1
                topic_content_lengths[tag] += content_length
        
        breadth_score = len(topic_doc_counts)  # Number of different topics
        depth_score = np.mean(list(topic_content_lengths.values())) if topic_content_lengths else 0
        
        # Normalize scores
        breadth_normalized = min(breadth_score / 20, 1.0) * 100  # Cap at 20 topics
        depth_normalized = min(depth_score / 10000, 1.0) * 100  # Cap at 10k words per topic
        
        learning_style = "balanced"
        if breadth_normalized > depth_normalized * 1.5:
            learning_style = "breadth-focused"
        elif depth_normalized > breadth_normalized * 1.5:
            learning_style = "depth-focused"
        
        return {
            "breadth_score": round(breadth_normalized, 1),
            "depth_score": round(depth_normalized, 1),
            "learning_style": learning_style,
            "topic_specializations": [
                {
                    "topic": topic,
                    "document_count": count,
                    "total_content": topic_content_lengths[topic]
                }
                for topic, count in topic_doc_counts.most_common(5)
            ]
        }
    
    async def _predict_trends(self, documents: List[Document]) -> Dict[str, Any]:
        """Predict future trends based on current patterns"""
        try:
            if len(documents) < 10:
                return {"error": "Insufficient data for trend prediction"}
            
            predictions = {
                "next_month_projections": {},
                "emerging_topics": [],
                "declining_interests": [],
                "recommended_focus_areas": []
            }
            
            # Analyze recent upload patterns
            recent_30_days = datetime.utcnow() - timedelta(days=30)
            recent_docs = [doc for doc in documents if doc.uploaded_at and doc.uploaded_at >= recent_30_days]
            
            if recent_docs:
                # Project next month's activity
                current_velocity = len(recent_docs) / 30
                predictions["next_month_projections"] = {
                    "estimated_documents": int(current_velocity * 30),
                    "confidence": "high" if len(recent_docs) > 10 else "low",
                    "based_on_last_30_days": len(recent_docs)
                }
                
                # Identify emerging patterns using topic modeling
                if self.vectorizer and self.topic_model and len(recent_docs) > 5:
                    emerging_topics = await self._identify_emerging_topics(recent_docs)
                    predictions["emerging_topics"] = emerging_topics
            
            # Analyze declining interests
            declining = await self._identify_declining_interests(documents)
            predictions["declining_interests"] = declining
            
            # Generate recommendations
            recommendations = await self._generate_focus_recommendations(documents)
            predictions["recommended_focus_areas"] = recommendations
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error predicting trends: {e}")
            return {"error": str(e)}
    
    async def _identify_emerging_topics(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Use topic modeling to identify emerging topics"""
        try:
            if not documents:
                return []
            
            # Prepare text data
            texts = [doc.content[:1000] for doc in documents]  # Limit length for performance
            
            # Fit TF-IDF vectorizer
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            
            # Fit topic model
            self.topic_model.fit(tfidf_matrix)
            
            # Extract topics
            feature_names = self.vectorizer.get_feature_names_out()
            topics = []
            
            for topic_idx, topic in enumerate(self.topic_model.components_):
                top_words_idx = topic.argsort()[-10:][::-1]
                top_words = [feature_names[i] for i in top_words_idx]
                top_scores = [topic[i] for i in top_words_idx]
                
                topics.append({
                    "topic_id": f"emerging_topic_{topic_idx}",
                    "keywords": top_words[:5],
                    "confidence": round(float(np.mean(top_scores)), 3),
                    "description": f"Topic characterized by: {', '.join(top_words[:3])}"
                })
            
            # Sort by confidence and return top topics
            topics.sort(key=lambda x: x["confidence"], reverse=True)
            return topics[:5]
            
        except Exception as e:
            logger.error(f"Error identifying emerging topics: {e}")
            return []
    
    async def _identify_declining_interests(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Identify topics that are declining in interest"""
        try:
            if len(documents) < 20:
                return []
            
            # Split documents into old and recent
            mid_point = len(documents) // 2
            old_docs = documents[:mid_point]
            recent_docs = documents[mid_point:]
            
            old_topics = Counter()
            recent_topics = Counter()
            
            for doc in old_docs:
                for tag in doc.tags:
                    old_topics[tag] += 1
            
            for doc in recent_docs:
                for tag in doc.tags:
                    recent_topics[tag] += 1
            
            declining = []
            for topic, old_count in old_topics.items():
                recent_count = recent_topics.get(topic, 0)
                if old_count > 2 and recent_count < old_count * 0.5:  # Significant decline
                    decline_rate = (old_count - recent_count) / old_count * 100
                    declining.append({
                        "topic": topic,
                        "decline_rate": round(decline_rate, 1),
                        "old_mentions": old_count,
                        "recent_mentions": recent_count,
                        "status": "declining"
                    })
            
            declining.sort(key=lambda x: x["decline_rate"], reverse=True)
            return declining[:5]
            
        except Exception as e:
            logger.error(f"Error identifying declining interests: {e}")
            return []
    
    async def _generate_focus_recommendations(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Generate recommendations for areas to focus on"""
        try:
            recommendations = []
            
            if not documents:
                return recommendations
            
            # Analyze current knowledge distribution
            topic_counts = Counter()
            topic_content = defaultdict(int)
            
            for doc in documents:
                content_length = len(doc.content.split())
                for tag in doc.tags:
                    topic_counts[tag] += 1
                    topic_content[tag] += content_length
            
            # Identify underexplored topics with potential
            total_topics = len(topic_counts)
            if total_topics > 5:
                # Topics with few documents but moderate content
                for topic, count in topic_counts.items():
                    if 2 <= count <= 4:  # Moderate interest
                        avg_content = topic_content[topic] / count
                        if avg_content > 500:  # Substantial content
                            recommendations.append({
                                "type": "deepen_knowledge",
                                "topic": topic,
                                "reason": f"You have {count} documents on {topic} with good depth. Consider expanding this area.",
                                "priority": "medium",
                                "action": "Find more comprehensive resources"
                            })
                
                # Identify topics that could benefit from connections
                graph_data = await self.knowledge_graph.get_knowledge_graph_data(limit=100)
                if graph_data.get("nodes"):
                    isolated_topics = []
                    edge_counts = defaultdict(int)
                    
                    for edge in graph_data.get("edges", []):
                        edge_counts[edge["source"]] += 1
                        edge_counts[edge["target"]] += 1
                    
                    for node in graph_data["nodes"]:
                        connections = edge_counts.get(node["id"], 0)
                        if connections <= 1 and node.get("size", 0) > 20:
                            isolated_topics.append(node["label"])
                    
                    for topic in isolated_topics[:3]:
                        recommendations.append({
                            "type": "connect_knowledge",
                            "topic": topic,
                            "reason": f"{topic} is well-developed but lacks connections to other areas.",
                            "priority": "high",
                            "action": "Explore interdisciplinary connections"
                        })
            
            return recommendations[:5]
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    async def _save_evolution_snapshot(self, analysis: Dict[str, Any]):
        """Save evolution analysis for historical comparison"""
        try:
            snapshot_file = f"{self.analytics_storage}/evolution_snapshot_{datetime.utcnow().date()}.json"
            with open(snapshot_file, 'w') as f:
                json.dump(analysis, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving evolution snapshot: {e}")
    
    async def generate_impact_analysis(self, user_id: str = "default") -> Dict[str, Any]:
        """Analyze the impact and influence of different concepts"""
        try:
            documents = await self.vector_store.get_documents(limit=1000)
            graph_data = await self.knowledge_graph.get_knowledge_graph_data(limit=200)
            
            impact_analysis = {
                "user_id": user_id,
                "analyzed_at": datetime.utcnow().isoformat(),
                "concept_influence": {},
                "knowledge_hubs": [],
                "citation_network": {},
                "impact_metrics": {}
            }
            
            if not graph_data.get("nodes"):
                return {"error": "No knowledge graph data available"}
            
            # Calculate concept influence
            nodes = graph_data["nodes"]
            edges = graph_data["edges"]
            
            # Calculate centrality measures
            centrality_scores = self._calculate_centrality(nodes, edges)
            impact_analysis["concept_influence"] = centrality_scores
            
            # Identify knowledge hubs
            hubs = sorted(centrality_scores.items(), key=lambda x: x[1], reverse=True)[:10]
            impact_analysis["knowledge_hubs"] = [
                {"concept": concept, "influence_score": round(score, 3)}
                for concept, score in hubs
            ]
            
            # Calculate impact metrics
            impact_metrics = {
                "total_concepts": len(nodes),
                "total_connections": len(edges),
                "network_density": round(len(edges) / (len(nodes) * (len(nodes) - 1)) * 2, 4) if len(nodes) > 1 else 0,
                "average_connections": round(len(edges) * 2 / len(nodes), 2) if nodes else 0,
                "knowledge_clustering": self._calculate_clustering_coefficient(nodes, edges)
            }
            impact_analysis["impact_metrics"] = impact_metrics
            
            return impact_analysis
            
        except Exception as e:
            logger.error(f"Error generating impact analysis: {e}")
            return {"error": str(e)}
    
    def _calculate_centrality(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, float]:
        """Calculate centrality measures for nodes"""
        try:
            # Build adjacency list
            adjacency = defaultdict(set)
            for edge in edges:
                source = edge["source"]
                target = edge["target"]
                adjacency[source].add(target)
                adjacency[target].add(source)
            
            centrality_scores = {}
            total_nodes = len(nodes)
            
            for node in nodes:
                node_id = node["id"]
                # Degree centrality (normalized)
                degree = len(adjacency[node_id])
                degree_centrality = degree / (total_nodes - 1) if total_nodes > 1 else 0
                
                # Combine with node size (importance)
                size_weight = node.get("size", 0) / 100  # Normalize size
                
                # Combined influence score
                influence = (degree_centrality * 0.7) + (size_weight * 0.3)
                centrality_scores[node_id] = influence
            
            return centrality_scores
            
        except Exception as e:
            logger.error(f"Error calculating centrality: {e}")
            return {}
    
    def _calculate_clustering_coefficient(self, nodes: List[Dict], edges: List[Dict]) -> float:
        """Calculate clustering coefficient of the knowledge graph"""
        try:
            if len(nodes) < 3:
                return 0.0
            
            # Build adjacency list
            adjacency = defaultdict(set)
            for edge in edges:
                source = edge["source"]
                target = edge["target"]
                adjacency[source].add(target)
                adjacency[target].add(source)
            
            total_clustering = 0
            nodes_with_edges = 0
            
            for node in nodes:
                node_id = node["id"]
                neighbors = list(adjacency[node_id])
                
                if len(neighbors) < 2:
                    continue
                
                nodes_with_edges += 1
                
                # Count triangles
                triangles = 0
                possible_triangles = len(neighbors) * (len(neighbors) - 1) / 2
                
                for i, neighbor1 in enumerate(neighbors):
                    for neighbor2 in neighbors[i+1:]:
                        if neighbor2 in adjacency[neighbor1]:
                            triangles += 1
                
                local_clustering = triangles / possible_triangles if possible_triangles > 0 else 0
                total_clustering += local_clustering
            
            return round(total_clustering / nodes_with_edges, 4) if nodes_with_edges > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating clustering coefficient: {e}")
            return 0.0
    
    async def get_analytics_dashboard_data(self, user_id: str = "default") -> Dict[str, Any]:
        """Get comprehensive analytics data for dashboard"""
        try:
            dashboard_data = {
                "user_id": user_id,
                "generated_at": datetime.utcnow().isoformat(),
                "overview_metrics": {},
                "recent_trends": {},
                "knowledge_health": {},
                "recommendations": []
            }
            
            # Get recent evolution analysis
            evolution = await self.analyze_knowledge_evolution(user_id, days_back=30)
            if "error" not in evolution:
                dashboard_data["recent_trends"] = {
                    "upload_velocity": evolution.get("timeline_analysis", {}).get("daily_upload_velocity", 0),
                    "trending_topics": evolution.get("topic_evolution", {}).get("trending_up", [])[:5],
                    "new_topics": evolution.get("topic_evolution", {}).get("new_topics", [])[:3]
                }
            
            # Get impact analysis
            impact = await self.generate_impact_analysis(user_id)
            if "error" not in impact:
                dashboard_data["knowledge_health"] = {
                    "network_density": impact.get("impact_metrics", {}).get("network_density", 0),
                    "knowledge_hubs": impact.get("knowledge_hubs", [])[:5],
                    "clustering": impact.get("impact_metrics", {}).get("knowledge_clustering", 0)
                }
            
            # Generate actionable recommendations
            recommendations = []
            if "error" not in evolution:
                growth = evolution.get("knowledge_growth", {})
                if growth.get("learning_intensity", {}).get("intensity_consistency", 100) < 50:
                    recommendations.append({
                        "type": "consistency",
                        "title": "Improve Learning Consistency", 
                        "description": "Your learning pattern shows inconsistency. Try to maintain regular knowledge intake.",
                        "priority": "medium"
                    })
                
                if growth.get("topic_diversity", 0) < 2:
                    recommendations.append({
                        "type": "diversity",
                        "title": "Expand Topic Diversity",
                        "description": "Consider exploring new topics to broaden your knowledge base.",
                        "priority": "low"
                    })
            
            dashboard_data["recommendations"] = recommendations
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating dashboard data: {e}")
            return {"error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Check analytics service health"""
        return {
            "status": "healthy",
            "ml_models_initialized": bool(self.vectorizer and self.topic_model),
            "storage_accessible": Path(self.analytics_storage).exists(),
            "capabilities": [
                "Knowledge evolution analysis",
                "Trend prediction",
                "Impact analysis",
                "Learning pattern recognition",
                "Predictive analytics"
            ]
        }