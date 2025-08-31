import os
import uuid
import logging
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import tempfile
import asyncio
from datetime import datetime

# Image processing imports
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration, BlipForQuestionAnswering

# OCR imports (for text extraction from images)
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logging.warning("Tesseract OCR not available. Text extraction from images will be limited.")

from models.schemas import Document, DocumentChunk, FileType
from services.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

class ImageProcessor(DocumentProcessor):
    def __init__(self):
        super().__init__()
        self.blip_processor = None
        self.blip_captioning_model = None
        self.blip_qa_model = None
        self._initialize_image_models()
    
    def _initialize_image_models(self):
        """Initialize BLIP models for image understanding"""
        try:
            # Initialize BLIP for image captioning
            self.blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
            self.blip_captioning_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
            
            # Initialize BLIP for visual question answering
            self.blip_qa_model = BlipForQuestionAnswering.from_pretrained("Salesforce/blip-vqa-base")
            
            # Move to GPU if available
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.blip_captioning_model.to(device)
            self.blip_qa_model.to(device)
            
            logger.info(f"BLIP models initialized successfully on {device}")
            
        except Exception as e:
            logger.error(f"Error initializing BLIP models: {e}")
            self.blip_processor = None
            self.blip_captioning_model = None
            self.blip_qa_model = None
    
    async def process_image_file(self, file_path: str) -> Document:
        """Process image file and extract visual content"""
        try:
            file_path_obj = Path(file_path)
            
            # Load and preprocess image
            image = await self._load_and_preprocess_image(file_path)
            
            # Extract text content using multiple methods
            text_content = await self._extract_image_content(image, file_path)
            
            # Generate image metadata
            image_metadata = await self._extract_image_metadata(file_path, image)
            
            # Generate document metadata
            document_id = str(uuid.uuid4())
            title = self._extract_title(text_content, file_path_obj.stem)
            
            # Create document chunks
            chunks = self._create_chunks(text_content, document_id)
            
            # Generate summary
            summary = await self._generate_summary(text_content)
            
            # Extract tags/entities
            tags = self._extract_tags(text_content)
            tags.extend(["image", "visual", image_metadata.get("format", "").lower()])
            
            # Get file stats
            file_stats = file_path_obj.stat()
            
            document = Document(
                id=document_id,
                title=title,
                content=text_content,
                summary=summary,
                tags=list(set(tags)),
                file_type=self._get_image_file_type(file_path_obj.suffix),
                file_path=file_path,
                size_bytes=file_stats.st_size,
                chunk_ids=[chunk.id for chunk in chunks]
            )
            
            # Add image-specific metadata
            document.metadata = image_metadata
            
            self.chunks = chunks
            
            return document
            
        except Exception as e:
            logger.error(f"Error processing image file {file_path}: {e}")
            raise
    
    async def _load_and_preprocess_image(self, file_path: str) -> Image.Image:
        """Load and preprocess image for analysis"""
        try:
            image = Image.open(file_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Store original dimensions
            original_size = image.size
            
            # Resize if image is too large (for model compatibility)
            max_size = 1024
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"Resized image from {original_size} to {new_size}")
            
            return image
            
        except Exception as e:
            logger.error(f"Error loading image {file_path}: {e}")
            raise
    
    async def _extract_image_content(self, image: Image.Image, file_path: str) -> str:
        """Extract text content from image using multiple methods"""
        content_parts = []
        
        try:
            # 1. Generate image caption using BLIP
            caption = await self._generate_image_caption(image)
            if caption:
                content_parts.append(f"Image Description: {caption}")
            
            # 2. Extract text using OCR if available
            ocr_text = await self._extract_text_with_ocr(image)
            if ocr_text:
                content_parts.append(f"Text in Image: {ocr_text}")
            
            # 3. Generate contextual descriptions
            contextual_info = await self._generate_contextual_descriptions(image)
            content_parts.extend(contextual_info)
            
            # 4. Basic image analysis
            basic_analysis = await self._analyze_image_properties(image, file_path)
            if basic_analysis:
                content_parts.append(f"Image Analysis: {basic_analysis}")
            
            # Combine all content
            full_content = "\n\n".join(content_parts)
            
            if not full_content.strip():
                # Fallback content
                file_name = Path(file_path).name
                full_content = f"Image file: {file_name}\n\nVisual content analysis not available."
            
            return full_content
            
        except Exception as e:
            logger.error(f"Error extracting image content: {e}")
            file_name = Path(file_path).name
            return f"Image file: {file_name}\n\nError occurred during content extraction."
    
    async def _generate_image_caption(self, image: Image.Image) -> str:
        """Generate caption for image using BLIP"""
        try:
            if not self.blip_processor or not self.blip_captioning_model:
                return ""
            
            # Process image and generate caption
            loop = asyncio.get_event_loop()
            
            def generate_caption():
                inputs = self.blip_processor(image, return_tensors="pt")
                
                # Move to same device as model
                device = next(self.blip_captioning_model.parameters()).device
                inputs = {k: v.to(device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    out = self.blip_captioning_model.generate(**inputs, max_length=50)
                
                caption = self.blip_processor.decode(out[0], skip_special_tokens=True)
                return caption
            
            caption = await loop.run_in_executor(None, generate_caption)
            
            logger.info(f"Generated image caption: {caption}")
            return caption
            
        except Exception as e:
            logger.error(f"Error generating image caption: {e}")
            return ""
    
    async def _extract_text_with_ocr(self, image: Image.Image) -> str:
        """Extract text from image using OCR"""
        try:
            if not TESSERACT_AVAILABLE:
                return ""
            
            # Enhance image for better OCR results
            enhanced_image = await self._enhance_image_for_ocr(image)
            
            # Extract text using Tesseract
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                None,
                lambda: pytesseract.image_to_string(enhanced_image, config='--psm 6')
            )
            
            # Clean up extracted text
            text = text.strip()
            if len(text) > 10:  # Only return if substantial text found
                logger.info(f"Extracted {len(text)} characters of text from image")
                return text
            
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting text with OCR: {e}")
            return ""
    
    async def _enhance_image_for_ocr(self, image: Image.Image) -> Image.Image:
        """Enhance image for better OCR results"""
        try:
            # Convert to grayscale
            gray_image = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(gray_image)
            enhanced = enhancer.enhance(2.0)
            
            # Apply slight sharpening
            enhanced = enhanced.filter(ImageFilter.SHARPEN)
            
            return enhanced
            
        except Exception as e:
            logger.warning(f"Error enhancing image for OCR: {e}")
            return image
    
    async def _generate_contextual_descriptions(self, image: Image.Image) -> List[str]:
        """Generate contextual descriptions by asking specific questions"""
        descriptions = []
        
        if not self.blip_processor or not self.blip_qa_model:
            return descriptions
        
        # Define questions to ask about the image
        questions = [
            "What objects are in this image?",
            "What is the setting or location?",
            "What colors are prominent in this image?",
            "What activities or actions are happening?",
            "What is the mood or atmosphere of this image?"
        ]
        
        try:
            loop = asyncio.get_event_loop()
            
            def answer_question(question: str) -> str:
                inputs = self.blip_processor(image, question, return_tensors="pt")
                
                # Move to same device as model
                device = next(self.blip_qa_model.parameters()).device
                inputs = {k: v.to(device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    out = self.blip_qa_model.generate(**inputs, max_length=30)
                
                answer = self.blip_processor.decode(out[0], skip_special_tokens=True)
                return answer.strip()
            
            for question in questions:
                try:
                    answer = await loop.run_in_executor(None, answer_question, question)
                    if answer and len(answer) > 2:  # Valid answer
                        descriptions.append(f"{question.replace('?', '')}: {answer}")
                except Exception as e:
                    logger.warning(f"Error answering question '{question}': {e}")
                    continue
            
            logger.info(f"Generated {len(descriptions)} contextual descriptions")
            
        except Exception as e:
            logger.error(f"Error generating contextual descriptions: {e}")
        
        return descriptions
    
    async def _analyze_image_properties(self, image: Image.Image, file_path: str) -> str:
        """Analyze basic image properties"""
        try:
            properties = []
            
            # Basic properties
            width, height = image.size
            properties.append(f"Dimensions: {width}x{height}")
            
            # Color analysis
            if image.mode == 'RGB':
                # Get dominant colors (simplified)
                colors = image.getcolors(maxcolors=256*256*256)
                if colors:
                    # Sort by frequency and get most common
                    colors.sort(reverse=True)
                    dominant_color = colors[0][1]  # RGB tuple
                    properties.append(f"Dominant color: RGB{dominant_color}")
            
            # File format
            format_info = Path(file_path).suffix.upper().replace('.', '')
            properties.append(f"Format: {format_info}")
            
            return "; ".join(properties)
            
        except Exception as e:
            logger.warning(f"Error analyzing image properties: {e}")
            return ""
    
    async def _extract_image_metadata(self, file_path: str, image: Image.Image) -> Dict[str, Any]:
        """Extract comprehensive metadata from image"""
        try:
            metadata = {
                "type": "image",
                "width": image.size[0],
                "height": image.size[1],
                "mode": image.mode,
                "format": image.format or Path(file_path).suffix.upper().replace('.', ''),
                "has_transparency": image.mode in ('RGBA', 'LA'),
            }
            
            # Extract EXIF data if available
            if hasattr(image, '_getexif') and image._getexif():
                exif_data = image._getexif()
                if exif_data:
                    # Extract useful EXIF data
                    metadata["exif"] = {
                        "datetime": exif_data.get(306),  # DateTime
                        "camera_make": exif_data.get(271),  # Make
                        "camera_model": exif_data.get(272),  # Model
                        "orientation": exif_data.get(274),  # Orientation
                    }
            
            # Add processing timestamp
            metadata["processed_at"] = datetime.utcnow().isoformat()
            
            return metadata
            
        except Exception as e:
            logger.warning(f"Error extracting image metadata: {e}")
            return {
                "type": "image",
                "width": image.size[0] if image else 0,
                "height": image.size[1] if image else 0,
                "error": str(e)
            }
    
    def _get_image_file_type(self, extension: str) -> FileType:
        """Convert image file extension to FileType enum"""
        # For now, return string since FileType might not have image types
        image_mapping = {
            '.jpg': 'jpeg',
            '.jpeg': 'jpeg',
            '.png': 'png',
            '.gif': 'gif',
            '.bmp': 'bmp',
            '.webp': 'webp',
            '.tiff': 'tiff',
            '.svg': 'svg'
        }
        
        return image_mapping.get(extension.lower(), 'image')
    
    async def search_images_by_description(self, description: str, image_paths: List[str]) -> List[Tuple[str, float]]:
        """Search images by natural language description"""
        try:
            if not self.blip_processor or not self.blip_qa_model:
                return []
            
            results = []
            
            for image_path in image_paths:
                try:
                    image = await self._load_and_preprocess_image(image_path)
                    
                    # Ask if the image matches the description
                    loop = asyncio.get_event_loop()
                    
                    def check_match():
                        question = f"Does this image show {description}?"
                        inputs = self.blip_processor(image, question, return_tensors="pt")
                        
                        device = next(self.blip_qa_model.parameters()).device
                        inputs = {k: v.to(device) for k, v in inputs.items()}
                        
                        with torch.no_grad():
                            out = self.blip_qa_model.generate(**inputs, max_length=10)
                        
                        answer = self.blip_processor.decode(out[0], skip_special_tokens=True)
                        return answer.lower()
                    
                    answer = await loop.run_in_executor(None, check_match)
                    
                    # Simple scoring based on answer
                    score = 0.8 if "yes" in answer else 0.2
                    results.append((image_path, score))
                    
                except Exception as e:
                    logger.warning(f"Error processing image {image_path} for search: {e}")
                    continue
            
            # Sort by score
            results.sort(key=lambda x: x[1], reverse=True)
            return results
            
        except Exception as e:
            logger.error(f"Error searching images: {e}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """Check image processor health"""
        return {
            "status": "healthy" if self.blip_processor else "degraded",
            "blip_available": bool(self.blip_processor and self.blip_captioning_model),
            "blip_qa_available": bool(self.blip_qa_model),
            "ocr_available": TESSERACT_AVAILABLE,
            "supported_formats": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"],
            "device": "cuda" if torch.cuda.is_available() else "cpu"
        }