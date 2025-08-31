import logging
from typing import List, Union, Dict, Any, Optional, Tuple
import numpy as np
import torch
from PIL import Image
import asyncio

# Multimodal embedding imports
from sentence_transformers import SentenceTransformer
try:
    from transformers import CLIPProcessor, CLIPModel
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False
    logging.warning("CLIP not available for multimodal embeddings")

from models.schemas import Document, DocumentChunk

logger = logging.getLogger(__name__)

class MultimodalEmbedder:
    """Unified embedding service for text, image, and audio content"""
    
    def __init__(self):
        self.text_encoder = None
        self.clip_processor = None
        self.clip_model = None
        self.embedding_dim = 384  # Standard dimension for all embeddings
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize embedding models"""
        try:
            # Text encoder (same as used in document processor)
            self.text_encoder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            logger.info("Text encoder initialized")
            
            # CLIP for multimodal embeddings (text + image)
            if CLIP_AVAILABLE:
                self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
                self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
                
                # Move to GPU if available
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self.clip_model.to(device)
                logger.info(f"CLIP model initialized on {device}")
            
        except Exception as e:
            logger.error(f"Error initializing multimodal embedder: {e}")
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate text embedding"""
        try:
            if not self.text_encoder:
                return self._get_dummy_embedding()
            
            # Run embedding generation in thread pool
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                lambda: self.text_encoder.encode(text, convert_to_numpy=True)
            )
            
            return self._normalize_embedding(embedding.tolist())
            
        except Exception as e:
            logger.error(f"Error generating text embedding: {e}")
            return self._get_dummy_embedding()
    
    async def embed_image_description(self, image_description: str) -> List[float]:
        """Generate embedding for image description using CLIP text encoder"""
        try:
            if not CLIP_AVAILABLE or not self.clip_processor or not self.clip_model:
                # Fallback to text encoder
                return await self.embed_text(image_description)
            
            loop = asyncio.get_event_loop()
            
            def generate_clip_text_embedding():
                inputs = self.clip_processor(text=image_description, return_tensors="pt", padding=True)
                
                # Move to same device as model
                device = next(self.clip_model.parameters()).device
                inputs = {k: v.to(device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    text_features = self.clip_model.get_text_features(**inputs)
                    # Normalize embeddings
                    text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                
                return text_features.cpu().numpy()[0]
            
            embedding = await loop.run_in_executor(None, generate_clip_text_embedding)
            
            # Resize to standard dimension if necessary
            return self._resize_embedding(embedding.tolist(), self.embedding_dim)
            
        except Exception as e:
            logger.error(f"Error generating CLIP text embedding: {e}")
            return await self.embed_text(image_description)
    
    async def embed_image_file(self, image_path: str) -> List[float]:
        """Generate embedding for image file using CLIP image encoder"""
        try:
            if not CLIP_AVAILABLE or not self.clip_processor or not self.clip_model:
                logger.warning("CLIP not available for image embedding")
                return self._get_dummy_embedding()
            
            # Load image
            image = Image.open(image_path).convert('RGB')
            
            loop = asyncio.get_event_loop()
            
            def generate_clip_image_embedding():
                inputs = self.clip_processor(images=image, return_tensors="pt")
                
                # Move to same device as model
                device = next(self.clip_model.parameters()).device
                inputs = {k: v.to(device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    image_features = self.clip_model.get_image_features(**inputs)
                    # Normalize embeddings
                    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                
                return image_features.cpu().numpy()[0]
            
            embedding = await loop.run_in_executor(None, generate_clip_image_embedding)
            
            # Resize to standard dimension if necessary
            return self._resize_embedding(embedding.tolist(), self.embedding_dim)
            
        except Exception as e:
            logger.error(f"Error generating image embedding: {e}")
            return self._get_dummy_embedding()
    
    async def embed_multimodal_content(self, content: str, content_type: str = "text", file_path: Optional[str] = None) -> List[float]:
        """Generate unified embedding for multimodal content"""
        try:
            if content_type == "text":
                return await self.embed_text(content)
            
            elif content_type == "image":
                if file_path:
                    # Use actual image file for embedding
                    image_embedding = await self.embed_image_file(file_path)
                    # Also embed the text description
                    text_embedding = await self.embed_image_description(content)
                    # Combine embeddings (weighted average)
                    return self._combine_embeddings([image_embedding, text_embedding], [0.7, 0.3])
                else:
                    # Only text description available
                    return await self.embed_image_description(content)
            
            elif content_type == "audio":
                # For audio, we embed the transcribed text
                # In the future, we could use audio-specific models
                return await self.embed_text(content)
            
            else:
                logger.warning(f"Unknown content type: {content_type}, using text embedding")
                return await self.embed_text(content)
                
        except Exception as e:
            logger.error(f"Error generating multimodal embedding: {e}")
            return self._get_dummy_embedding()
    
    async def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Compute cosine similarity between two embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Compute cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error computing similarity: {e}")
            return 0.0
    
    async def find_similar_content(self, 
                                   query_embedding: List[float], 
                                   candidate_embeddings: List[Tuple[str, List[float]]], 
                                   top_k: int = 10) -> List[Tuple[str, float]]:
        """Find most similar content based on embeddings"""
        try:
            similarities = []
            
            for content_id, embedding in candidate_embeddings:
                similarity = await self.compute_similarity(query_embedding, embedding)
                similarities.append((content_id, similarity))
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Error finding similar content: {e}")
            return []
    
    def _normalize_embedding(self, embedding: List[float]) -> List[float]:
        """Normalize embedding to unit length"""
        try:
            vec = np.array(embedding)
            norm = np.linalg.norm(vec)
            if norm == 0:
                return embedding
            return (vec / norm).tolist()
        except:
            return embedding
    
    def _resize_embedding(self, embedding: List[float], target_dim: int) -> List[float]:
        """Resize embedding to target dimension"""
        try:
            current_dim = len(embedding)
            if current_dim == target_dim:
                return embedding
            
            vec = np.array(embedding)
            
            if current_dim > target_dim:
                # Truncate
                return vec[:target_dim].tolist()
            else:
                # Pad with zeros
                padded = np.zeros(target_dim)
                padded[:current_dim] = vec
                return padded.tolist()
                
        except Exception as e:
            logger.error(f"Error resizing embedding: {e}")
            return self._get_dummy_embedding()
    
    def _combine_embeddings(self, embeddings: List[List[float]], weights: List[float]) -> List[float]:
        """Combine multiple embeddings with weights"""
        try:
            if len(embeddings) != len(weights):
                logger.error("Mismatch between embeddings and weights")
                return embeddings[0] if embeddings else self._get_dummy_embedding()
            
            # Normalize weights
            total_weight = sum(weights)
            if total_weight == 0:
                return embeddings[0] if embeddings else self._get_dummy_embedding()
            
            weights = [w / total_weight for w in weights]
            
            # Weighted combination
            combined = np.zeros(len(embeddings[0]))
            for embedding, weight in zip(embeddings, weights):
                combined += np.array(embedding) * weight
            
            return self._normalize_embedding(combined.tolist())
            
        except Exception as e:
            logger.error(f"Error combining embeddings: {e}")
            return embeddings[0] if embeddings else self._get_dummy_embedding()
    
    def _get_dummy_embedding(self) -> List[float]:
        """Generate dummy embedding for fallback"""
        return [0.0] * self.embedding_dim
    
    async def process_document_chunks(self, document: Document, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Process document chunks and add multimodal embeddings"""
        try:
            # Determine content type from document
            content_type = self._get_content_type(document)
            
            for chunk in chunks:
                if not chunk.embedding:  # Only process if embedding not already present
                    embedding = await self.embed_multimodal_content(
                        content=chunk.content,
                        content_type=content_type,
                        file_path=document.file_path if content_type == "image" else None
                    )
                    chunk.embedding = embedding
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing document chunks: {e}")
            return chunks
    
    def _get_content_type(self, document: Document) -> str:
        """Determine content type from document"""
        if document.file_type in ['jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff']:
            return "image"
        elif document.file_type in ['mp3', 'wav', 'm4a', 'flac', 'ogg', 'aac']:
            return "audio"
        else:
            return "text"
    
    def health_check(self) -> Dict[str, Any]:
        """Check multimodal embedder health"""
        return {
            "status": "healthy" if self.text_encoder else "degraded",
            "text_encoder_available": bool(self.text_encoder),
            "clip_available": CLIP_AVAILABLE and bool(self.clip_model),
            "embedding_dimension": self.embedding_dim,
            "device": "cuda" if torch.cuda.is_available() else "cpu"
        }