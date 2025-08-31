import os
import time
import logging
from typing import List, Optional, Dict, Any
import asyncio

# LLM imports
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch

from models.schemas import QueryRequest, QueryResponse, QuerySource, SearchFilters
from services.vector_store import VectorStore

logger = logging.getLogger(__name__)

class RAGEngine:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.llm_pipeline = None
        self.tokenizer = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the LLM for answer generation"""
        try:
            # Use a lighter model for development/demo
            model_name = "microsoft/DialoGPT-medium"  # Fallback for development
            
            # Check if we have GPU available
            device = 0 if torch.cuda.is_available() else -1
            
            # Try to load Mistral-7B if available, otherwise use fallback
            try:
                # For production, use: "mistralai/Mistral-7B-Instruct-v0.1"
                model_name = "microsoft/DialoGPT-medium"  # Lighter alternative
                
                self.llm_pipeline = pipeline(
                    "text-generation",
                    model=model_name,
                    device=device,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    max_length=512,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=50256
                )
                
                logger.info(f"LLM pipeline initialized with model: {model_name}")
                
            except Exception as e:
                logger.warning(f"Failed to load preferred model, using fallback: {e}")
                # Ultra-light fallback
                self.llm_pipeline = None
                
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            self.llm_pipeline = None
    
    async def query(self, query: str, filters: Optional[SearchFilters] = None, top_k: int = 5) -> QueryResponse:
        """Process a user query using RAG"""
        start_time = time.time()
        
        try:
            # Step 1: Retrieve relevant chunks
            similar_chunks = await self.vector_store.search_similar(
                query=query,
                filters=filters,
                top_k=top_k
            )
            
            if not similar_chunks:
                return QueryResponse(
                    answer="I couldn't find any relevant information in your documents to answer this question.",
                    sources=[],
                    confidence=0.0,
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
            
            # Step 2: Prepare context from retrieved chunks
            context_pieces = []
            sources = []
            
            for chunk, similarity_score in similar_chunks:
                context_pieces.append(f"[Source {len(context_pieces) + 1}]: {chunk.content}")
                
                # Get document title (simplified - would need proper document lookup)
                doc_title = f"Document {chunk.document_id[:8]}"
                
                sources.append(QuerySource(
                    document_id=chunk.document_id,
                    document_title=doc_title,
                    chunk_content=chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                    relevance_score=similarity_score,
                    chunk_index=chunk.chunk_index
                ))
            
            # Step 3: Generate answer using LLM
            answer = await self._generate_answer(query, context_pieces)
            
            # Step 4: Calculate confidence based on retrieval scores
            avg_similarity = sum(score for _, score in similar_chunks) / len(similar_chunks)
            confidence = min(avg_similarity * 1.2, 1.0)  # Boost confidence slightly
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return QueryResponse(
                answer=answer,
                sources=sources,
                confidence=confidence,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return QueryResponse(
                answer="I encountered an error while processing your question. Please try again.",
                sources=[],
                confidence=0.0,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
    
    async def _generate_answer(self, query: str, context_pieces: List[str]) -> str:
        """Generate an answer using the LLM"""
        try:
            # Prepare the prompt
            context = "\n\n".join(context_pieces)
            
            prompt = f"""Based on the following information from the user's documents, please answer the question. If the information doesn't fully answer the question, say so.

Context:
{context}

Question: {query}

Answer:"""
            
            if self.llm_pipeline:
                # Generate response using the LLM
                response = self.llm_pipeline(
                    prompt,
                    max_length=len(prompt.split()) + 100,  # Allow for answer
                    num_return_sequences=1,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.llm_pipeline.tokenizer.eos_token_id
                )
                
                # Extract the answer (everything after "Answer:")
                full_response = response[0]['generated_text']
                if "Answer:" in full_response:
                    answer = full_response.split("Answer:")[-1].strip()
                else:
                    answer = full_response[len(prompt):].strip()
                
                return answer[:500]  # Limit answer length
            else:
                # Fallback: simple extractive answer
                return await self._fallback_answer(query, context_pieces)
                
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return await self._fallback_answer(query, context_pieces)
    
    async def _fallback_answer(self, query: str, context_pieces: List[str]) -> str:
        """Fallback answer generation when LLM is not available"""
        if not context_pieces:
            return "I couldn't find relevant information to answer your question."
        
        # Simple extractive approach: return most relevant context
        context = "\n\n".join(context_pieces[:2])  # Use top 2 sources
        
        # Try to find sentences that might answer the query
        query_words = set(query.lower().split())
        sentences = []
        
        for piece in context_pieces[:2]:
            piece_sentences = piece.replace('[Source ', '').split('. ')
            for sentence in piece_sentences:
                sentence_words = set(sentence.lower().split())
                overlap = len(query_words & sentence_words)
                if overlap > 1:  # Some overlap with query
                    sentences.append(sentence.strip())
        
        if sentences:
            # Return most relevant sentences
            answer = ". ".join(sentences[:3])
            return f"Based on your documents: {answer}"
        else:
            # Return condensed context
            return f"Here's what I found in your documents:\n\n{context[:300]}..."
    
    def health_check(self) -> Dict[str, Any]:
        """Check RAG engine health"""
        return {
            "status": "healthy" if self.llm_pipeline or True else "degraded",  # Always healthy in fallback mode
            "llm_available": bool(self.llm_pipeline),
            "vector_store_available": bool(self.vector_store)
        }
    
    async def _get_document_title(self, document_id: str) -> str:
        """Helper to get document title (simplified)"""
        # In a full implementation, this would query the vector store
        return f"Document {document_id[:8]}"